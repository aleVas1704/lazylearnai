---
name: backend-feature
description: Crear funciones FastAPI pequeñas con pruebas sin cambiar la arquitectura.
---

# Feature backend

1. Leer `AGENTS.md` y `docs/ARCHITECTURE.md`.
2. Escribir el objetivo y los criterios verificables antes de modificar código.
3. Añadir rutas en `backend/modules/<feature>/routes.py`.
4. Usar `service.py` para reglas de negocio; crear `repository.py` solo si hay SQL.
5. No tocar plantillas ni archivos compartidos sin pedir coordinación.
6. Añadir tests para comportamiento principal y errores relevantes.
7. Ejecutar Ruff y Pytest; indicar resultados y archivos modificados.
