"""Adaptador mínimo al SDK oficial de Gemini, ejecutado solo en el servidor."""

from google import genai
from google.genai import types

from backend.core.config import gemini_api_key, gemini_model


class GeminiNotConfigured(Exception):
    pass


class GeminiUnavailable(Exception):
    pass


def generate(
    contents: list[types.Content],
    system_instruction: str,
    *,
    timeout_ms: int = 30000,
    max_tokens: int = 1200,
) -> str:
    key = gemini_api_key()
    if not key:
        raise GeminiNotConfigured()
    try:
        with genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=timeout_ms, retry_options=types.HttpRetryOptions(attempts=1)
            ),
        ) as client:
            response = client.models.generate_content(
                model=gemini_model(),
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.25,
                    max_output_tokens=max_tokens,
                ),
            )
        text = (response.text or "").strip()
    except Exception as error:
        raise GeminiUnavailable() from error
    if not text:
        raise GeminiUnavailable()
    return text[:4000].replace("**", "")
