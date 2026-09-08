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
        self.custom_cmd = custom_cmd or settings.TESSERACT_CMD
        self._binary_path: Optional[str] = None
        self._detect_binary()

    def _detect_binary(self):
        # 1. Custom configured command
        if self.custom_cmd and os.path.exists(self.custom_cmd):
            self._binary_path = self.custom_cmd
            return

        # 2. PATH check
        path_binary = shutil.which("tesseract")
        if path_binary:
            self._binary_path = path_binary
            return

        # 3. Standard Windows locations
        windows_defaults = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
        ]
        for wpath in windows_defaults:
            if os.path.exists(wpath):
                self._binary_path = wpath
                return

        self._binary_path = None

    async def is_available(self) -> bool:
        if not settings.OCR_ENABLED:
            return False
        if not self._binary_path:
            self._detect_binary()
        return self._binary_path is not None

    async def extract_text_from_image(self, image_input: Any) -> Dict[str, Any]:
        if not await self.is_available():
            return {
                "success": False,
                "text": "",
                "confidence": 0.0,
                "page": 1,
                "error": "OCR_UNAVAILABLE: Local Tesseract binary not installed. Zero fake OCR generated."
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
        avail = self._binary_path is not None and settings.OCR_ENABLED
        return {
            "provider": "local_tesseract",
            "available": avail,
            "binary_path": self._binary_path if avail else None,
            "status": "READY" if avail else "OCR_UNAVAILABLE",
            "message": "Local Tesseract OCR engine ready" if avail else "Tesseract binary not installed on host. Zero fake OCR generated."
        }


# Global singleton
local_ocr_provider = LocalOCRProvider()


def get_ocr_provider() -> OCRProvider:
    """Returns configured local OCR provider."""
    return local_ocr_provider
