# Kit de identidad visual NeoQuest (mínimo)

Contiene la skill de paleta, fondos, bordes, tipografía, iconos y estilos CSS básicos; incluye dos ilustraciones RPG originales. No define pantallas ni nombres/acciones de botones o tarjetas.


## Catálogo de fuentes elegido

Google Fonts (Latin): https://fonts.google.com/?preview.script=Latn

Ese es **el catálogo de tipografías**, no una fuente específica. El equipo/developer seleccionará la familia cuando apruebe los mockups. Hasta entonces se conserva `system-ui` como alternativa predeterminada, controlada por `--ll-font-ui` en `neoquest-theme.css`.

Al seleccionar una fuente: 1) abrir el catálogo, 2) verificar compatibilidad con acentos en español y claridad en lectura matemática, 3) copiar el código `<link>` que proporciona Google Fonts (o alojarla localmente si corresponde), 4) establecer `--ll-font-ui` en `neoquest-theme.css`. No hace falta instalar una librería de JS.

Para agregar también esta referencia al `README.md` principal de `abstracthon-edu`:

```markdown
### Tipografía del sistema de diseño
Catálogo de fuentes aprobado para explorar: [Google Fonts (Latin)](https://fonts.google.com/?preview.script=Latn).
La familia definitiva se escogerá con los mockups. El tema NeoQuest utiliza `--ll-font-ui` con `system-ui` como fallback.
```

## Iconografía de aventura (SVG originales)

- `character-portrait.svg` y `castle.svg`: iconos monocromáticos de 24 × 24, compatibles con `.ll-icon` / `currentColor` mediante CSS mask.
- `character-avatar.svg` y `adventure-castle.svg`: ilustraciones RPG multicolor para representar visualmente un personaje y un castillo. Usar `<img>` para mantener sus colores.

```html
<!-- Dibujo a color, sin definir comportamiento -->
<img src="{{ url_for('static', path='icons/character-avatar.svg') }}" alt="Retrato de personaje" width="64" height="64">
<img src="{{ url_for('static', path='icons/adventure-castle.svg') }}" alt="Ilustración de castillo" width="96" height="96">

<!-- Monocromáticos, color por CSS; decorativos -->
<span class="ll-icon ll-icon--character-portrait" aria-hidden="true"></span>
<span class="ll-icon ll-icon--castle" aria-hidden="true"></span>
```

Los dos nuevos diseños de aventura son creaciones originales para el kit; los restantes 34 SVG proceden de Lucide y mantienen su licencia ISC.

Para agregarlo sin sobrescribir los CSS existentes:

1. Copia `.agents/skills/neoquest-design-system/SKILL.md` a la misma ruta en tu repositorio.
2. Copia `frontend/static/css/neoquest-theme.css` y `neoquest-primitives.css`.
3. Copia los SVG de `frontend/static/icons/` y `frontend/static/css/neoquest-icons.css`.
4. En `frontend/templates/base.html`, después de las hojas existentes, agrega:

```html
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-theme.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-primitives.css') }}">
<link rel="stylesheet" href="{{ url_for('static', path='css/neoquest-icons.css') }}">
```

Uso visual de icono (sin asignar funcionalidad):

```html
<span class="ll-icon ll-icon--book-open" aria-hidden="true"></span>
```

Botón genérico: `<button class="ll-button" type="button">...</button>`.
Tarjeta genérica: `<article class="ll-card">...</article>`.

El desarrollador decide el texto, función, variantes, nombres de componentes concretos, rutas y estructura de pantalla al revisar su mockup.

Guía visual completa y accesibilidad en el PDF `LazyLearnAI_Catalogo_Iconos_NeoQuest.pdf`.

Origen de SVG: Lucide (https://lucide.dev/icons/), licencia ISC. Ver `frontend/static/icons/LICENSE_LUCIDE.txt`.
