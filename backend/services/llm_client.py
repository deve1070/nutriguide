from typing import Optional

from groq import Groq

from backend.config import get_settings

settings = get_settings()


class LLMClient:
    """
    Thin wrapper around the Groq API.
    All prompting logic lives in rag_engine.py — this class only handles
    the HTTP call and error handling.
    """

    def __init__(self):
        self._client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model_id

    def complete(
        self,
        prompt: str,
        system: str = "You are a helpful clinical nutrition assistant.",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Optional[str]:
        """
        Send a prompt and return the response text.
        Returns None on failure so callers can use fallback logic.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            text = response.choices[0].message.content
            return text.strip() if text else None

        except Exception as e:
            print(f"❌ Groq LLM error: {e}")
            return None

    def is_available(self) -> bool:
        """Quick connectivity check"""
        if not settings.groq_api_key:
            return False
        try:
            result = self.complete("Say OK", max_tokens=5)
            return result is not None
        except Exception:
            return False


# ── Singleton ─────────────────────────────────────────
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """FastAPI dependency — returns shared LLMClient instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
