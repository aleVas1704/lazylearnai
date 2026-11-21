# LazyLearnAI — base de desarrollo

Proyecto web educativo en desarrollo para un equipo de tres personas. El repositorio conserva la arquitectura de la práctica y los temas NeoQuest de estudiantes y mentores/docentes. Las pantallas, acciones y reglas de negocio definitivas dependen de los mockups aprobados.

## Tecnologías

- **Backend:** Python 3.12, FastAPI, Uvicorn y Jinja2.
- **Interfaz:** HTML, CSS nativo, HTMX opcional y JavaScript mínimo cuando haga falta.
- **Diseño:** NeoQuest (estudiantes) y NeoQuest Mentor (docentes), SVG locales Lucide y arte RPG propio.
- **Datos:** PostgreSQL con Neon, solo cuando se requiera persistencia.
- **IA:** Gemini API, integración pendiente de desarrollar y configurar.
- **Dependencias y formato:** `uv` y Ruff (solo uso local).
- **Despliegue:** Vercel desde GitHub, cuando lo decida el equipo.

El equipo revisará manualmente los flujos de usuario antes de integrar cambios.

## Estructura

```text
backend/                   Aplicación FastAPI y módulos
frontend/templates/        Plantillas y componentes Jinja2
frontend/static/css/       CSS y temas NeoQuest
frontend/static/icons/     Lucide SVG y arte RPG local
docs/                      Arquitectura, diseño y colaboración
.agents/skills/            Instrucciones para asistentes de programación
.github/pull_request_template.md  Plantilla de revisión manual
migrations/                Reservado para futuros cambios de esquema
.env.example               Nombres de variables (sin secretos)
pyproject.toml             Dependencias y configuración del proyecto
uv.lock                    Generado con el primer `uv sync --dev`
```

## 1. Instalación local

Instalar `uv`: https://docs.astral.sh/uv/getting-started/installation/

```powershell
uv sync --dev
uv run uvicorn backend.main:app --reload
```

Abrir `http://127.0.0.1:8000`. Rutas técnicas existentes: `/`, `/preview?tema=ejemplo`, `/health`, `/health/db` y `/docs`. No se ha construido aún la funcionalidad definitiva de LazyLearnAI.

## 2. Revisión manual del código

Ruff sirve para detectar problemas de estilo y aplicar formato, sin montar un sistema de pruebas automáticas:

```powershell
uv run ruff check .
uv run ruff format .
```

Antes de incorporar cambios, revisar en el navegador la funcionalidad afectada, el tamaño móvil y escritorio, mensajes de error y la ausencia de secretos en el repositorio. Los PR se revisan por otra persona.

## 3. Variables de entorno

Copiar `.env.example` a `.env` solo cuando se vayan a configurar servicios; `.env` está ignorado por Git.

- `DATABASE_URL`: conexión PostgreSQL/Neon de servidor. No es necesaria para abrir la demo básica.
- `DATABASE_URL_DIRECT`: solo si una operación administrada necesita conexión directa.
- `GEMINI_API_KEY`: nombre reservado para la integración de Gemini; no tiene efecto hasta implementar el cliente.

Para iniciar con un `.env` local:

```powershell
uv run --env-file .env uvicorn backend.main:app --reload
```

Neon: tras configurar `DATABASE_URL`, consultar `/health/db`; sin configurar devuelve 503 de manera controlada.

## 4. Dos variantes visuales, una sola aplicación

- `docs/README_NEOQUEST.md`: visual de estudiantes.
- `docs/README_NEOQUEST_MENTOR.md`: visual sobrio de docentes.
- `.agents/skills/neoquest-design-system/SKILL.md`: tokens, fondos, bordes, iconos, tipografía y componentes genéricos.
- `frontend/static/css/neoquest-theme.css`, `neoquest-primitives.css`, `neoquest-icons.css` y `neoquest-mentor.css`: hojas compartidas ya referenciadas en `frontend/templates/base.html`.
- `frontend/static/icons/`: archivos SVG con sus licencias y arte original.

La variante docente utiliza `.theme--mentor`. Se mantiene `system-ui` hasta que el equipo seleccione una familia de [Google Fonts](https://fonts.google.com/?preview.script=Latn).

## 5. Trabajo colaborativo y despliegue

Crear ramas `feature/*` o `fix/*`, abrir Pull Request y solicitar una revisión humana antes de integrar en `main`. Consultar `docs/TEAM_WORKFLOW.md` y `AGENTS.md`.

El proyecto conserva `[tool.vercel] entrypoint = "backend.main:app"`; cuando se despliegue, importar la **raíz** del repositorio. Ver `docs/DEPLOY.md`.

## 6. Procedencia y reglas del evento

Este starter procede de la preparación del equipo. Confirmar con la organización si es válido reutilizar código previo; crear un repositorio nuevo no cambia su procedencia. Detalles en `docs/PROCEDENCIA_Y_REGLAS.md`.
