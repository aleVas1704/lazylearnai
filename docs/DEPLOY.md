# Despliegue: GitHub + Vercel + Neon

## 1. Publicar el repositorio

1. Crear repo en GitHub (público solo si las reglas del evento lo permiten).
2. Subir estos archivos completos con `pyproject.toml` y `uv.lock`.
3. Invitar a los otros dos integrantes con cuentas propias.

## 2. Vercel

1. Ingresar a https://vercel.com/new → Import Git Repository.
2. Seleccionar la **raíz** del proyecto; no elegir `frontend/` como Root Directory.
3. Se detecta FastAPI gracias a `pyproject.toml`:
   ```toml
   [tool.vercel]
   entrypoint = "backend.main:app"
   ```
4. No configurar Build Command, Output Directory ni Docker.
5. Production Branch = `main`. Dar Deploy.
6. Confirmar `/`, `/static/css/tokens.css` y `/health` en la URL asignada.
7. Un PR debería lanzar CI y, si el plan y permisos lo permiten, una preview de Vercel;
   al integrar a `main`, producción se actualizará automáticamente.

> Nota: el auto-deploy desde Git y los checks de GitHub son procesos distintos. No se
> garantiza que Vercel espere automáticamente a CI: proteger `main` para bloquear merges
> con checks rojos, y configurar Deployment Checks si el plan lo ofrece.

## 3. Neon

1. Crear proyecto en https://console.neon.tech/.
2. Crear o seleccionar una base para **ensayos**; obtener la cadena *pooled*.
3. En Vercel → Project → Settings → Environment Variables, añadir `DATABASE_URL`
   (secreto, solo servidor). Seleccionar Production y, para Preview, otra base/rama aislada.
4. Redeploy y visitar `/health/db`.
   - `200`: la BD respondió a `SELECT 1`.
   - `503`: falta configurar la conexión o la BD está temporalmente no disponible.
5. Para probar localmente, crear `.env` con la URL (NO subirlo) y ejecutar:
   ```bash
   uv run --env-file .env python -m scripts.db_smoke
   ```
6. Solo crear tablas y migraciones cuando el ejercicio concreto las necesite.

## 4. Precauciones

- No incluir credenciales en HTML, repositorio ni logs.
- No usar archivos locales de Vercel como almacenamiento persistente.
- No ejecutar scripts de migración en cada request o cada build.
- En Vercel Hobby, el autor del commit de un despliegue debe ser el propietario del equipo;
  probar el proceso real con los tres integrantes antes de depender del deploy automático.

## 5. Recuperación

Si un PR rompe la demo: revertirlo en GitHub y confirmar el redeploy.
Guardar una captura y una grabación breve de la demo como plan de respaldo.

## Referencias

- https://vercel.com/docs/frameworks/backend/fastapi
- https://vercel.com/docs/git
- https://vercel.com/docs/deployments/troubleshoot-project-collaboration
- https://neon.com/docs/connect/connection-pooling
