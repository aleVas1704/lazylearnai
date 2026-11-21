# LazyLearnAI — NeoQuest Mentor

**Guía adicional de identidad visual para el perfil docente / mentor**  
**Estado:** propuesta visual, no especificación de producto.  
**Compatible con:** Python 3.12, FastAPI, Jinja2, HTML, CSS nativo y HTMX opcional.

## 1. Objetivo

Mantener una sola identidad LazyLearnAI para estudiantes y docentes. El perfil estudiantil conserva una estética de aventura más vistosa; **NeoQuest Mentor** utiliza los mismos iconos, tipografía, bordes y componentes base, pero con colores azul pizarra, índigo moderado, verde azulado y superficies claras. Las ilustraciones RPG se usan con moderación.

**Esta guía no define** pantallas, módulos, menús, textos de botones, enlaces, rutas, permisos, acciones de HTMX/JavaScript, gráficos, métricas ni reglas educativas. Todo eso se concretará mediante los mockups que apruebe el equipo.

## 2. Fuente y tecnología

- Catálogo de fuentes acordado: [Google Fonts — Latin](https://fonts.google.com/?preview.script=Latn).
- La **familia exacta sigue pendiente** de aprobación: se aplicará la **misma que el perfil de estudiantes**. Hasta entonces conservar `--ll-font-ui: system-ui, ...` del tema NeoQuest original.
- No instalar librerías de componentes o fuentes para JavaScript. La tipografía puede cargarse mediante el `<link>` oficial de Google Fonts cuando se seleccione, o alojarse localmente si el equipo lo decide.
- Usar `frontend/templates/` para Jinja2; `frontend/static/css/` para estilos; `frontend/static/icons/` para SVG. Mantener un único backend FastAPI; no agregar React, Tailwind, Next.js, Bootstrap ni `package.json`.

## 3. Paleta NeoQuest Mentor

Esta variante usa como referencia la propuesta visual docente más reciente; es **una paleta diferente dentro del mismo sistema**, no un segundo design system.

| Token CSS | Valor | Uso visual sugerido |
|---|---|---|
| `--ll-navy-950` | `#0B1B36` | Barra o área oscura |
| `--ll-navy-800` | `#1E2E4D` | Paneles oscuros y navegación |
| `--ll-purple-500` | `#3F5E9E` | Azul índigo de énfasis |
| `--ll-purple-700` | `#314F88` | Botón genérico con texto blanco |
| `--ll-cyan-400` | `#14B8A6` | Acentos y progreso |
| `--ll-lime-300` | `#29B78B` | Acento de estado positivo |
| `--ll-gold-400` | `#B89352` | Insignias RPG discretas |
| `--ll-ice-50` | `#E2E8F0` | Superficies pálidas y separadores |
| `--ll-white` | `#F8FAFC` | Tarjetas y zonas de lectura |
| `--ll-bg` | `#F4F6FA` | Fondo general |
| `--ll-surface` | `#F8FAFC` | Superficie elevada |
| `--ll-text` | `#14213A` | Texto principal |
| `--ll-muted` | `#53647E` | Texto secundario |
| `--ll-border` | `#CCD5E3` | Bordes sutiles |
| `--ll-focus` | `#0E746B` | Foco visible de mayor contraste |

Regla: las tablas, textos largos y formularios usan superficies claras con texto oscuro; los azules profundos se reservan principalmente para navegación o detalles. Los colores de acento no sustituyen las etiquetas textuales ni validan por sí solos el significado de un estado. Para foco y texto sobre fondos claros se utiliza turquesa oscuro `#0E746B`, no el turquesa brillante `#14B8A6`, que ofrece contraste insuficiente como texto pequeño.

## 4. Componentes neutrales reutilizados

Se reutilizan las **mismas primitivas** del kit estudiantil. No crear otra familia de componentes ni nombrarlos según funcionalidades que todavía no están definidas.

| Clase existente | Responsabilidad visual |
|---|---|
| `.ll-button` | Área interactiva de botón; sin etiqueta ni evento predeterminado |
| `.ll-card` | Contenedor con borde, radio, padding y sombra |
| `.ll-game-shell` | Superficie oscura de identidad |
| `.ll-reading-surface` | Zona clara y legible |
| `.ll-icon` | Icono local monocromático mediante CSS `mask` |
| `.ll-icon--sm` / `.ll-icon--lg` | Tamaño 18 px / 32 px |

Estética común a ambos perfiles:
- Radios de **8 / 12 / 18 px**; 18 px para tarjeta grande y 12 px para botón.
- Borde estándar de **1 px** y sombra difusa suave.
- Espaciado consistente de **4 / 8 / 12 / 16 / 24 / 32 px**.
- Controles táctiles de al menos **44 × 44 px**, foco visible y buen contraste.
- Evitar neón excesivo, animaciones constantes y texto sobre ilustraciones complejas.

Ejemplo visual sin nombre de botón ni lógica asignada:

```html
<div class="theme--mentor">
  <div class="ll-reading-surface">
    <article class="ll-card">
      <!-- Estructura y contenido definidos por el mockup aprobado. -->
      <button class="ll-button" type="button">
        <!-- Etiqueta real definida por el desarrollador. -->
      </button>
    </article>
  </div>
</div>
```

El ejemplo es solo de **clases visuales**; una implementación real debe asignar etiqueta accesible y acción al botón y elegir la etiqueta semántica apropiada para cada elemento.

## 5. Iconos y elementos RPG compartidos

No instalar bibliotecas nuevas. Reutilizar el catálogo e iconos locales del kit anterior: [Lucide](https://lucide.dev/icons/) con archivos SVG dentro de `frontend/static/icons/` y las cuatro ilustraciones/iconos RPG originales.

**Iconos Lucide disponibles y útiles en un contexto docente (sin fijar su función):**

- `book-open`, `book-check`, `graduation-cap`, `notebook-pen`, `clipboard-list`, `file-text`.
- `users`, `user-round`, `chart-no-axes-column`, `target`, `circle-check`, `calendar-days`, `clock-3`.
- `lightbulb`, `message-circle`, `brain`, `bot`, `sparkles`, `search`, `settings`.
- `trophy`, `medal`, `star`, `shield-check` para detalles decorativos.

**Arte RPG original del kit anterior:**

- `character-portrait.svg` y `castle.svg`: versiones monocromáticas; pueden cambiar de color con `.ll-icon` y CSS `mask`.
- `character-avatar.svg` y `adventure-castle.svg`: ilustraciones multicolor, adecuadas como decoración discreta con `<img>`.
- El arte se usa con moderación: un encabezado o un acento ilustrativo suele ser suficiente para transmitir la temática de academia/aventura.

Ejemplo con SVG local monocromático:

```html
<span class="ll-icon ll-icon--graduation-cap" aria-hidden="true"></span>
<span class="ll-icon ll-icon--book-open" aria-hidden="true"></span>
```

Ejemplo de imagen decorativa multicolor:

```html
<img
  src="{{ url_for('static', path='icons/adventure-castle.svg') }}"
  alt=""
  width="96"
  height="96"
  loading="lazy"
>
```

Para iconos **decorativos**, `aria-hidden="true"` o `alt=""`; para iconos que aporten significado, incluir una etiqueta de texto accesible (el desarrollador la define según la acción real). No usar `<img>` para cambiar dinámicamente el color de un SVG con `currentColor`; para ello utilizar `.ll-icon` o SVG inline.

## 6. Instalación sin afectar la vista de estudiantes

Se asume que el equipo **ya integró el kit NeoQuest estudiantil v2**, en particular:

```text
frontend/static/css/neoquest-theme.css
frontend/static/css/neoquest-primitives.css
frontend/static/css/neoquest-icons.css
frontend/static/icons/*.svg
```

Añadir **solo** `frontend/static/css/neoquest-mentor.css` a la carpeta de CSS y cargarlo **después** de las hojas existentes:

```html
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-theme.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-primitives.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-icons.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-mentor.css') }}">
```

Asignar la clase `theme--mentor` **solo al contenedor o vista que defina el desarrollador**. La vista estudiantil continúa usando el tema base NeoQuest. No es necesario cambiar rutas ni lógica Python para aplicar los colores; si el proyecto utiliza una plantilla base compartida, el desarrollador decide cómo transmitir la clase al elemento correcto.

**Atención:** el CSS del kit anterior usa variables como `--ll-purple-700`, `--ll-navy-950` y `--ll-white`; el nuevo tema las sobrescribe solo dentro de `.theme--mentor`. Por eso siguen funcionando `.ll-button`, `.ll-card`, `.ll-icon` y los fondos sin crear nuevas clases de botón o tarjeta.

## 7. Validación antes de integrar

- Confirmar que activar `.theme--mentor` no modifica colores de la vista de estudiantes.
- Revisar contraste (objetivo WCAG AA: 4.5:1 texto normal, 3:1 texto grande), navegación por teclado y foco visible.
- Probar en 390 px, 768 px y 1440 px. No depender solo del color para comunicar estados.
- Si se añade una fuente de Google Fonts, probar acentos en español, ecuaciones y tiempos de carga; respetar preferencias de movimiento reducido.
- Revisar manualmente en el navegador y documentar problemas reales. Ruff es opcional y se utiliza localmente para estilo.

## 8. Instrucción para el desarrollador o asistente de IA

> Lee `.agents/skills/neoquest-design-system/SKILL.md`, este README y los CSS del kit NeoQuest v2. Implementa exclusivamente la variante **NeoQuest Mentor** mediante tokens, fondos, bordes, iconos SVG y componentes visuales neutros. Reutiliza `ll-button` y `ll-card` sin inventar nuevas funciones, nombres de botones, rutas, interacciones HTMX, módulos ni reglas de negocio: espera al mockup aprobado para decidirlos. Mantén la misma familia tipográfica que estudiantes y evita instalar dependencias nuevas.

---

**Documento complementario; no modifica el README principal, el repositorio GitHub ni el diseño estudiantil.**
