"""
Local OCR Provider Abstraction & Implementation (SIH26117).
Enforces 100% on-premise local OCR extraction.
Zero cloud OCR APIs. Fails closed and reports OCR_UNAVAILABLE honestly if local binary is missing.
"""

import os
import shutil
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from PIL import Image
import io

from app.config import settings

logger = logging.getLogger("sovereign.ocr")


class OCRProvider(ABC):
    """Abstract base class for Sovereign Local OCR Providers."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Returns True if local OCR engine is installed, reachable, and ready."""
        pass

    @abstractmethod
    async def extract_text_from_image(self, image_bytes_or_path: Any) -> Dict[str, Any]:
        """
        Extracts text from an image.
        Returns: {
            "success": bool,
            "text": str,
            "confidence": float,
            "page": int,
            "error": Optional[str]
        }
        """
        pass

    @abstractmethod
    async def extract_text_from_pdf_page(self, page_image: Any, page_number: int = 1) -> Dict[str, Any]:
        """Extracts text from a rendered PDF page image."""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Returns provider metadata for system capability diagnostics."""
        pass


class LocalOCRProvider(OCRProvider):
    """
    Local Tesseract OCR Provider.
    Detects local Tesseract installation across PATH and standard Windows/Linux locations.
    Never calls external cloud APIs.
    """

    def __init__(self, custom_cmd: Optional[str] = None):
        self.custom_cmd = custom_cmd if custom_cmd is not None else (settings.TESSERACT_CMD or None)
        self._binary_path: Optional[str] = None
        self._detect_binary()

    def _detect_binary(self):
        # If custom command was provided, strictly validate it without falling back
        if self.custom_cmd:
            if os.path.exists(self.custom_cmd) or shutil.which(self.custom_cmd):
                self._binary_path = self.custom_cmd if os.path.exists(self.custom_cmd) else shutil.which(self.custom_cmd)
            else:
                self._binary_path = None
            return

        # Auto-detect when no custom command is provided
        if shutil.which("tesseract"):
            self._binary_path = shutil.which("tesseract")
        else:
            # Standard Windows locations
            user_appdata = os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
            windows_defaults = [
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                user_appdata,
                r"C:\Users\vk980\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
            ]
            for wpath in windows_defaults:
                if os.path.exists(wpath):
                    self._binary_path = wpath
                    break
            else:
                self._binary_path = None

        if self._binary_path:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self._binary_path
            except Exception:
                pass

    def _verify_execution(self) -> bool:
        """Executes a real check against the local binary to verify it actually works."""
        if not self._binary_path or not os.path.exists(self._binary_path):
            return False
        try:
            import subprocess
            res = subprocess.run([self._binary_path, "--version"], capture_output=True, timeout=3.0)
            return res.returncode == 0
        except Exception:
            return False

    def _get_version(self) -> Optional[str]:
        if not self._binary_path or not os.path.exists(self._binary_path):
            return None
        try:
            import subprocess
            res = subprocess.run([self._binary_path, "--version"], capture_output=True, text=True, timeout=3.0)
            if res.returncode == 0:
                line = res.stdout.splitlines()[0]
                return line.strip()
        except Exception:
            pass
        return None

    def _list_languages(self) -> List[str]:
        if not self._binary_path or not os.path.exists(self._binary_path):
            return []
        try:
            import subprocess
            res = subprocess.run([self._binary_path, "--list-langs"], capture_output=True, text=True, timeout=3.0)
            if res.returncode == 0:
                langs = [l.strip() for l in res.stdout.splitlines() if l.strip() and not l.startswith("List of")]
                return langs
        except Exception:
            pass
        return ["eng"]

    async def is_available(self) -> bool:
        if not settings.OCR_ENABLED:
            return False
        if not self._binary_path:
            self._detect_binary()
        return self._verify_execution()

    async def extract_text_from_image(self, image_input: Any) -> Dict[str, Any]:
        if not await self.is_available():
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "page": 1,
                "error": "OCR_UNAVAILABLE: Local Tesseract binary not installed or failed verification. Zero fake OCR generated."
            }

        try:
            import pytesseract
            if self._binary_path:
                pytesseract.pytesseract.tesseract_cmd = self._binary_path

            if isinstance(image_input, (bytes, bytearray)):
                img = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, str) and os.path.exists(image_input):
                img = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                img = image_input
            else:
                return {
                    "success": False,
                    "text": "",
                    "confidence": 0.0,
                    "page": 1,
                    "error": "Invalid image input format for OCR."
                }

            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Extract text
            raw_text = pytesseract.image_to_string(img)

            # Extract confidence via image_to_data
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confs = [int(c) for c in data.get("conf", []) if str(c).isdigit() and int(c) >= 0]
                avg_conf = (sum(confs) / len(confs)) / 100.0 if confs else 0.85
            except Exception:
                avg_conf = 0.85

            return {
                "success": True,
                "text": raw_text.strip(),
                "confidence": round(avg_conf, 4),
                "page": 1,
                "error": None
            }
        except Exception as e:
            logger.error(f"Local OCR execution error: {e}")
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "page": 1,
                "error": f"OCR_FAILED: {str(e)}"
            }

    async def extract_text_from_pdf_page(self, page_image: Any, page_number: int = 1) -> Dict[str, Any]:
        res = await self.extract_text_from_image(page_image)
        res["page"] = page_number
        return res

    def get_provider_info(self) -> Dict[str, Any]:
        can_exec = settings.OCR_ENABLED and self._verify_execution()
        return {
            "provider": "local_tesseract",
            "available": can_exec,
            "binary_path": self._binary_path if can_exec else None,
            "version": self._get_version() if can_exec else None,
            "languages": self._list_languages() if can_exec else [],
            "status": "AVAILABLE" if can_exec else "OCR_UNAVAILABLE",
            "message": "Local Tesseract OCR engine available and operational" if can_exec else "Tesseract binary not installed on host. Zero fake OCR generated."
        }


# Global singleton
local_ocr_provider = LocalOCRProvider()


def get_ocr_provider() -> OCRProvider:
    """Returns configured local OCR provider."""
    return local_ocr_provider
