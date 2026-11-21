# Frontend

El frontend usa **Jinja2 + HTML + CSS nativo + HTMX opcional**, servido por el mismo FastAPI.
No tiene `package.json` ni se despliega por separado.

- `templates/base.html`: estructura común.
- `templates/pages/`: páginas por funcionalidad.
- `templates/components/`: macros y fragmentos reutilizables.
- `static/css/tokens.css`: colores, espaciado y tipografía compartidos.
- `static/css/components.css`: estilos de botones, tarjetas, formularios y estados.
- `static/css/layout.css`: grillas y media queries.
- `static/icons/`: SVG de iconos Lucide usados por la aplicación.

Trabajar desde Figma con los componentes definidos. Ver `docs/DESIGN_SYSTEM.md`.
Probar móvil y escritorio después de cada cambio visual.
