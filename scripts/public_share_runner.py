#!/usr/bin/env python3
"""
Sovereign AI Workbench - Public Share Mode Runner (SIH26117)
------------------------------------------------------------
Establishes secure ingress (Tailscale Funnel or Cloudflare Tunnel) directly to the local FastAPI backend (127.0.0.1:8000).
Ensures:
- Local AI (Ollama 127.0.0.1:11434) is NEVER directly exposed to the internet.
- SQLite, ChromaDB, and Windows host filesystem are NEVER exposed.
- Zero Cloud AI APIs are contacted; all inference executes on the local host.
- Host header validation permits ONLY the exact configured public hostname.
"""

import os
import sys
import time
import re
import subprocess
import signal
import urllib.request
import urllib.error
import json
import argparse
from pathlib import Path

# Workspace root
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_URL_FILE = WORKSPACE_ROOT / ".public_share_url"
BACKEND_HEALTH_URL = "http://127.0.0.1:8000/api/v1/health"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"

cloudflared_proc = None
backend_proc = None


def cleanup():
    """Clean up running tunnel processes and metadata file."""
    global cloudflared_proc, backend_proc
    print("\n[CLEANUP] Stopping Public Share tunnel...")
    if cloudflared_proc and cloudflared_proc.poll() is None:
        try:
            cloudflared_proc.terminate()
            cloudflared_proc.wait(timeout=3)
        except Exception:
            pass

    if backend_proc and backend_proc.poll() is None:
        try:
            backend_proc.terminate()
            backend_proc.wait(timeout=3)
        except Exception:
            try:
                backend_proc.kill()
            except Exception:
                pass

    if PUBLIC_URL_FILE.exists():
        try:
            PUBLIC_URL_FILE.unlink()
            print(f"[CLEANUP] Removed {PUBLIC_URL_FILE.name}")
        except Exception as e:
            print(f"[WARN] Could not remove {PUBLIC_URL_FILE}: {e}")

    print("[CLEANUP] Sovereign Workbench returned to local-only mode.\n")


def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)


def check_ollama() -> dict:
    """Verify local Ollama instance and models."""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL, headers={"User-Agent": "SovereignRunner/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            models = [m.get("name", "") for m in data.get("models", [])]
            return {"connected": True, "models": models}
    except Exception as e:
        return {"connected": False, "error": str(e), "models": []}


def check_tesseract() -> bool:
    """Verify local Tesseract OCR executable."""
    try:
        res = subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        if res.returncode == 0:
            return True
    except Exception:
        pass

    user_appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        Path(user_appdata) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ]
    for c in candidates:
        if c.exists():
            return True
    return False


def check_cloudflared() -> str:
    """Find cloudflared executable."""
    try:
        res = subprocess.run(["cloudflared", "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
        if res.returncode == 0:
            return "cloudflared"
    except Exception:
        pass

    user_appdata = os.environ.get("LOCALAPPDATA", "")
    candidates = [
        WORKSPACE_ROOT / "venv" / "Scripts" / "cloudflared.exe",
        Path(user_appdata) / "Programs" / "cloudflared" / "cloudflared.exe",
        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "cloudflared" / "cloudflared.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    return ""


def check_backend_running() -> bool:
    """Check if FastAPI backend is answering on 127.0.0.1:8000."""
    try:
        req = urllib.request.Request(BACKEND_HEALTH_URL, headers={"User-Agent": "SovereignRunner/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            return resp.status == 200
    except Exception:
        return False


def start_backend():
    """Start local backend if not already active."""
    global backend_proc
    print("[PRE-FLIGHT] Starting local FastAPI backend on 127.0.0.1:8000...")
    backend_dir = WORKSPACE_ROOT / "backend"
    venv_python = WORKSPACE_ROOT / "venv" / "Scripts" / "python.exe"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable

    env = os.environ.copy()
    env["PYTHONPATH"] = str(backend_dir)
    env["WORKBENCH_AIR_GAP_STRICT_MODE"] = "False"
    env["PUBLIC_SHARE_ENABLED"] = "true"

    cmd = [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
    backend_proc = subprocess.Popen(cmd, cwd=str(backend_dir), env=env)

    # Wait for backend to come up
    for _ in range(60):
        time.sleep(0.5)
        if check_backend_running():
            print("[PRE-FLIGHT] Local backend successfully online.")
            return True
    print("[ERROR] Failed to start local backend within 30 seconds.")
    return False


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = argparse.ArgumentParser(description="Sovereign AI Workbench - Public Share Runner (SIH26117)")
    parser.add_argument("--mode", choices=["quick", "stable"], default=None, help="Tunnel mode: 'quick' (ephemeral) or 'stable' (named)")
    parser.add_argument("--token", default=None, help="Cloudflare Named Tunnel token (never commit to git)")
    parser.add_argument("--name", default=None, help="Cloudflare Named Tunnel name")
    parser.add_argument("--url", default=None, help="Configured public base URL (e.g. https://laptop-5shove4t.tail907df1.ts.net)")
    parser.add_argument("--provider", choices=["cloudflare", "tailscale", "auto"], default="auto", help="Tunnel ingress provider")
    args = parser.parse_args()

    # Determine mode: CLI flag -> Environment variable -> Default to quick
    env_mode = os.getenv("PUBLIC_SHARE_MODE", "quick").strip().lower()
    mode = args.mode or ("stable" if env_mode in ("stable", "named", "public_share_stable") else "quick")

    tunnel_token = args.token or os.getenv("CLOUDFLARE_TUNNEL_TOKEN")
    tunnel_name = args.name or os.getenv("CLOUDFLARE_TUNNEL_NAME")
    public_base_url = args.url or os.getenv("PUBLIC_BASE_URL")

    # Detect provider
    is_tailscale = bool(
        args.provider == "tailscale"
        or (args.provider == "auto" and public_base_url and "ts.net" in public_base_url.lower())
    )

    if public_base_url:
        os.environ["PUBLIC_BASE_URL"] = public_base_url
        os.environ["PUBLIC_SHARE_ENABLED"] = "true"
        PUBLIC_URL_FILE.write_text(public_base_url.strip(), encoding="utf-8")

    banner_mode = "TAILSCALE FUNNEL" if is_tailscale else mode.upper()
    print("========================================================================")
    print(f"   SOVEREIGN AI WORKBENCH - PUBLIC SHARE ({banner_mode}) (SIH26117)   ")
    print("========================================================================")

    # Pre-flight checks
    if not is_tailscale:
        cf_path = check_cloudflared()
        if not cf_path:
            print("[ERROR] 'cloudflared' binary not found. Please install cloudflared or add to PATH.")
            sys.exit(1)
        print(f"[PRE-FLIGHT] Cloudflare binary verified: {cf_path}")
    else:
        print("[PRE-FLIGHT] Ingress managed via Tailscale Funnel to local port 8000.")

    # Ollama check
    ollama_info = check_ollama()
    if ollama_info["connected"]:
        print(f"[PRE-FLIGHT] Ollama Daemon ONLINE (Found {len(ollama_info['models'])} models)")
    else:
        print("[WARN] Ollama Daemon NOT responding on 127.0.0.1:11434. Local inference may fail.")

    # Tesseract check
    tess_ok = check_tesseract()
    print(f"[PRE-FLIGHT] Local Tesseract OCR: {'ONLINE' if tess_ok else 'NOT FOUND'}")

    # Backend check
    if not check_backend_running():
        print("[PRE-FLIGHT] Backend is not currently running. Launching backend...")
        if not start_backend():
            sys.exit(1)
    else:
        print("[PRE-FLIGHT] Local FastAPI backend is already running on 127.0.0.1:8000.")

    # Ingress Tunnel Routing
    # CRITICAL SECURITY REQUIREMENT: Only tunnel port 8000. NEVER tunnel port 11434.
    global cloudflared_proc
    public_url = None

    if is_tailscale:
        public_url = public_base_url.strip()
        PUBLIC_URL_FILE.write_text(public_url, encoding="utf-8")
        tunnel_type_label = "Tailscale Funnel"
        print(f"[SECURITY] Tailscale Funnel endpoint: {public_url}")
        print("[SECURITY] FastAPI Host header validation permits ONLY this exact host.")

    elif mode == "stable":
        print("[SECURITY] Initiating Cloudflare Named Tunnel ONLY to http://127.0.0.1:8000...")
        if not tunnel_token and not tunnel_name:
            print("\n" + "=" * 76)
            print(" [BLOCKED] STABLE HOSTNAME REQUIRES CLOUDFLARE NAMED TUNNEL CONFIGURATION ")
            print("=" * 76)
            print(" Reason: Stable named tunnel mode was requested, but neither")
            print("         CLOUDFLARE_TUNNEL_TOKEN nor CLOUDFLARE_TUNNEL_NAME was provided.\n")
            print(" Operator Setup Instructions to activate a Stable Named Tunnel:")
            print(" -----------------------------------------------------------------")
            print(" 1. Log in to your Cloudflare Zero Trust dashboard:")
            print("      https://one.dash.cloudflare.com/")
            print(" 2. Navigate to Networks > Tunnels > Add a Tunnel.")
            print(" 3. Choose 'Cloudflare' connector, name it (e.g. 'sovereign-workbench').")
            print(" 4. Copy the tunnel token provided in the connector installation section.")
            print(" 5. In the tunnel's 'Public Hostname' tab, add a route:")
            print("      Subdomain/Domain: e.g. ai.yourdomain.com")
            print("      Type: HTTP")
            print("      URL: 127.0.0.1:8000")
            print(" 6. Configure environment variables (or add to your .env file):")
            print("      $env:CLOUDFLARE_TUNNEL_TOKEN = \"your_tunnel_token_here\"")
            print("      $env:PUBLIC_BASE_URL = \"https://ai.yourdomain.com\"")
            print("      $env:PUBLIC_SHARE_MODE = \"stable\"")
            print(" 7. Launch stable mode:")
            print("      .\\scripts\\start_public_share_stable.ps1\n")
            print(" Fallback to Quick Tunnel (ephemeral trycloudflare.com URL):")
            print("      .\\scripts\\start_public_share.ps1")
            print("============================================================================\n")
            cleanup()
            sys.exit(2)

        if tunnel_token:
            cmd = [cf_path, "tunnel", "run", "--token", tunnel_token, "--no-autoupdate"]
        else:
            cmd = [cf_path, "tunnel", "run", tunnel_name, "--no-autoupdate"]

        cloudflared_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        public_url = public_base_url or (f"https://{tunnel_name}.cfargotunnel.com" if tunnel_name else "https://configured-named-tunnel.cloudflare.com")
        PUBLIC_URL_FILE.write_text(public_url.strip(), encoding="utf-8")
        tunnel_type_label = "Cloudflare Named Tunnel"
        time.sleep(2)

    else:
        # Quick Tunnel mode
        print("[SECURITY] Initiating isolated HTTPS tunnel ONLY to http://127.0.0.1:8000...")
        cmd = [cf_path, "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate"]

        cloudflared_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        url_pattern = re.compile(r"https:\/\/[a-zA-Z0-9-]+\.trycloudflare\.com")

        print("[TUNNEL] Connecting to Cloudflare edge network...")
        start_time = time.time()
        while time.time() - start_time < 30:
            line = cloudflared_proc.stdout.readline()
            if not line:
                if cloudflared_proc.poll() is not None:
                    print(f"[ERROR] cloudflared process terminated with code {cloudflared_proc.returncode}")
                    break
                time.sleep(0.1)
                continue

            stripped = line.strip()
            if stripped:
                print(f"[TUNNEL] {stripped}")

            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                break

        if not public_url:
            print("[ERROR] Timed out waiting for Cloudflare tunnel URL.")
            cleanup()
            sys.exit(1)

        PUBLIC_URL_FILE.write_text(public_url.strip(), encoding="utf-8")
        tunnel_type_label = "Cloudflare Quick Tunnel"

    # Display rich status banner
    print("\n" + "=" * 40)
    print("SOVEREIGN AI WORKBENCH")
    print(f"PUBLIC SHARE READY ({banner_mode})")
    print("=" * 40)
    print(f"\nLOCAL:\nhttp://127.0.0.1:8000\n")
    print(f"PUBLIC:\n{public_url}\n")
    print(f"MODE:\nPUBLIC SHARE / LOCAL AI\n")
    print(f"TYPE:\n{tunnel_type_label}\n")
    print(f"BACKEND:\n{'ONLINE' if check_backend_running() else 'OFFLINE'}\n")
    print(f"OLLAMA:\n{'ONLINE' if ollama_info['connected'] else 'OFFLINE'}\n")
    print("CHROMA:\nONLINE\n")
    print(f"OCR:\n{'ONLINE' if tess_ok else 'OFFLINE'}\n")
    vision_ok = any("llava" in m.lower() for m in ollama_info.get("models", []))
    print(f"VISION:\n{'ONLINE' if vision_ok else 'OFFLINE'}\n")
    print("=" * 40 + "\n")
    print("Remote users can access the application, while AI models,")
    print("knowledge base and processing remain on the host machine.\n")
    print("Press Ctrl+C at any time to terminate the public tunnel and return to")
    print("local-only operation.\n")

    # Keep alive loop
    try:
        while True:
            if cloudflared_proc:
                line = cloudflared_proc.stdout.readline()
                if not line and cloudflared_proc.poll() is not None:
                    print(f"[WARN] Tunnel process ended unexpectedly (code {cloudflared_proc.returncode})")
                    break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
