---
name: neoquest-design-system
description: Aplica únicamente la identidad visual NeoQuest de LazyLearnAI (paleta, fondos, bordes, iconos y componentes visuales básicos) en Jinja2 y CSS nativo. No determina pantallas, nombres de acciones ni funcionalidades.
---

# NeoQuest — Skill visual mínima de LazyLearnAI

## 1. Alcance exacto

Esta skill define la **apariencia compartida** de LazyLearnAI. NO decide funcionalidades, rutas, acciones de botones, nombres comerciales de componentes, pantallas, flujos educativos, reglas de gamificación ni posición final de los elementos. Todo eso lo decidirá el desarrollador a partir del mockup aprobado.

Se permiten únicamente:
- Paleta cromática y tokens semánticos.
- Fondos, superficies, bordes, radios, sombras y foco visible.
- Iconografía SVG de trazo lineal.
- Estilos visuales neutros para **botón genérico** y **tarjeta genérica**, sin texto, comportamiento o variante funcional predefinidos.

**No** convertir este documento en una especificación funcional ni añadir componentes de tareas, tutor, XP o navegación sin aprobación.

## 2. Arquitectura que se debe respetar

Proyecto existente: Python 3.12, FastAPI, Jinja2, HTML, CSS nativo, HTMX opcional, PostgreSQL/Neon cuando se necesite persistencia. Un solo monolito. Consultar `AGENTS.md`, `docs/ARCHITECTURE.md`, `frontend/README.md` y `docs/DESIGN_SYSTEM.md`.

No instalar React, Next.js, Tailwind, Bootstrap, dependencias de iconos ni Node. No crear un `package.json` ni un segundo frontend. No tocar backend, rutas, pruebas ni configuración para aplicar la paleta.

## 3. Paleta oficial propuesta: NeoQuest

| Token CSS | Hex | Uso recomendado |
|---|---|---|
| `--ll-navy-950` | `#10152F` | Fondo principal oscuro o navegación |
| `--ll-navy-800` | `#202B53` | Paneles y superficies oscuras |
| `--ll-purple-500` | `#7957FF` | Acento violeta y efectos puntuales |
| `--ll-purple-700` | `#6040DA` | Superficie de acción genérica con texto blanco |
| `--ll-cyan-400` | `#31D8F7` | Iconos y detalles de IA |
| `--ll-lime-300` | `#B9F46A` | Avance y éxito visual |
| `--ll-gold-400` | `#FFC857` | Destacados y recompensas |
| `--ll-ice-50` | `#F7F8FC` | Zona clara para lectura |
| `--ll-white` | `#FFFFFF` | Tarjetas y campos claros |
| `--ll-muted` | `#4D5874` | Texto secundario sobre claro |
| `--ll-border` | `#D8DFF0` | Límites sutiles de tarjetas claras |
| `--ll-success-ink` | `#17633E` | Texto de éxito, alto contraste |
| `--ll-error-ink` | `#A1233D` | Texto de error |

No dispersar valores hex por las páginas: usar variables desde `frontend/static/css/neoquest-theme.css`. No modificar la paleta según cada pantalla sin aprobación del equipo.

### Aplicación cromática

- Zona de navegación o fondo con estética gamer: azul noche `--ll-navy-950`, con bloques `--ll-navy-800`.
- Áreas donde se estudia, lee o escribe: fondo `--ll-ice-50`, contenido `--ll-white` y texto `--ll-navy-950`.
- Reservar violeta, cian, lima y dorado para acentos. **No** poner párrafos largos sobre fondos saturados o gradientes.
- El significado no debe depender solo del color: usar texto y, cuando corresponda, un icono accesible.
- Violeta claro `--ll-purple-500` es un acento; para botones con texto blanco es preferible `--ll-purple-700`.

## 4. Bordes, esquinas, profundidad y espaciado

| Token | Valor | Uso |
|---|---|---|
| `--ll-radius-sm` | `8px` | Elementos compactos |
| `--ll-radius-md` | `12px` | Componentes básicos |
| `--ll-radius-lg` | `18px` | Tarjetas principales |
| `--ll-radius-pill` | `999px` | Chips e insignias sin decidir contenido |
| `--ll-border-width` | `1px` | Bordes normales |
| `--ll-outline-width` | `3px` | Foco de teclado |
| `--ll-shadow-card` | `0 12px 28px rgb(16 21 47 / 9%)` | Elevación moderada |
| `--ll-space-1/2/3/4/6/8` | `4/8/12/16/24/32px` | Ritmo vertical y horizontal |

Preferir bordes sutiles a brillos fuertes. Una decoración de videojuego puede aparecer en encabezados o ilustraciones, pero no alrededor de todos los campos de lectura.

## 5. Tipografía y accesibilidad

- **Catálogo tipográfico elegido por el equipo:** [Google Fonts (Latin)](https://fonts.google.com/?preview.script=Latn). Este enlace es un catálogo; **la familia concreta aún no está seleccionada** y debe decidirla el desarrollador con el mockup aprobado.
- Fuente provisional/fallback: `system-ui`; token de tipografía `--ll-font-ui` en `neoquest-theme.css`.
- Una vez aprobada la familia, añadir en `base.html` el `<link>` oficial generado por Google Fonts o alojar la fuente según las necesidades de privacidad y rendimiento; actualizar `--ll-font-ui` para que se aplique en toda la interfaz.
- Elegir una fuente de lectura con acentos en español y caracteres matemáticos necesarios; probar pesos 400, 600 y 700. No descargar ni incorporar archivos de fuente sin selección y revisión de licencia.
- Texto normal: **16px mínimo** en lectura e interacción de estudio; línea de texto 1.5 o más.
- Elementos interactivos: área táctil mínima de **44 × 44px**.
- Foco visible mediante `:focus-visible`, sin eliminar el `outline` sin reemplazo.
- Revisar contraste de texto normal >= 4.5:1 y de texto grande >= 3:1 para WCAG AA.
- Comprobar anchuras 390, 768 y 1440px y la preferencia `prefers-reduced-motion`.

## 6. Iconos: una sola familia visual

Utilizar **Lucide SVG** (https://lucide.dev/icons/) para iconos de interfaz, preferentemente como archivos locales en `frontend/static/icons/` para evitar dependencias en tiempo de ejecución.

**Excepción de arte RPG propio:** el kit agrega `character-portrait.svg` y `castle.svg` (monocromáticos para CSS mask), más `character-avatar.svg` y `adventure-castle.svg` (ilustraciones multicolor originales). Estos últimos son **assets decorativos**, no componentes funcionales ni iconos Lucide; se renderizan con `<img>` para conservar sus colores. Son reinterpretaciones originales de la temática, no copias exactas del mockup generado.

- Apariencia: `viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`, `stroke-width="2"`, extremos y uniones redondeados.
- Tamaños de referencia: 18px dentro de texto, 20/24px para interfaz, 28/32px para ilustrar una sección.
- No mezclar al azar Lucide, Font Awesome, emojis y bibliotecas de iconos llenos. Las dos ilustraciones RPG originales son una excepción explícita y limitada para la identidad visual.
- Nunca usar un icono solo para explicar una acción importante: acompañarlo de una etiqueta o un `aria-label` adecuado.
- Para SVG insertado con `<img>`, el atributo `currentColor` del archivo **no hereda** automáticamente el color CSS del contenedor. Si hay que cambiar color desde CSS, usar un **CSS mask** o SVG inline.
- El nombre del archivo sí identifica el icono (`book-open.svg`, `bot.svg`, etc.); **no** define funcionalidades de la aplicación.
- Consultar el catálogo PDF actualizado (36 iconos monocromáticos + 2 ilustraciones RPG multicolor) antes de incorporar iconos nuevos.

## 7. Componentes visuales BASE (sin funciones ni nombres de negocio)

Están autorizadas solo estas dos primitivas visuales:

```html
<button class="ll-button" type="button">
  <!-- El desarrollador define el texto, el tipo y la acción desde el mockup -->
</button>

<article class="ll-card">
  <!-- El desarrollador define título, datos y semántica desde el mockup -->
</article>
```

- `ll-button` es **únicamente estilo visual**: tipografía, altura, borde, radio, foco y transición.
- `ll-card` es **únicamente contenedor visual**: superficie, borde, radio, padding y sombra.
- No crear `ll-start-button`, `ll-quest-card`, `ll-teacher-stat`, etc. en esta skill.
- No asignar `onclick`, `hx-get`, `hx-post`, rutas, valores, textos ni IDs predeterminados.
- El desarrollador decide si corresponde `<button>`, `<a>`, `<article>` o `<section>` según la funcionalidad real.
- En código de CSS usar clases para estilos y reservar `id` para elementos únicos, accesibilidad o interacciones HTMX definidas después.

## 8. Fondos y superficies base

- `.ll-game-shell`: fondo oscuro, apto para menús o envolturas de aplicación.
- `.ll-reading-surface`: zona clara para información y formularios.
- `.ll-card`: superficie y borde genéricos.
- `.ll-icon`: icono monocromático controlado por `currentColor` con máscara CSS y archivo SVG local.
- No fijar diseños de pantalla ni posición de componentes dentro de estas clases.

Los archivos incluidos son `neoquest-theme.css` y `neoquest-primitives.css`. Se pueden enlazar al final de las hojas CSS existentes. Se mantienen los alias actuales del starter (`--bg`, `--surface`, `--text`, `--brand`, `--brand-hover`, `--line`, `--focus` y `--radius`).

## 9. Procedimiento para un desarrollador o agente de IA

1. Leer esta skill y los CSS existentes antes de añadir estilos.
2. Verificar si el mockup aprobado utiliza modo oscuro, superficie clara o ambos.
3. Elegir solo tokens existentes. Si falta uno, proponerlo y justificarlo antes de crear una variante. Para tipografía, consultar Google Fonts y decidir la familia tras aprobar el mockup.
4. Elegir Lucide para la interfaz y, cuando el mockup lo justifique, una de las dos ilustraciones RPG originales incluidas; conservar el archivo de licencia de Lucide.
5. Usar únicamente `ll-button` y `ll-card` como componentes genéricos hasta que se aprueben mockups y alcance.
6. Validar legibilidad, estados de foco, responsive y ausencia de texto sobre colores neón.
7. Ejecutar e informar resultados reales: `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest -q`.

**No inferir pantallas, nombres, funciones o lógica educativa a partir de ejemplos visuales.**
