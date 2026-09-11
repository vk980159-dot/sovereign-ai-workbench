"""
Model Provider Abstraction Layer (SIH26117).
Provides decoupled, extensible interface for local LLM inference (Ollama llama3.1)
with transparent status reporting, zero cloud calls, and deterministic fallback.
"""

import json
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from app.config import settings


class ModelProvider(ABC):
    """Abstract interface for local sovereign models."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1
    ) -> str:
        """Executes text generation."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Returns True if local inference engine is reachable."""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Returns metadata about the active model."""
        pass


class OllamaModelProvider(ModelProvider):
    """
    Local Ollama Inference Provider.
    Strictly on-premise, zero cloud/API telemetry.
    """

    def __init__(self, base_url: Optional[str] = None, default_model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.default_model = default_model or settings.DEFAULT_MODEL
        self.timeout = settings.INFERENCE_TIMEOUT_SECONDS

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.1
    ) -> str:
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.default_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 384
            }
        }
        if system:
            payload["system"] = system
        if json_mode:
            payload["format"] = "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("response", "").strip()
                return f"[Local Inference Error: HTTP {response.status_code}]"
        except httpx.ConnectError:
            return (
                f"[INFERENCE STATUS: Ollama engine at {self.base_url} is unreachable. "
                f"Sovereign integrity preserved: zero fake AI responses generated. "
                f"Start local daemon via 'ollama serve' with model '{self.default_model}'.]"
            )
        except httpx.TimeoutException:
            return (
                f"[INFERENCE STATUS: Request timed out after {self.timeout}s. "
                f"Host requires additional compute resources for '{self.default_model}'.]"
            )
        except Exception as e:
            return f"[Inference Exception: {str(e)}]"

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "Ollama (On-Premise)",
            "model": self.default_model,
            "endpoint": self.base_url,
            "air_gapped": True
        }


# Global singleton provider instance
default_model_provider = OllamaModelProvider()


def get_model_provider() -> ModelProvider:
    return default_model_provider
