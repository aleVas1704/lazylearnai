from fastapi import APIRouter, HTTPException

from backend.core.config import database_url
from backend.core.database import ping_database

router = APIRouter(tags=["Salud"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "abstracthon-base"}


@router.get("/health/db")
def database_health() -> dict[str, str]:
    url = database_url()
    if not url:
        raise HTTPException(status_code=503, detail="Base de datos sin configurar")
    try:
        ping_database(url)
    except Exception as exc:
        # Evitar devolver errores del driver o detalles de la conexion al navegador.
        raise HTTPException(status_code=503, detail="Base de datos no disponible") from exc
    return {"status": "ok", "database": "connected"}
