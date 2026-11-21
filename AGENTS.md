# Reglas compartidas del repositorio

Este proyecto contiene una **sola aplicación FastAPI** con carpetas `frontend/` y `backend/`.
Sirve como base de **dos ensayos**; no presupone el desafío que se anuncie oficialmente.

## Arquitectura
- `backend/main.py` ensambla la aplicación; no acumular lógica allí.
- `backend/modules/<feature>/routes.py` gestiona HTTP, `service.py` lógica de negocio y
  `repository.py` SQL si la funcionalidad requiere persistencia.
- `frontend/templates/` contiene páginas y componentes Jinja2; `frontend/static/` contiene CSS,
  iconos SVG y JavaScript reducido. NO crear un segundo servidor frontend.
- Una sola instancia FastAPI se despliega a Vercel; Neon se conecta desde el servidor.

## UI
- Seguir `docs/DESIGN_SYSTEM.md` y reutilizar tokens y componentes existentes.
- CSS nativo, responsive mobile-first, iconos SVG de estilo Lucide.
- Evitar interfaces genéricas con demasiados gradientes, brillos o efectos.

## Calidad y seguridad
- Revisar manualmente cada funcionalidad y sus estados de error antes de entregar.
- Ruff puede utilizarse localmente para revisar estilo y formatear: `uv run ruff check .` y `uv run ruff format .`.
- No subir `.env`, claves, tokens, cookies ni datos de usuario al repositorio.
- No exponer `DATABASE_URL` ni errores internos de Neon en respuestas HTML/JSON.
- Nunca ejecutar migraciones destructivas automáticamente en el arranque o build.
- No agregar frameworks, servicios ni dependencias sin justificarlo al equipo.

## Colaboración
- Cada cambio en rama `feature/*`, `fix/*` o `docs/*` con PR pequeño hacia `main`.
- No reestructurar carpetas ni editar archivos ajenos a la tarea sin coordinar.
- Mantener `main` demostrable y la demo de Vercel estable.
- Los agentes deben resumir archivos modificados, comprobaciones y riesgos.

## Skills
- `.agents/skills/backend-feature/SKILL.md`
- `.agents/skills/frontend-ui/SKILL.md`
- `.agents/skills/review-pr/SKILL.md`

Seguir las restricciones sobre IA y código previo anunciadas por la organización del evento.
