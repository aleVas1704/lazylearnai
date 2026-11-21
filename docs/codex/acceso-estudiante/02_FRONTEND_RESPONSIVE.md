# 02 · Contrato visual y responsive

## Elementos de interfaz

Un logo gráfico (libro + destello) y marca LazyLearnAI, dos pares `<label for>`/`<input id>` y un `<button type="submit">Entrar</button>` dentro de un `<form method="post">`. Los nombres de campo (`name`, `identity_number`) son un contrato técnico para el backend, no nuevos elementos visibles.

No añadir placeholder si afecta la fidelidad visual; si se usa, que sea discreto y no sustituya a la etiqueta. Los estados de error y carga solo aparecen cuando corresponda.

## Diseño a tres anchuras

**Escritorio ≥1024px:** fondo completo (cielo, nubes, montañas), logo centrado encima del formulario, tarjeta de aprox. 460–500 px sobre el centro o centro-derecha, niño visible en sector inferior izquierdo y castillo a la derecha; ambos fuera del área táctil del formulario.

**Tablet 768px:** tarjeta centrada y no más ancha que el viewport menos márgenes; paisaje reencuadrado sin recortar campos o CTA.

**Móvil 390px:** logo superior, tarjeta centrada de ancho disponible menos 16–24px por lado, inputs y CTA a 100% del contenedor, boy y castillo reconocibles en el tercio inferior cuando haya altura suficiente. Si el teclado virtual aparece, priorizar acceso al botón sobre exhibición del paisaje. Permitir scroll vertical en móviles pequeños.

## Comportamiento y accesibilidad

- No desbordamiento horizontal a 320/390/768/1440px.
- Labels visibles, iconos decorativos `aria-hidden="true"`, logo con nombre accesible.
- `autocomplete="name"` para Nombre cuando aplique; documento no debe tener `type="number"`.
- Textos base 16 px, elementos táctiles al menos 44 px, contraste WCAG AA y foco `:focus-visible`.
- `aria-describedby` para errores; sin exponer el documento en mensajes de error.
- Botón funcional con teclado y sin JavaScript; evitar `onclick` y dependencias de un CDNs para el submit.
- Usar clases CSS específicas de la página **solo para layout**; tokens y primitivas siguen en NeoQuest compartido.
- `prefers-reduced-motion: reduce` elimina transiciones no esenciales.

## Prioridad visual

1. Estructura exacta de 2 campos + CTA y ausencia de elementos extra.
2. Legibilidad, colores, botones, radios, iconos y espaciado.
3. Composición y escala responsive; artes del niño y castillo.
4. Detalles decorativos como estrellas, nubes y sombreado.

No ocultar errores de programación con capturas falsas, ni afirmar que la imagen fue reproducida exactamente si no se dispone del arte original.
