# PROMPT COMPLETO PARA CODEX — LAZYLEARNAI / ACCESO ESTUDIANTE

Actúa como desarrollador full-stack senior y responsable de implementar una sola funcionalidad acotada de LazyLearnAI. Trabaja **sobre el repositorio abierto en el workspace** `lazylearnai` y en una **rama de feature propia**. No reinicies el proyecto ni crees un frontend separado. Primero revisa la estructura real y las instrucciones locales; luego implementa de forma incremental.

## 0. Contexto que debes leer antes de editar

Lee completamente los documentos existentes:

- `AGENTS.md`
- `.agents/skills/neoquest-design-system/SKILL.md`
- `.agents/skills/frontend-ui/SKILL.md`
- `.agents/skills/backend-feature/SKILL.md`
- `.agents/skills/student-login-neoquest/SKILL.md`
- `docs/ARCHITECTURE.md`
- `docs/DESIGN_SYSTEM.md`
- `docs/README_NEOQUEST.md`
- `frontend/templates/base.html`, `frontend/templates/pages/home.html`
- `frontend/static/css/tokens.css`, `neoquest-theme.css`, `neoquest-primitives.css`, `neoquest-icons.css`, `base.css`, `components.css`, `layout.css`
- `backend/main.py`, `backend/core/config.py`, `backend/core/database.py`, `backend/modules/demo/routes.py`, `pyproject.toml`, `.env.example`

También revisa el mockup real `docs/codex/acceso-estudiante/mockup-login-web-movil.png` y las cuatro especificaciones en la carpeta `docs/codex/acceso-estudiante/`.

Antes de modificar archivos, devuelve un plan breve con: archivos afectados, cómo aislar la pantalla del layout demo actual, estrategia de assets, contrato HTTP/BD, variables de entorno y cómo revisar manualmente el resultado. **No solicites recrear el proyecto ni cambies el stack.**

## 1. Resultado que quiero

Implementa **solo la primera pantalla de acceso del estudiante**, replicando lo más fielmente posible la referencia visual proporcionada en ambas resoluciones: **vista web/escritorio y vista móvil responsive**.

Elementos obligatorios, y únicamente estos en el formulario:

1. Logo con icono de **libro abierto + pequeña estrella**, seguido de `LazyLearnAI`.
2. Campo etiquetado **Nombre**.
3. Campo etiquetado **Carnet de identidad**.
4. Un solo botón principal amarillo con texto **Entrar**, con icono de acceso si resulta fiel al mockup.

No agregues enlaces de registro, contraseña, “olvidé mi contraseña”, menú de navegación, XP, tarjetas de materias, lecciones, chatbot, ilustraciones de funciones nuevas ni banners promocionales; la vista debe permanecer muy simple y fiel a la imagen.

El fondo es parte esencial de la identidad: **estilo retro pixel-art de videojuego, cielo azul-violeta, nubes 8-bit, montañas, el personaje estudiante con mochila mirando hacia un castillo flotante**, conservando la composición: personaje a la izquierda y castillo a la derecha en escritorio, ambos reconocibles en la parte inferior del móvil. Utiliza recursos locales originales separados; revisa primero si el repositorio ya incluye `character-avatar.svg`, `adventure-castle.svg` y otros SVG. **NO uses el PNG completo del mockup como un background** porque incluye campos y botón dibujados que no serían interactivos. Si no hay una imagen de fondo limpia y no puedes generarla, construye una aproximación honesta con CSS/SVG/arte existente y explícame qué detalle no quedó idéntico.

La tarjeta del formulario tendrá fondo muy claro, bordes suaves, campos lavanda, texto azul oscuro y un botón dorado de aspecto 8-bit. Evita neón excesivo sobre el texto. Para lectura utiliza tipografía legible (`--ll-font-ui`; de momento `system-ui`, pues el equipo solo eligió el catálogo Google Fonts, no una familia concreta). Para los iconos de campos usa los SVG del kit; si necesitas uno inexistente, agrégalo como SVG local coherente y con licencia o atribución adecuada.

## 2. Stack obligatorio

- Python 3.12 + una sola aplicación FastAPI.
- HTML semántico + Jinja2 y CSS nativo; HTMX **opcional** si de verdad aporta algo.
- JavaScript vanilla mínimo si fuera imprescindible.
- PostgreSQL/Neon con `psycopg` **ya incluido** para persistencia de demostración.
- `uv` para dependencias y Ruff para formato manual.
- Iconos SVG locales y tokens NeoQuest ya existentes.

**Prohibido:** React, Next.js, Vue, Tailwind, Bootstrap, Node, `package.json`, backend separado, servicios de login externos, CSS frameworks o dependencias adicionales sin justificar y sin aprobación. No implementes integración Gemini: **este primer login no necesita IA**.

## 3. Respeta el código y a los otros desarrolladores

No borres el código de los compañeros ni reestructures las carpetas. Trabaja en la rama `feature/student-login-neoquest` a partir del `main` actualizado, con árbol de trabajo limpio. Si hay cambios sin confirmar en el repositorio, informa el estado y evita `reset --hard`, `clean -fd`, `force push` o sobreescritura. No hagas cambios sobre la rama `main`.

El starter hoy utiliza `GET /` para una demo; al convertir `/` en pantalla de acceso, conserva la demo previa en una ruta secundaria como `/demo` si es viable, sin eliminar `/preview`, `/health`, `/health/db` ni `/docs`.

Para esta nueva función organiza el código preferentemente en:

- `backend/modules/student_access/routes.py`
- `backend/modules/student_access/service.py`
- `backend/modules/student_access/repository.py`
- `frontend/templates/pages/student_login.html`
- `frontend/static/css/student-login.css`
- `migrations/001_student_access.sql`

Admite `models.py` o una plantilla mínima adicional **solo si justificas su necesidad**. `backend/main.py` únicamente registra el router y, si hace falta, actualiza el título de la app. Evita reescribir `base.html` global; si su header demo no corresponde al login, usa un layout Jinja2 propio para esta pantalla o bloques adecuados, sin afectar otras páginas.

## 4. Contrato frontend y comportamiento

- `GET /`: renderiza la página de login con Jinja2 y código HTTP 200 sin requerir conexión a BD para cargar el diseño.
- `POST /student/access`: recibe un formulario HTML con `name` y `identity_number`; valida del lado servidor y nunca envía el número en URL.
- Envío con formulario HTML funcional **sin JavaScript**; HTMX no es obligatorio.
- Campos obligatorios y mensajes de error claros en español, asociados con sus inputs; nunca imprimir valores sensibles en la página ni errores SQL.
- Se admite un nombre de 2 a 80 caracteres, se normalizan espacios y se bloquea longitud excesiva; el número de documento se trata como texto para no eliminar ceros a la izquierda, con reglas sencillas de validación explícitas en el código. No asumir que una cédula verificada identifica realmente al usuario.
- Si la BD aún no está configurada, la página sigue mostrando el formulario, pero el POST produce un error de configuración **amigable y controlado**, no un 500 ni un falso éxito.
- Tras un envío de demostración válido y persistido, crear una sesión **de prueba** en el servidor y hacer un redirect 303 a un destino de confirmación mínimo; **no diseñar una segunda pantalla completa ni inventar un dashboard**. Si el equipo todavía no ha definido la pantalla siguiente, explica cuál ruta provisional utilizaste.
- El submit no debe generar registros duplicados para un mismo carnet de prueba. El comportamiento de nombre distinto para una identidad ya existente debe ser seguro y explícito.

## 5. Privacidad y BD: requisito crítico

La interfaz solicita **Nombre y Carnet de identidad**, que son datos personales; el público contempla estudiantes de secundaria. Por ello esta etapa debe ser claramente **DEMO con datos sintéticos, no un sistema de autenticación real**. Implementa todo con datos ficticios y evita introducir cédulas reales.

- No almacenar el número de carnet en texto plano.
- Si se necesita reconocer un identificador repetido, usar `HMAC-SHA256` del documento normalizado con una clave exclusiva del servidor (`STUDENT_ID_HMAC_KEY`, variable privada >=32 bytes) y guardar solo el resultado; NO usar hash SHA-256 simple sin clave para un valor de baja entropía.
- Guardar un perfil mínimo con `id UUID`, `display_name`, `identity_hmac` único y `created_at`.
- Guardar sesiones de demo en tabla independiente con identificador de perfil, `token_hash` de un token aleatorio seguro, `expires_at` y `created_at`; el token solo va en cookie HttpOnly con SameSite=Lax, y `Secure` al usar HTTPS.
- No colocar el número en logs, mensajes de error, rutas, cookies, analytics o HTML posterior a submit.
- No subir `.env` ni claves a Git. Añadir los nombres de variables, vacíos, a `.env.example` y explicar cómo generar claves de forma segura.
- Queries siempre parametrizadas con `psycopg`; sin SQL interpolado desde campos del usuario.
- No ejecutar migraciones automáticamente al iniciar FastAPI ni en el build de Vercel. Añadir SQL de migración **manual**, sin `DROP TABLE` ni operaciones destructivas.
- No devolver trazas de PostgreSQL a la interfaz; proteger fallos y recuperar controladamente.

**Advertencia explícita en documentación:** nombre + carnet no autentica identidades, no es apto para producción escolar y puede ser suplantado; antes de usar con menores se necesita consentimiento/política de datos, autorización del centro y un mecanismo de autenticación real.

La estructura y los criterios concretos de BD están en `docs/codex/acceso-estudiante/03_BACKEND_BD.md`.

## 6. Validación visual y de calidad

- Visual desktop **1440px**, tablet **768px** y smartphone **390px**. Sin desbordamiento horizontal ni controles cortados.
- En móvil, el teclado no debe tapar el botón; la tarjeta es totalmente usable sin hover.
- Mantén la misma pantalla en ambos formatos, no secciones extra.
- Contraste >=4.5:1 para texto normal, foco visible, labels reales y objetivos táctiles >=44px.
- Ajusta el fondo para que personaje/castillo no compitan con formulario; el texto nunca debe colocarse sobre la ilustración.
- Respeta `prefers-reduced-motion`; evita animaciones continuas y efectos pesados.
- Comprueba que el botón funciona con Enter, tabulación, sin JS y con errores de entrada.
- Levanta el proyecto con `uv sync --dev` y `uv run uvicorn backend.main:app --reload`.
- Revisa el formato manualmente con `uv run ruff check .` y `uv run ruff format --check .` (puedes ejecutar `uv run ruff format .` si es necesario).
- **NO crear Pytest, carpeta `tests/` ni GitHub Actions**: el equipo los descartó expresamente. Documenta las comprobaciones manuales reales.

## 7. Entregables de la implementación

1. Resumen de lo implementado y rutas HTTP finales.
2. Lista exacta de archivos modificados/creados, explicando la separación rutas–servicio–repositorio.
3. Capturas reales del navegador **web y móvil** que permitan comparar con la referencia.
4. Migración SQL y pasos de configuración de Neon/Postgres, sin claves.
5. Evidencia manual de éxito, validación fallida, DB desconfigurada y acceso repetido sin duplicados.
6. Resultados reales de `ruff check` y `ruff format --check`.
7. Riesgos conocidos (especialmente autenticación no segura) y cuestiones pendientes.
8. Commit(s) en rama de feature y Pull Request hacia `main`, **sin fusionarlo**.

**Regla de alcance:** implementa exclusivamente esta primera pantalla y su backend/BD mínima de demostración. No agregues aún materias, tareas, tutor IA, gamificación, ni panel docente; estas partes tienen sus propias especificaciones y responsables.
