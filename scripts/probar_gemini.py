"""Probar modelo activo sin mostrar credenciales ni acceder a Neon."""

import os

from google.genai import types

from backend.modules.student_task_chat import gemini_client

if not os.getenv("GEMINI_API_KEY"):
    raise SystemExit("Falta GEMINI_API_KEY en .env")
print("Modelo:", os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))
try:
    answer = gemini_client.generate(
        [types.Content(role="user", parts=[types.Part.from_text(text="Responde solo: OK")])],
        "Responde con el texto OK y nada más.",
    )
    print("Gemini respondió:", answer[:100])
except (gemini_client.GeminiNotConfigured, gemini_client.GeminiUnavailable):
    print("Gemini no respondió. Revisa modelo, cuota, permisos, conectividad y API key.")
    raise SystemExit(1) from None
