# Flujo de equipo (3 desarrolladores)

## Ramas

`main`: estable. `feature/<cambio>`: funcionalidad. `fix/<cambio>`: reparación.
Una persona toma una tarea. Otro integrante revisa el PR.

```bash
git switch main
git pull origin main
git switch -c feature/primer-cambio
# editar y comprobar
git add .
git commit -m "feat: agregar primer cambio"
git push -u origin feature/primer-cambio
```

Abrir PR → revisión manual de código y funcionamiento → merge a `main`.

## Archivo de propiedad compartida

Avisar antes de modificar: `backend/main.py`, `pyproject.toml` y, cuando se genere, `uv.lock`,
`frontend/static/css/tokens.css` y los estilos visuales compartidos.

## Uso de IA

Antes de pedir cambios, especificar objetivos, archivos permitidos y criterios de aceptación.
Revisar manualmente la funcionalidad y entender el código generado antes de crear el PR. Usar Ruff localmente si es necesario.

## Vercel Hobby

Verificar autoría de commits: el plan Hobby puede bloquear despliegues cuando el autor no es
el propietario del equipo de Vercel. No modificar autorías para evadir la restricción. Usar un
plan compatible o probar un flujo autorizado donde el responsable de despliegue publique la versión.
