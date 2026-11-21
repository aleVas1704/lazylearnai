---
name: review-pr
description: Revisar PR de hackathon antes de integrar a main.
---

# Revisión de integración

1. Leer el alcance declarado del PR.
2. Buscar secretos o `.env`, cambios accidentales y dependencias innecesarias.
3. Verificar estructura, enlaces, renderizado y compatibilidad del backend.
4. Ejecutar Ruff, formato y Pytest (no afirmar resultados sin ejecutarlos).
5. Si cambió UI, probar el flujo responsive y los estados de error.
6. Señalar problemas concretos por archivo, gravedad y corrección propuesta.
7. Confirmar que el despliegue no necesita migraciones o variables no documentadas.
