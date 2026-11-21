# Migraciones

`001_student_access.sql` crea los perfiles ficticios y las sesiones del acceso de demostración.
`002_student_dashboard.sql` crea materias, inscripciones, tareas y asignaciones.
`003_student_task_chat.sql` añade el contenido de la tarea y persiste conversaciones y mensajes.
Las migraciones son idempotentes para tablas, columnas e índices; no modifican datos por sí solas.

Aplicar manualmente y únicamente en una base o rama de Neon de ensayo. Usar
`DATABASE_URL_DIRECT` para la migración y `DATABASE_URL` pooled para la aplicación.
No ejecutar migraciones al importar FastAPI, durante el build ni en cada solicitud.

`demo_student_dashboard.sql` es opcional y carga datos claramente marcados como demo para un
perfil ficticio indicado mediante `psql -v profile_id=...`. No representa acciones docentes.

Ver comandos, variables y comprobaciones en `docs/codex/acceso-estudiante/05_IMPLEMENTACION.md`
y `docs/codex/panel-estudiante/IMPLEMENTACION.md`. La integración del tutor requiere además
`GEMINI_API_KEY`; `GEMINI_MODEL` permite cambiar el modelo sin modificar código.
