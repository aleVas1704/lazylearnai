# Entrega local: conversación MCM y validadores por tema

## Resultado y alcance

Implementación local sobre la rama existente `feature/mvp-docente-fracciones`, conservando cambios previos. No se leyó `.env`, no se conectó Neon, no se ejecutaron migraciones, ni se hizo commit, push o despliegue. La tarea #8 no fue consultada ni modificada; su comportamiento de diez fracciones se protege con datos ficticios equivalentes.

Soporte real: `fraction_add_sub` (diez ejercicios y cuatro fases) y `mcm` (un ejercicio con enteros 1..100). El registro cerrado rechaza tipos desconocidos. Ecuaciones lineales, porcentajes y proporcionalidad quedan pendientes; no hay selectores que permitan publicarlos. Para extender: implementar `validate_plan`, `intro_message`, `evaluate_response`, `completed_count` y `total_exercises`; incorporar pruebas completas y ampliar el CHECK en una migración posterior.

## Archivos de esta intervención

- `backend/modules/guided_math/strategies.py`: registro y adaptador de fracciones; MCM con `math.lcm` y gramática conservadora.
- `backend/modules/guided_math/repository.py`: reserva temporal, deduplicación, exclusión de turnos concurrentes y guardado transaccional.
- `backend/modules/guided_math/service.py`: orquestación; Gemini fuera de transacciones; inicio/cierre MCM sin IA; respaldo local; progreso dinámico y métricas.
- `backend/modules/guided_math/rules.py`: evita avances ante preguntas y pedidos de respuesta; conserva fases de fracciones.
- `backend/modules/student_task_chat/gemini_client.py`: timeout y tokens configurables; un intento por llamada.
- `backend/modules/student_task_chat/repository.py`: orden lógico por relación pregunta/réplica, inicio primero y secuencia estable.
- `backend/modules/student_task_chat/routes.py`: progreso visible, recuperación de solicitudes pendientes y errores cotidianos.
- `backend/modules/teacher_portal/data.py`: publicación MCM, idempotencia por borrador, reportes dinámicos y comprobación de clase actual del docente.
- `backend/modules/teacher_portal/routes.py`: publicación por tipo y reporte sin IA; resumen opcional con progreso correcto.
- `backend/modules/student_access/http.py`: rechaza mutaciones sin evidencia de origen autorizado.
- `backend/core/timing.py`, `backend/main.py`: duración HTTP sin registrar contenido, identidades ni credenciales.
- `frontend/templates/pages/teacher_dashboard.html`, `frontend/static/js/teacher-portal.js`: borrador MCM sin IA, revisión/publicación, reporte 1/1 y textos cotidianos.
- `frontend/templates/pages/student_task_chat.html`, `frontend/static/js/student-task-chat.js`: progreso, escape Jinja, retorno al final de chat y bloqueo de doble envío.
- `frontend/templates/student_task_chat_base.html`: deja de cargar captura de pegados/cambios de pestaña. Los eventos históricos siguen disponibles.
- `migrations/007_topic_validators.sql`, `scripts/aplicar_mvp_007.py`: migración aditiva pendiente y ejecución manual con inspección por defecto.
- `tests/test_legacy.py`, `tests/test_topics.py`: regresión y aceptación offline.
- `scripts/verificar_tutor_conversacional.py`, `scripts/verificar_mvp_docente.py`: verificadores offline adaptados al comportamiento conservador.
- Este documento.

Los cambios anteriores en `.env.example`, login, prompts, CSS docente, migración 006 y otros archivos sin seguimiento no se descartaron. No se modificaron 005 ni 006. No se añadieron dependencias.

## Persistencia e idempotencia

007 añade tipo (por defecto fracciones), identificador de publicación, token/vencimiento/versión del turno y secuencia de mensajes. Añade también un registro mínimo de solicitudes IA docentes para limitar consumo. Mantiene JSONB como array e índices 1..10. MCM usa `concept → done`. Los CHECK de cantidad y completitud son NOT VALID para no reescribir filas históricas; sí se exigen en nuevas escrituras. No certifican la integridad histórica hasta una revisión posterior.

Una transacción corta reserva el turno; Gemini se ejecuta después de cerrar conexión; otra transacción comprueba token/versión y guarda réplica, estado y fecha juntos. Una reserva dura 45 s. Si el proceso muere, el mismo request_id puede recuperar el turno con explicación local, sin nueva llamada IA. El formulario recupera ese identificador del mensaje pendiente. Otro turno concurrente recibe espera y no avanza. Una respuesta de un proceso antiguo no puede sobrescribir la recuperación.

El orden respeta cada `reply_to_message_id`, no UUID aleatorios; se conserva el historial. En mensajes antiguos con tiempos idénticos y sin relación, no se puede reconstruir una cronología inexistente: la nueva secuencia proporciona un desempate estable.

## Evidencia offline

Tres pruebas base se ejecutaron antes de editar lógica. Suite final: 17 pruebas correctas (~0,2 s de ejecución de tests; no equivale a latencia real).

Cubren: los dos mensajes obligatorios; inicio sin IA; duda 0/1 sin fecha; cierre 1/1 con fecha; cinco mensajes; reporte docente y HTML de ambos paneles; gramática positiva/negativa; fallback por error y spoilers numéricos o «doce»; reintentos; reserva concurrente; recuperación; rollback simulado; rechazo de estudiante/docente ajenos; sesión/origen; creación de tarea nueva y publicación repetida; generación de diez fracciones con SDK simulado; diez ejercicios hasta 10/10; parámetros reales del SDK para timeout/reintentos.

La BD es un doble en memoria que ejecuta el flujo de repositorio y simula transacciones. Estas pruebas NO sustituyen ejecutar SQL en PostgreSQL ni comprobar navegador con Neon. El SDK y la red externa están bloqueados en pruebas; no se consume cuota. Starlette muestra un aviso de deprecación de su adaptador httpx; no se instalaron paquetes por ese aviso.

Ruff check, Ruff format --check y git diff --check pasan. Se verificó renderizado Jinja y respuestas HTTP en proceso. Queda comprobación visual manual en 390 px/escritorio y validación de sesiones reales.

## Comandos PowerShell

Ejecutar desde el repositorio. Las comprobaciones offline no cargan `.env`:

```powershell
Set-Location 'C:\Users\HP\Proyectos\lazylearnai'
uv run --offline --no-env-file python -m unittest discover -s tests -v
uv run --offline --no-env-file python -m scripts.verificar_mvp_docente
uv run --offline --no-env-file ruff check .
uv run --offline --no-env-file ruff format --check .
git diff --check
```

Antes de iniciar esta versión contra la base, revisar y aplicar 007. Estos comandos SÍ conectan a la base configurada y son para ejecución exclusiva del usuario. No volver a aplicar 005/006. Revisar que el entorno corresponde a desarrollo:

```powershell
Get-Content -LiteralPath .\migrations\007_topic_validators.sql
uv run --env-file .env python -m scripts.aplicar_mvp_007
# Solo después de revisar la inspección y decidir aplicar:
uv run --env-file .env python -m scripts.aplicar_mvp_007 --apply
# Escribir en el prompt: APLICAR 007 EN DESARROLLO
```

La inspección solo lee metadatos de columnas. La escritura es transaccional; ante error revierte y no imprime excepciones de conexión. Si detecta columnas existentes de 007, detiene aplicación para evitar repetir o aceptar una migración parcial. No iniciar esta versión contra esquema 006 solamente: necesita 007.

Para la demostración local, tras migración autorizada y con las variables ya configuradas por el usuario:

```powershell
$env:STUDENT_ALLOW_LOCAL_HTTP = '1'
uv run --env-file .env uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level info
```

No exportar `DATABASE_URL_DIRECT` a Vercel. El servidor usa `DATABASE_URL`; clave/modelo Gemini permanecen en servidor. No cambiar el modelo ya configurado en el entorno.

## Guion manual

1. Abrir http://127.0.0.1:8000/teacher/login con la cuenta docente existente.
2. Nueva tarea → seleccionar la clase de Matemáticas asignada → números 4 y 6 → **Preparar MCM sin IA** → revisar título, descripción y pregunta → **Publicar esta tarea**. Guardar el nuevo identificador; no reutilizar #8.
3. En otra ventana o sesión, entrar como estudiante existente desde http://127.0.0.1:8000/ y abrir la tarea nueva desde sus clases. Usar el botón de inicio si todavía no se inició.
4. Ver pregunta inicial y **En progreso · 0/1**. Enviar exactamente «¿Qué es el MCM y cómo se saca?». Comprobar explicación sin resultado y progreso todavía 0/1.
5. Enviar «Es 12». Ver confirmación y **Actividad completada · 1/1** sin espera de Gemini.
6. Docente: actualizar panel, abrir Reportes y **Ver chat**. Ver completada 1/1 y los cinco mensajes. No pulsar Generar resumen durante la demo.
7. Abrir #8 aparte para comprobar que permanece disponible con sus fracciones e historial.

## Latencia y pendientes de Preview

Se eliminó la llamada IA bajo bloqueo; se configuraron 8 s y 350 tokens para explicación, sin reintentos del SDK. Ese timeout no garantiza un tiempo total extremo a extremo. Logs `tutor_ms` contienen claim/explanation/persist/total; `http_total_ms` mide la petición. No contienen mensajes, claves ni nombres. No se midieron Neon, Gemini real, región ni cold starts.

El filtro antiespóiler es adicional, no una garantía semántica universal: cubre números y algunas palabras de la demo, no toda forma lingüística de expresar un resultado. El fallback permanece activo y no decide completitud.

Antes de Preview: ejecutar 007 en desarrollo, comprobar SQL/sesiones HTTPS, demo real de dos mensajes, permisos con cuentas reales y aspecto móvil. Se conservaron cookies HttpOnly/SameSite/Secure y la excepción local está desactivada en Vercel. El límite del cuerpo docente se redujo para mantener el archivo de 3 MB en base64 bajo el tamaño de petición esperado; falta validar el límite efectivo de la plataforma. Generación y resumen docentes requieren sesión y acción explícita, con cuota persistente por docente: 3 generaciones y 10 resúmenes cada 10 minutos; los fallos también consumen la reserva. Se limpian registros de más de un día del docente al aceptar una nueva solicitud. Los reportes no hacen acusaciones ni deducen tiempo de atención. Las credenciales demo y políticas de consentimiento necesitan revisión antes de acceso público.

