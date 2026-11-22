# Entrega local: conversaciÃ³n MCM y validadores por tema

## Resultado y alcance

ImplementaciÃ³n local sobre la rama existente `feature/mvp-docente-fracciones`, conservando cambios previos. No se leyÃ³ `.env`, no se conectÃ³ Neon, no se ejecutaron migraciones, ni se hizo commit, push o despliegue. La tarea #8 no fue consultada ni modificada; su comportamiento de diez fracciones se protege con datos ficticios equivalentes.

Soporte real: `fraction_add_sub` (diez ejercicios y cuatro fases) y `mcm` (un ejercicio con enteros 1..100). El registro cerrado rechaza tipos desconocidos. Ecuaciones lineales, porcentajes y proporcionalidad quedan pendientes; no hay selectores que permitan publicarlos. Para extender: implementar `validate_plan`, `intro_message`, `evaluate_response`, `completed_count` y `total_exercises`; incorporar pruebas completas y ampliar el CHECK en una migraciÃ³n posterior.

## Archivos de esta intervenciÃ³n

- `backend/modules/guided_math/strategies.py`: registro y adaptador de fracciones; MCM con `math.lcm` y gramÃ¡tica conservadora.
- `backend/modules/guided_math/repository.py`: reserva temporal, deduplicaciÃ³n, exclusiÃ³n de turnos concurrentes y guardado transaccional.
- `backend/modules/guided_math/service.py`: orquestaciÃ³n; Gemini fuera de transacciones; inicio/cierre MCM sin IA; respaldo local; progreso dinÃ¡mico y mÃ©tricas.
- `backend/modules/guided_math/rules.py`: evita avances ante preguntas y pedidos de respuesta; conserva fases de fracciones.
- `backend/modules/student_task_chat/gemini_client.py`: timeout y tokens configurables; un intento por llamada.
- `backend/modules/student_task_chat/repository.py`: orden lÃ³gico por relaciÃ³n pregunta/rÃ©plica, inicio primero y secuencia estable.
- `backend/modules/student_task_chat/routes.py`: progreso visible, recuperaciÃ³n de solicitudes pendientes y errores cotidianos.
- `backend/modules/teacher_portal/data.py`: publicaciÃ³n MCM, idempotencia por borrador, reportes dinÃ¡micos y comprobaciÃ³n de clase actual del docente.
- `backend/modules/teacher_portal/routes.py`: publicaciÃ³n por tipo y reporte sin IA; resumen opcional con progreso correcto.
- `backend/modules/student_access/http.py`: rechaza mutaciones sin evidencia de origen autorizado.
- `backend/core/timing.py`, `backend/main.py`: duraciÃ³n HTTP sin registrar contenido, identidades ni credenciales.
- `frontend/templates/pages/teacher_dashboard.html`, `frontend/static/js/teacher-portal.js`: borrador MCM sin IA, revisiÃ³n/publicaciÃ³n, reporte 1/1 y textos cotidianos.
- `frontend/templates/pages/student_task_chat.html`, `frontend/static/js/student-task-chat.js`: progreso, escape Jinja, retorno al final de chat y bloqueo de doble envÃ­o.
- `frontend/templates/student_task_chat_base.html`: deja de cargar captura de pegados/cambios de pestaÃ±a. Los eventos histÃ³ricos siguen disponibles.
- `migrations/007_topic_validators.sql`, `scripts/aplicar_mvp_007.py`: migraciÃ³n aditiva pendiente y ejecuciÃ³n manual con inspecciÃ³n por defecto.
- `tests/test_legacy.py`, `tests/test_topics.py`: regresiÃ³n y aceptaciÃ³n offline.
- `scripts/verificar_tutor_conversacional.py`, `scripts/verificar_mvp_docente.py`: verificadores offline adaptados al comportamiento conservador.
- Este documento.

Los cambios anteriores en `.env.example`, login, prompts, CSS docente, migraciÃ³n 006 y otros archivos sin seguimiento no se descartaron. No se modificaron 005 ni 006. No se aÃ±adieron dependencias.

## Persistencia e idempotencia

007 aÃ±ade tipo (por defecto fracciones), identificador de publicaciÃ³n, token/vencimiento/versiÃ³n del turno y secuencia de mensajes. AÃ±ade tambiÃ©n un registro mÃ­nimo de solicitudes IA docentes para limitar consumo. Mantiene JSONB como array e Ã­ndices 1..10. MCM usa `concept â†’ done`. Los CHECK de cantidad y completitud son NOT VALID para no reescribir filas histÃ³ricas; sÃ­ se exigen en nuevas escrituras. No certifican la integridad histÃ³rica hasta una revisiÃ³n posterior.

Una transacciÃ³n corta reserva el turno; Gemini se ejecuta despuÃ©s de cerrar conexiÃ³n; otra transacciÃ³n comprueba token/versiÃ³n y guarda rÃ©plica, estado y fecha juntos. Una reserva dura 45 s. Si el proceso muere, el mismo request_id puede recuperar el turno con explicaciÃ³n local, sin nueva llamada IA. El formulario recupera ese identificador del mensaje pendiente. Otro turno concurrente recibe espera y no avanza. Una respuesta de un proceso antiguo no puede sobrescribir la recuperaciÃ³n.

El orden respeta cada `reply_to_message_id`, no UUID aleatorios; se conserva el historial. En mensajes antiguos con tiempos idÃ©nticos y sin relaciÃ³n, no se puede reconstruir una cronologÃ­a inexistente: la nueva secuencia proporciona un desempate estable.

## Evidencia offline

Tres pruebas base se ejecutaron antes de editar lÃ³gica. Suite final: 17 pruebas correctas (~0,2 s de ejecuciÃ³n de tests; no equivale a latencia real).

Cubren: los dos mensajes obligatorios; inicio sin IA; duda 0/1 sin fecha; cierre 1/1 con fecha; cinco mensajes; reporte docente y HTML de ambos paneles; gramÃ¡tica positiva/negativa; fallback por error y spoilers numÃ©ricos o Â«doceÂ»; reintentos; reserva concurrente; recuperaciÃ³n; rollback simulado; rechazo de estudiante/docente ajenos; sesiÃ³n/origen; creaciÃ³n de tarea nueva y publicaciÃ³n repetida; generaciÃ³n de diez fracciones con SDK simulado; diez ejercicios hasta 10/10; parÃ¡metros reales del SDK para timeout/reintentos.

La BD es un doble en memoria que ejecuta el flujo de repositorio y simula transacciones. Estas pruebas NO sustituyen ejecutar SQL en PostgreSQL ni comprobar navegador con Neon. El SDK y la red externa estÃ¡n bloqueados en pruebas; no se consume cuota. Starlette muestra un aviso de deprecaciÃ³n de su adaptador httpx; no se instalaron paquetes por ese aviso.

Ruff check, Ruff format --check y git diff --check pasan. Se verificÃ³ renderizado Jinja y respuestas HTTP en proceso. Queda comprobaciÃ³n visual manual en 390 px/escritorio y validaciÃ³n de sesiones reales.

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

Antes de iniciar esta versiÃ³n contra la base, revisar y aplicar 007. Estos comandos SÃ conectan a la base configurada y son para ejecuciÃ³n exclusiva del usuario. No volver a aplicar 005/006. Revisar que el entorno corresponde a desarrollo:

```powershell
Get-Content -LiteralPath .\migrations\007_topic_validators.sql
uv run --env-file .env python -m scripts.aplicar_mvp_007
# Solo despuÃ©s de revisar la inspecciÃ³n y decidir aplicar:
uv run --env-file .env python -m scripts.aplicar_mvp_007 --apply
# Escribir en el prompt: APLICAR 007 EN DESARROLLO
```

La inspecciÃ³n solo lee metadatos de columnas. La escritura es transaccional; ante error revierte y no imprime excepciones de conexiÃ³n. Si detecta columnas existentes de 007, detiene aplicaciÃ³n para evitar repetir o aceptar una migraciÃ³n parcial. No iniciar esta versiÃ³n contra esquema 006 solamente: necesita 007.

Para la demostraciÃ³n local, tras migraciÃ³n autorizada y con las variables ya configuradas por el usuario:

```powershell
$env:STUDENT_ALLOW_LOCAL_HTTP = '1'
uv run --env-file .env uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level info
```

No exportar `DATABASE_URL_DIRECT` a Vercel. El servidor usa `DATABASE_URL`; clave/modelo Gemini permanecen en servidor. No cambiar el modelo ya configurado en el entorno.

## Guion manual

1. Abrir http://127.0.0.1:8000/teacher/login con la cuenta docente existente.
2. Nueva tarea â†’ seleccionar la clase de MatemÃ¡ticas asignada â†’ nÃºmeros 4 y 6 â†’ **Preparar MCM sin IA** â†’ revisar tÃ­tulo, descripciÃ³n y pregunta â†’ **Publicar esta tarea**. Guardar el nuevo identificador; no reutilizar #8.
3. En otra ventana o sesiÃ³n, entrar como estudiante existente desde http://127.0.0.1:8000/ y abrir la tarea nueva desde sus clases. Usar el botÃ³n de inicio si todavÃ­a no se iniciÃ³.
4. Ver pregunta inicial y **En progreso Â· 0/1**. Enviar exactamente Â«Â¿QuÃ© es el MCM y cÃ³mo se saca?Â». Comprobar explicaciÃ³n sin resultado y progreso todavÃ­a 0/1.
5. Enviar Â«Es 12Â». Ver confirmaciÃ³n y **Actividad completada Â· 1/1** sin espera de Gemini.
6. Docente: actualizar panel, abrir Reportes y **Ver chat**. Ver completada 1/1 y los cinco mensajes. No pulsar Generar resumen durante la demo.
7. Abrir #8 aparte para comprobar que permanece disponible con sus fracciones e historial.

## Latencia y pendientes de Preview

Se eliminÃ³ la llamada IA bajo bloqueo; se configuraron 8 s y 350 tokens para explicaciÃ³n, sin reintentos del SDK. Ese timeout no garantiza un tiempo total extremo a extremo. Logs `tutor_ms` contienen claim/explanation/persist/total; `http_total_ms` mide la peticiÃ³n. No contienen mensajes, claves ni nombres. No se midieron Neon, Gemini real, regiÃ³n ni cold starts.

El filtro antiespÃ³iler es adicional, no una garantÃ­a semÃ¡ntica universal: cubre nÃºmeros y algunas palabras de la demo, no toda forma lingÃ¼Ã­stica de expresar un resultado. El fallback permanece activo y no decide completitud.

Antes de Preview: ejecutar 007 en desarrollo, comprobar SQL/sesiones HTTPS, demo real de dos mensajes, permisos con cuentas reales y aspecto mÃ³vil. Se conservaron cookies HttpOnly/SameSite/Secure y la excepciÃ³n local estÃ¡ desactivada en Vercel. El lÃ­mite del cuerpo docente se redujo para mantener el archivo de 3 MB en base64 bajo el tamaÃ±o de peticiÃ³n esperado; falta validar el lÃ­mite efectivo de la plataforma. GeneraciÃ³n y resumen docentes requieren sesiÃ³n y acciÃ³n explÃ­cita, con cuota persistente por docente: 3 generaciones y 10 resÃºmenes cada 10 minutos; los fallos tambiÃ©n consumen la reserva. Se limpian registros de mÃ¡s de un dÃ­a del docente al aceptar una nueva solicitud. Los reportes no hacen acusaciones ni deducen tiempo de atenciÃ³n. Las credenciales demo y polÃ­ticas de consentimiento necesitan revisiÃ³n antes de acceso pÃºblico.
