# Abstracthon — repositorio base

**Base mínima para 3 desarrolladores y 2 ensayos.** Un monorepo, un FastAPI, un despliegue.
Aún no contiene una solución educativa específica.

## Tecnologías

Python 3.12, FastAPI, Jinja2, HTML/CSS, HTMX (opcional), Neon PostgreSQL (opcional),
uv, Ruff, Pytest, GitHub Actions y Vercel.

## Estructura

```text
frontend/
  templates/base.html
  templates/pages/
  templates/components/
  static/css/
  static/icons/
backend/
  main.py
  core/config.py, database.py
  modules/health/, modules/demo/
tests/                     # dos pruebas automáticas de arranque
migrations/                # para cuando haga falta persistencia
docs/                      # arquitectura, UI, deploy y equipo
.agents/skills/            # backend-feature, frontend-ui, review-pr
.github/workflows/ci.yml   # CI de cada PR
AGENTS.md
pyproject.toml + uv.lock (se genera al primer uv sync)
```

## 1. Instalar y arrancar

Instalar uv: https://docs.astral.sh/uv/getting-started/installation/

**Windows PowerShell y Linux** (mismos comandos con uv instalado):

```bash
uv sync --dev
uv run uvicorn backend.main:app --reload
```

Abrir http://127.0.0.1:8000

- `/` — página de práctica responsive.
- `/preview?tema=prueba` — flujo de muestra con formulario y Jinja2.
- `/health` — estado básico (sin base de datos).
- `/health/db` — verifica Neon; devuelve 503 hasta configurar `DATABASE_URL`.
- `/docs` — documentación interactiva FastAPI.

## 2. Ejecutar los checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

Para corregir formato: `uv run ruff format .`.

Los **2 tests incluidos** comprueban `/health` y el HTML/CSS de inicio; no requieren Neon.
GitHub Actions ejecuta estos tres checks al hacer PR y al integrar a `main`. Si `uv.lock` está presente lo respeta con `--locked`; por eso deben versionar el archivo generado al hacer `uv sync --dev`.

## 3. Crear un repositorio real en GitHub

1. Crear un repositorio vacío (sin README automático) en https://github.com/new.
2. Dentro de esta carpeta, ejecutar:

```bash
git init
git branch -M main
git add .
git commit -m "chore: iniciar base de hackathon"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

Cambiar `TU_USUARIO/TU_REPO`. Invitar a los otros 2 desde Settings > Collaborators.
Crear ramas `feature/*` y PR a `main`. **No subir `.env`.**

Opcional, con GitHub CLI autenticada: `gh repo create nombre-repo --public --source . --remote origin --push`.

## 4. Desplegar automáticamente en Vercel

1. Importar el GitHub repo en https://vercel.com/new.
2. Elegir la raíz del proyecto, rama de producción `main`; NO crear dos aplicaciones.
3. Vercel reconocerá `[tool.vercel] entrypoint = "backend.main:app"`.
4. Dar Deploy; abrir la URL y verificar `/` y `/health`.
5. Al incorporar cambios a `main`, Vercel volverá a desplegar automáticamente,
   según los permisos y límites de su plan.

En plan Hobby, **el autor del commit debe coincidir con el propietario del equipo Vercel**:
validar este punto con los tres antes del ensayo. Más detalles en `docs/DEPLOY.md`.

## 5. Conectar Neon (sin forzar a tener BD desde el día 1)

1. Crear base en https://console.neon.tech/ y copiar cadena PostgreSQL **pooled**.
2. Vercel → Environment Variables → `DATABASE_URL` (Production y, separadamente, Preview).
3. Para local, copiar `.env.example` a `.env`, completar `DATABASE_URL` y ejecutar:

```bash
uv run --env-file .env python -m scripts.db_smoke
uv run --env-file .env uvicorn backend.main:app --reload
```

**Jamás suban `.env` a Git.** Las pruebas de GitHub Actions no requieren secretos.

## 6. Guías del equipo

- `AGENTS.md`: reglas de codificación y asistentes IA.
- `docs/ARCHITECTURE.md`: esquema completo de la aplicación.
- `docs/DESIGN_SYSTEM.md`: tokens UI, botones y responsive.
- `docs/TEAM_WORKFLOW.md`: ramas, PR y revisión.
- `docs/DEPLOY.md`: paso a paso de Vercel y Neon.
- `docs/TWO_PRACTICES.md`: cómo organizar los dos ensayos.

> Esta es una preparación técnica. Verificar primero qué permite reutilizar la organización del evento.

## Preparación visual de LazyLearnAI — NeoQuest

Este paquete parte de la base de práctica previa. **Antes de utilizarlo en el concurso, revisar las reglas sobre código preexistente**, documentadas en `docs/PROCEDENCIA_Y_REGLAS.md`.

- `docs/README_NEOQUEST.md`: paleta, componentes base e iconografía para estudiantes.
- `docs/README_NEOQUEST_MENTOR.md`: variante más seria para docentes.
- `.agents/skills/neoquest-design-system/SKILL.md`: reglas reutilizables para el equipo y la IA.
- `frontend/static/css/neoquest-theme.css`: tokens, compatible con el starter.
- `frontend/static/css/neoquest-primitives.css`: botones y tarjetas genéricos, sin funcionalidades definidas.
- `frontend/static/css/neoquest-icons.css`: identificadores para SVG locales.
- `frontend/static/css/neoquest-mentor.css`: tokens específicos del ámbito `.theme--mentor`.
- `frontend/static/icons/`: SVG locales, licencia Lucide y arte propio del kit.

Las cuatro hojas NeoQuest se cargan en `frontend/templates/base.html`; el tema docente se activa únicamente al usar el contenedor `.theme--mentor`. La familia concreta de Google Fonts no está escogida todavía: https://fonts.google.com/?preview.script=Latn . Por defecto se utiliza `system-ui`.

**No hay integración Gemini ni Neon nueva en este paquete:** la conexión de prueba con PostgreSQL ya existía en el starter, y el proveedor de IA se integrará en su propia rama, después de acordar el contrato. No subir claves API al repositorio.
