"""
Omni Dimension / Ollama calling tools.

Provides a CallProviderTool that uses Ollama to simulate/drive a call
or to format payloads to send to Omni Dimension external API.
"""
from crewai.tools import BaseTool
from typing import Optional, Dict, Any
from ..config import settings
from ..logger import logger
import requests
import json


class CallProviderTool(BaseTool):
    name: str = "call_provider_omni"
    description: str = (
        "Initiate a call/verification via Omni Dimension or simulate using Ollama LLM. "
        "Returns a call session summary as JSON."
    )

    def _run(self, to: str, provider_name: str, payload: Optional[Dict[str, Any]] = None) -> str:
        # If Omni Dimension endpoint configured, send payload
        if payload is None:
            payload = {}

        payload.update({"to": to, "provider_name": provider_name})

        # If user has set an OMNI_ENDPOINT env var, forward the request
        omni_endpoint = getattr(settings, 'OMNI_ENDPOINT', None)
        if omni_endpoint:
            try:
                resp = requests.post(omni_endpoint, json=payload, timeout=10)
                resp.raise_for_status()
                return json.dumps(resp.json())
            except Exception as e:
                logger.warning(f"Omni call failed: {e}")

        # Fallback: Use local Ollama LLM to simulate a call summary
        try:
            llm_url = settings.OLLAMA_BASE_URL.rstrip('/') + '/api/generate'
            prompt = (
                f"You are an automated call system. Simulate a concise call summary for a call to {provider_name} ({to}).\n"
                "Return a JSON object with call_id, status, duration, call_summary, extracted_information."
            )
            data = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 200}
            }
            r = requests.post(llm_url, json=data, timeout=30)
            if r.status_code == 200:
                resp = r.json()
                raw = resp.get('response', '')
                # Try to extract JSON from response
                import re
                m = re.search(r'\{.*\}', raw, re.S)
                if m:
                    return m.group(0)
                return json.dumps({"call_id": "sim-" + to[-6:], "status": "completed", "call_summary": raw[:500]})
        except Exception as e:
            logger.warning(f"Ollama call simulation failed: {e}")

        # Final fallback
        return json.dumps({"call_id": "unknown", "status": "failed"})
