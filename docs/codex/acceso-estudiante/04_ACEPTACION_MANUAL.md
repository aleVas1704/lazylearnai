# 04 · Criterios de aceptación y verificación manual

El equipo ha retirado Pytest y GitHub Actions de esta etapa. Esta lista **no crea tests automáticos**, pero sí exige una revisión manual responsable antes de integrar.

## Criterios visuales

- [ ] La pantalla muestra exclusivamente logo/libro + marca, Nombre, Carnet de identidad y un botón Entrar.
- [ ] Colores y tokens pertenecen a NeoQuest (`neoquest-theme.css`); botón amarillo con texto oscuro, tarjeta legible, campos lavanda.
- [ ] El fondo muestra un estudiante con mochila **mirando un castillo**, con estilo pixel-art 8-bit; no se usa el screenshot entero como falsa interfaz.
- [ ] La vista es usable a 390px, 768px y 1440px, sin overflow horizontal ni botón cortado.
- [ ] El foco del teclado es visible, etiquetas de formulario están asociadas y Enter permite enviar.
- [ ] La composición móvil conserva el fondo sin tapar los controles; se puede hacer scroll al aparecer el teclado.

## Criterios funcionales

- [ ] `GET /` devuelve HTML 200 incluso sin Neon configurado.
- [ ] Un POST con nombre vacío o carnet incorrecto muestra mensajes controlados, sin revelar el valor del carnet.
- [ ] Un POST ficticio válido **con BD configurada** crea perfil/sesión de demostración y 303 a confirmación mínima.
- [ ] El mismo carnet ficticio no duplica perfil y la diferencia de nombre se trata sin revelar datos del perfil.
- [ ] El identificador en base se guarda como HMAC, no documento en claro; sesión se almacena como hash.
- [ ] La cookie es `HttpOnly`, `SameSite=Lax`, y `Secure` cuando se utiliza HTTPS.
- [ ] Si no hay `DATABASE_URL`, POST informa fallo controlado y no aparenta guardar datos.
- [ ] `/health`, `/health/db`, `/docs` y `/preview` funcionan según su contrato existente.
- [ ] La migración SQL es manual, documentada y no destructiva.

## Comandos reales

```powershell
uv sync --dev
uv run uvicorn backend.main:app --reload
uv run ruff check .
uv run ruff format --check .
```

Si el formato falla, ejecutar `uv run ruff format .` y verificar de nuevo. No afirmar que se corrieron comandos o pruebas que no se ejecutaron.

## Entrega a revisión

Capturas de la pantalla en navegador desktop 1440px y móvil 390px; resumen de archivos y rutas; SQL y variables de entorno; resultados reales de comandos; limitaciones y riesgos. No incorporar a `main` sin revisión del equipo.
