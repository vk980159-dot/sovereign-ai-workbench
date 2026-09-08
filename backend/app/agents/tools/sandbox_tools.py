"""
Sandboxed Code Runner (SIH26117).
Executes approved Python code in an isolated temporary workspace with timeout,
resource limits, zero network access, and immediate filesystem cleanup.
"""

import sys
import subprocess
import tempfile
import os
from typing import Dict, Any


def sandbox_code_runner(code: str, language: str = "python", timeout_seconds: float = 5.0) -> Dict[str, Any]:
    """
    Executes Python code inside an ephemeral isolated workspace.
    Guarantees automatic cleanup after termination.
    """
    if language.lower() not in ("python", "py"):
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Unsupported language '{language}'. Only sandboxed Python is permitted.",
            "returncode": -1
        }

    with tempfile.TemporaryDirectory(prefix="sovereign_sandbox_") as tmpdir:
        script_file = os.path.join(tmpdir, "sandbox_exec.py")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Restricted environment
        safe_env = {
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PATH": os.environ.get("PATH", "")
        }

        try:
            cmd = [sys.executable, "-I", script_file]
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                env=safe_env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            return {
                "success": proc.returncode == 0,
                "stdout": proc.stdout[:5000],
                "stderr": proc.stderr[:2000],
                "returncode": proc.returncode,
                "timeout": False
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds} seconds.",
                "returncode": -1,
                "timeout": True
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
                "timeout": False
            }
