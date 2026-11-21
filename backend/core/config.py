import os


def database_url() -> str | None:
    """Cadena secreta de Neon. Se inyecta como variable en el servidor."""
    return os.environ.get("DATABASE_URL") or None


def student_id_hmac_key() -> bytes | None:
    """Exigir al menos 32 bytes; generar aleatoriamente, nunca derivar del carnet."""
    key = os.environ.get("STUDENT_ID_HMAC_KEY", "").encode("utf-8")
    return key if len(key) >= 32 else None


def student_local_http_enabled() -> bool:
    """Excepción explícita para loopback, desactivada siempre en Vercel."""
    return os.environ.get("STUDENT_ALLOW_LOCAL_HTTP") == "1" and not os.environ.get("VERCEL")


def gemini_api_key() -> str | None:
    """Clave de Gemini disponible solo en el servidor."""
    return os.environ.get("GEMINI_API_KEY") or None


def gemini_model() -> str:
    """Modelo configurable sin exponerlo al navegador."""
    return os.environ.get("GEMINI_MODEL") or "gemini-3.8-flash"
