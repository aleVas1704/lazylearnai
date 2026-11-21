# Arquitectura acordada

**Monolito modular por funcionalidades, en un monorepo.**

- `frontend/`: Jinja2, HTML, CSS, HTMX opcional.
- `backend/`: única aplicación FastAPI, módulos por funcionalidad.
- `backend/core/`: configuración compartida y conexión al servidor Neon.
- `migrations/`: cambios controlados del esquema, solo cuando existan tablas.
- `.agents/skills/`: guía para asistentes de IA.

## Flujo de una petición

Navegador → FastAPI (`routes.py`) → servicio (`service.py`) → repositorio (si hay BD)
→ Neon → template Jinja2 → HTML de respuesta. HTMX puede sustituir fragmentos HTML.

## Límites

No crear `package.json`, una aplicación React separada, una API REST innecesaria ni más
servicios. Crecer por módulos SOLO después de conocer las necesidades del ensayo.

## Vercel

`[tool.vercel] entrypoint = "backend.main:app"` en `pyproject.toml`.
Vercel debe importar el **directorio raíz** del repositorio, no solo `frontend/`.
