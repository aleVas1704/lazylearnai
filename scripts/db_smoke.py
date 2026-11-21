"""Prueba manual de conexion a Neon SIN escribir ni cambiar el esquema."""

from backend.core.config import database_url
from backend.core.database import ping_database


def main() -> None:
    url = database_url()
    if not url:
        raise SystemExit("DATABASE_URL no configurada (ver docs/DEPLOY.md)")
    ping_database(url)
    print("Conexión a Neon correcta (SELECT 1)")


if __name__ == "__main__":
    main()
