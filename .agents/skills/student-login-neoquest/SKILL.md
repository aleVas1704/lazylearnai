---
name: student-login-neoquest
description: Implementar la primera pantalla de acceso DEMO de estudiantes LazyLearnAI (Nombre, Carnet, Entrar), fiel al mockup NeoQuest, con backend FastAPI y PostgreSQL/Neon de prueba. No desarrollar otras pantallas.
---

# Skill: Acceso de estudiante · LazyLearnAI

## Activación

Utiliza esta skill solo para la tarea de la **primera pantalla de acceso de estudiante**, aprobada en el mockup ubicado en `docs/codex/acceso-estudiante/mockup-login-web-movil.png`.

## Lectura obligatoria antes de tocar código

1. `AGENTS.md` y `.agents/skills/neoquest-design-system/SKILL.md`.
2. `.agents/skills/frontend-ui/SKILL.md` y `.agents/skills/backend-feature/SKILL.md`.
3. `docs/codex/acceso-estudiante/01_REFERENCIA_VISUAL.md`.
4. `docs/codex/acceso-estudiante/02_FRONTEND_RESPONSIVE.md`.
5. `docs/codex/acceso-estudiante/03_BACKEND_BD.md`.
6. `docs/codex/acceso-estudiante/04_ACEPTACION_MANUAL.md`.
7. Plantillas, CSS, rutas y config existentes del repositorio.

## Restricciones

- Pantalla con **solo** logo libro, Nombre, Carnet y botón Entrar.
- Fondo pixel-art: chico con mochila mirando castillo flotante; reencuadre responsive.
- Colores NeoQuest existentes, iconos SVG locales, HTML/Jinja2/CSS nativo; no React, Node, Tailwind ni dependencias innecesarias.
- FastAPI modular: `routes.py`, `service.py`, `repository.py`, PostgreSQL con `psycopg` cuando se requiera persistencia.
- El número de documento **NO es un factor de autenticación**. Solo demo ficticia; no almacenar carnet en claro, usar HMAC con secreto, cookies seguras y migración manual.
- No implementar Gemini, materias, chat IA, XP ni perfil docente.
- Sin Pytest ni GitHub Actions (decisión explícita del equipo); revisión manual + Ruff.
- Proteger trabajo de otros: rama feature propia, PR a main, no force push ni sobrescrituras ajenas.

## Proceso

1. Leer y hacer plan breve por archivos.
2. Construir frontend responsive fiel al mockup, con recursos originales separados de la captura.
3. Implementar módulo de demostración backend con validación y persistencia mínima.
4. Documentar variables y migración manual sin exponer datos personales ni secretos.
5. Comprobar visual y funcionalmente de forma manual; entregar capturas reales.
6. Resumir lo conseguido y las desviaciones del mockup; dejar PR listo sin fusionar.
