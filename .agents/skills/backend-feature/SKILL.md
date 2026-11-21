---
name: backend-feature
description: Crear funciones FastAPI pequeñas respetando la arquitectura y revisando su funcionamiento manualmente.
---

# Feature backend

1. Leer `AGENTS.md` y `docs/ARCHITECTURE.md`.
2. Escribir el objetivo y los criterios verificables antes de modificar código.
3. Añadir rutas en `backend/modules/<feature>/routes.py`.
4. Usar `service.py` para reglas de negocio; crear `repository.py` solo si hay SQL.
5. No tocar plantillas ni archivos compartidos sin pedir coordinación.
6. Revisar manualmente el caso principal, validaciones y errores previstos.
7. Utilizar Ruff localmente si corresponde; describir archivos modificados y cómo se verificó el funcionamiento.
