# Despliegue: GitHub + Vercel + Neon

## 1. Publicar el repositorio

1. Crear repo en GitHub (público solo si las reglas del evento lo permiten).
2. Subir los archivos del proyecto con `pyproject.toml`. Generar y versionar `uv.lock` tras ejecutar `uv sync --dev`.
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
7. Si el plan y los permisos lo permiten, los PR podrán tener previews de Vercel.
   Antes de integrar a `main`, revisar manualmente el cambio y el despliegue.

## 3. Neon

1. Crear proyecto en https://console.neon.tech/.
2. Crear o seleccionar una base para **ensayos**; obtener la cadena *pooled*.
3. En Vercel → Project → Settings → Environment Variables, añadir `DATABASE_URL`
   (secreto, solo servidor). Seleccionar Production y, para Preview, otra base/rama aislada.
4. Redeploy y visitar `/health/db`.
   - `200`: la BD respondió a `SELECT 1`.
   - `503`: falta configurar la conexión o la BD está temporalmente no disponible.
5. Para revisar la conexión desde el navegador, crear `.env` con la URL (NO subirlo), iniciar con `uv run --env-file .env uvicorn backend.main:app --reload` y consultar `/health/db`.
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
