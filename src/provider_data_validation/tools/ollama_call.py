from ..config import settings
import requests
from typing import Optional


class OllamaCallTool:
    """Simple wrapper to call a local Ollama HTTP endpoint or simulate output.

    This is intentionally tolerant of different Ollama deployments. If
    `settings.ollama_base_url` is not set, the tool returns a simulated
    response so the app can run without a local Ollama instance.
    """

    def __init__(self):
        self.base = (settings.OLLAMA_BASE_URL or "").rstrip("/")
        self.model = settings.OLLAMA_MODEL or "llama2"

    def generate(self, prompt: str, timeout: int = 15) -> str:
        if not self.base:
            return f"(simulated) Ollama not configured. Prompt: {prompt[:200]}"

        # Best-effort POST to a likely Ollama-compatible endpoint.
        try:
            url = f"{self.base}/v1/generate"
            payload = {"model": self.model, "prompt": prompt}
            resp = requests.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()

            # Try common response shapes gracefully.
            if isinstance(data, dict):
                if "text" in data:
                    return data["text"]
                if "output" in data:
                    return data["output"]
                choices = data.get("choices")
                if choices and isinstance(choices, list):
                    first = choices[0]
                    if isinstance(first, dict) and "text" in first:
                        return first["text"]

            return str(data)
        except Exception as exc:  # pragma: no cover - network or env dependent
            return f"(ollama-error) {exc}"


__all__ = ["OllamaCallTool"]
