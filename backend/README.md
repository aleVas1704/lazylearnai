# Backend

Una sola aplicación **FastAPI**. Se inicia desde la raíz con:

```bash
uv run uvicorn backend.main:app --reload
```

- `main.py`: crea FastAPI, registra módulos y sirve estáticos y templates.
- `core/config.py`: variables de entorno del servidor.
- `core/database.py`: prueba de conexión PostgreSQL/Neon.
- `modules/health/`: rutas `/health` y `/health/db`.
- `modules/demo/`: página y ejemplo de interacción Jinja2/HTMX.

Para una función nueva crear `modules/<funcionalidad>/routes.py`. Agregar `service.py`,
`models.py` o `repository.py` únicamente cuando la funcionalidad lo requiera.
Registrar el router en `main.py` coordinando con los demás integrantes.

No guardar secretos ni ejecutar migraciones desde el arranque. Ver `AGENTS.md`.
