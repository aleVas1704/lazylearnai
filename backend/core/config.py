import os


def database_url() -> str | None:
    """Cadena secreta de Neon. Se inyecta como variable en el servidor."""
    return os.environ.get("DATABASE_URL") or None
