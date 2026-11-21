# 01 · Referencia aprobada para el acceso de estudiante

Fuente: `mockup-login-web-movil.png`, adjunto por el equipo de LazyLearnAI. La mitad izquierda de la imagen muestra **vista web**, y la derecha **vista móvil** del mismo formulario. Usarlo como referencia de diseño, NO copiarlo como un elemento de la página.

## Jerarquía exacta visible

- En la parte superior: libro abierto con destello y nombre **LazyLearnAI**.
- En el centro, sobre una tarjeta clara: etiqueta **Nombre**, campo; etiqueta **Carnet de identidad**, campo; botón amarillo **Entrar**.
- Fondo oscuro azul/violeta con cielo y nubes pixel-art.
- Personaje estudiante con mochila a la **izquierda, mirando** al castillo flotante ubicado a la **derecha**.
- En móvil, el formulario ocupa el centro superior y la escena del niño/castillo permanece visible en la parte inferior.

## No debe aparecer

No mostrar menú, barra lateral, materias, dashboard, chatbot, lecciones, texto promocional, contraseña, registro, botones extra, XP o logros: esta pantalla es solo de identificación de demostración.

## Paleta: reutilizar la del repo, no inventar otra

- `--ll-navy-950: #10152F` — cielo y capa oscura.
- `--ll-navy-800: #202B53` — profundidad.
- `--ll-purple-500: #7957FF` — violeta de acento.
- `--ll-purple-700: #6040DA` — violeta oscuro.
- `--ll-cyan-400: #31D8F7` — brillos discretos del arte.
- `--ll-gold-400: #FFC857` — CTA amarillo.
- `--ll-ice-50: #F7F8FC` — tarjeta y lectura.
- `--ll-border: #D8DFF0` — bordes claros.
- `--ll-font-ui` — tipografía compartida: `system-ui` hasta elegir familia de Google Fonts.

La referencia posee algo más de lavanda/púrpura que los tokens de base; si hay que crear un tono auxiliar para inputs, definir un token semántico específico y documentar la extensión.

## Tratamiento 8-bit

Los dibujos del personaje, castillo, nubes, elementos estelares y remates del botón deben ser pixel-art genuino; los textos del formulario deben permanecer nítidos y legibles (no pixelar el texto normal). Se puede agregar borde escalonado, sombra dura o textura muy suave al CTA, sin efectos pesados. No utilizar emojis como iconos principales.

## Assets

El repositorio ya contiene SVG para `book-open`, `user-round` y arte original `character-avatar.svg`, `adventure-castle.svg`. Para recrear el escenario completo se necesita un asset original limpio separado de la interfaz o composición con HTML/CSS/SVG; **ninguno de estos SVG es necesariamente el paisaje completo del mockup**.

No recortar el formulario del PNG ni poner el PNG del mockup como fondo. Aceptar que sin archivos de arte por capas no se garantiza una reproducción pixel por pixel. Si se dibuja un fondo aproximado, se debe informar honestamente.
