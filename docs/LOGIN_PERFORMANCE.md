# Diagnóstico y optimización del login

## Conclusión y límites

El recorrido tenía aperturas TCP/TLS repetidas y consultas de conteo por clase en el panel docente. Se redujeron sin quitar consultas de sesión, rol, matrícula o propiedad. No hay Gemini en el login: su cuota o tiempo de generación no explica directamente este recorrido.

No se reprodujeron los 20 segundos con Neon real. Se respetó la prohibición vigente de acceder a Neon o leer secretos. No se puede atribuir esa demora a una consulta concreta, a suspensión del compute, a región, DNS o cold start sin medir el entorno real. Tampoco se comprobó si la URL actualmente configurada es pooled; ahora el servidor puede informar su clasificación sin imprimirla.

## Antes y después medidos

Mediciones tomadas sobre el código antes y después, con el mismo doble de BD, siete muestras por escenario y PBKDF2 real de 200.000 iteraciones sobre credenciales ficticias. Costes artificiales: apertura 5 ms, sentencia 2 ms y fin de transacción 1 ms. Windows añade variación de planificación: las medianas no son predicciones de Neon.

| Recorrido completo | Antes | Después |
| --- | ---: | ---: |
| Estudiante: conexiones | 4 | 2 |
| Estudiante: sentencias explícitas | 10 | 10 |
| Estudiante: mediana offline | 167,29 ms | 152,63 ms |
| Docente con 6 clases: conexiones | 5 | 3 |
| Docente con 6 clases: sentencias explícitas | 12 | 6 |
| Docente con 6 clases: mediana offline | 174,23 ms | 150,25 ms |

Evidencia: `docs/login_baseline.json` y `docs/login_after.json`. Los conteos no incluyen los mensajes BEGIN/COMMIT emitidos por el driver; se conservan cuatro transacciones del recorrido estudiante y cinco del docente. No se afirma una mejora de 20 segundos a esos valores.

## Cambios

- `backend/core/database.py`: envoltorio de conexiones/consultas con métricas; reutilización dentro de una unidad síncrona y un solo hilo. Cierre garantizado al salir y transacciones independientes con commit/rollback. No guarda conexiones entre peticiones ni crea un pool global.
- `backend/core/timing.py`: métricas por petición de login/dashboard, contraseña, consulta, fetch, conexión, transacción, carga y render. Cabeceras `Server-Timing` y `X-Performance-Id` aleatorio sin relación con sesión. Conserva la métrica HTTP simple para las otras rutas.
- `backend/modules/student_access/repository.py`, `service.py`, `routes.py`: instrumentación y reutilización de la conexión entre búsqueda de cuenta y guardado de sesión, manteniendo la revalidación del rol antes de insertar.
- `backend/modules/student_dashboard/repository.py`, `service.py`, `routes.py`: sesión y carga del panel en una unidad síncrona, con una conexión y transacciones separadas. Una sesión inválida nunca carga datos.
- `backend/modules/teacher_portal/auth.py`, `data.py`, `routes.py`: autenticación instrumentada; tres lecturas del panel comparten conexión; los conteos de alumnos se obtienen en la consulta de clases. La subconsulta correlacionada evita viajes por clase, aunque su coste SQL interno depende de datos/índices existentes.
- `scripts/benchmark_login_offline.py`: medición reproducible sin red, con entorno vacío y psycopg simulado.
- `tests/test_login_performance.py`: 13 pruebas nuevas; se mantienen las 17 anteriores.

No cambia la fortaleza PBKDF2, los timeouts existentes, los roles, la caducidad de sesión, las cookies, los filtros de matrícula ni los de propiedad docente. No se cachean usuarios, tokens ni decisiones de autorización. No se añadieron dependencias, migraciones ni cambios de esquema. No se tocó configuración remota ni se desplegó.

## Qué registran los nuevos logs

Una línea `login_performance` por petición a `/student/access`, `/teacher/access` o sus dashboards:

- `route`: categoría fija; nunca la URL, query string ni un identificador de usuario.
- `request`: ID aleatorio nuevo por petición. Se puede comparar con `X-Performance-Id` en el navegador.
- `status`, `http_ms`: estado HTTP y tiempo total dentro de ASGI.
- `database_endpoint`: `neon_pooled`, `neon_direct`, `other` o `unknown`, según formato del hostname; no se muestra hostname, base, usuario ni URL.
- `phases`: cada etiqueta contiene `count`, `ms` acumulados y `errors` numéricos.

Etiquetas principales: `db.connect`, `db.reuse`, `db.close`, `auth.password_verify`, `student.authentication`, `teacher.authentication`, `student.session`, `teacher.session`, `student.dashboard_load`, `teacher.dashboard_load`, `template.render`.

Cada función SQL tiene etiquetas `.query`, `.fetch`, `.transaction_begin` y `.transaction_end`. `.query` incluye las sentencias SET LOCAL existentes: el conteo permite identificar viajes repetidos. Los tiempos de fases de alto nivel contienen los de sus hijos: no sumar todas las fases como si fueran independientes. Query mide cliente/driver/red/servidor juntos, no es un EXPLAIN de PostgreSQL. No registra SQL, parámetros, resultados, contraseñas, hashes, cookies, nombres, mensajes de excepción ni tokens.

`Server-Timing: app` llega al inicio de respuesta; `http_ms` termina al completar ASGI. No miden el arranque previo a importar la app, TLS entre navegador y Vercel, descarga de recursos ni render del navegador. Eso se compara con el waterfall del navegador. Los logs de acceso de Uvicorn/plataforma son independientes de esta instrumentación; para la prueba local se recomienda `--no-access-log`.

## Pooling y seguridad

Neon ofrece PgBouncer en modo transacción. Para runtime, el usuario debe elegir la cadena pooled (`-pooler` en el host) en la consola, sin pegarla en chats ni logs. No se modifica automáticamente ninguna variable. Ver [pooling de Neon](https://neon.com/docs/connect/connection-pooling).

El pooling de Neon reutiliza conexiones del servidor PostgreSQL; no elimina por sí solo cada conexión cliente, DNS o handshake TLS. La reutilización implementada elimina aperturas dentro de una petición. Se conservan transacciones cortas y SET LOCAL, y se desactiva preparación automática de sentencias en este adaptador para no depender del estado de sesión del pooler.

No se añadió un pool persistente en Python: exigiría gestionar límites por proceso, cierre/reemplazo de conexiones rotas, idle timeouts, escalado y suspensión de instancias, además de una nueva dependencia. Aquí cada operación tiene dueño exclusivo, no cruza hilos, cierra al terminar y no retiene estado para otro usuario. Si las mediciones reales aún muestran conexión dominante, evaluar después un pool oficial limitado y comprobado; [Psycopg documenta el checkout, rollback y comprobación de conexiones](https://www.psycopg.org/psycopg3/docs/advanced/pool.html).

## Regiones recomendadas

Priorizar la función junto a la base existente, antes de elegir por proximidad al navegador. Vercel lo recomienda explícitamente: [configurar región](https://vercel.com/docs/functions/configuring-functions/region). No se consultaron la cuenta de Vercel ni el proyecto Neon del usuario.

| Región del proyecto Neon existente | Región correspondiente en Vercel |
| --- | --- |
| AWS N. Virginia, `aws-us-east-1` | `iad1` |
| AWS Ohio, `aws-us-east-2` | `cle1` |
| AWS Oregon, `aws-us-west-2` | `pdx1` |
| AWS Frankfurt, `aws-eu-central-1` | `fra1` |
| AWS São Paulo, `aws-sa-east-1` | `gru1` |

Fuentes consultadas el 22-11-2026: [regiones Neon](https://neon.com/docs/introduction/regions), [regiones Vercel](https://vercel.com/docs/regions). Ambas ofrecen São Paulo actualmente. Para una instalación NUEVA orientada a Bolivia, São Paulo en ambos servicios es un candidato a medir; no se recomienda mover solo Vercel a São Paulo manteniendo la base en otra región. Si la base actual está en Virginia, empezar con `iad1`. No se cambia ninguna región ni se crea `vercel.json` sin conocer la región real del proyecto.

Neon puede suspender y reactivar compute; una primera conexión puede tardar más. Pooling no demuestra que desaparezca ese coste. [Ciclo de compute](https://neon.com/docs/introduction/compute-lifecycle), [latencia y timeouts](https://neon.com/docs/connect/connection-latency). No se desactivó suspensión ni se añadió tráfico keepalive; hacerlo puede aumentar costes. La ubicación Vercel solo afecta el despliegue: un servidor local en Bolivia sigue conectándose desde la máquina local.

## Validación y reproducción offline

```powershell
Set-Location 'C:\Users\HP\Proyectos\lazylearnai'
uv run --offline --no-env-file python -m unittest discover -s tests -v
uv run --offline --no-env-file python -m scripts.benchmark_login_offline
uv run --offline --no-env-file ruff check .
uv run --offline --no-env-file ruff format --check .
git diff --check
```

30 pruebas pasan: los 17 casos anteriores y 13 nuevos (número de conexiones/consultas, rol revocado, contraseña incorrecta, sesión inválida/caducada, factories dict/tuple, cierre/rollback, aislamiento entre hilos/peticiones, logs sin secretos, cabeceras, fallos de dashboard y resultados de clases). No se ejecutó SQL contra una BD real. Ruff y diff check pasan. Sigue el aviso de deprecación de TestClient/httpx existente; no se cambian dependencias por ello.

## Cómo localizar los 20 segundos reales

Los siguientes pasos son para ejecución manual del usuario, con su entorno ya autorizado. No fueron ejecutados por Codex. Esta intervención no necesita una nueva migración; sigue aplicando el requisito previo de 007 del trabajo anterior.

```powershell
Set-Location 'C:\Users\HP\Proyectos\lazylearnai'
$env:STUDENT_ALLOW_LOCAL_HTTP = '1'
uv run --env-file .env uvicorn backend.main:app --host 127.0.0.1 --port 8000 --log-level info --no-access-log
```

1. Abrir herramientas del navegador, Network, Preserve log. No exportar HAR: puede contener contraseñas y cookies.
2. Iniciar sesión manualmente. Anotar solo duración de POST access, GET dashboard, Server-Timing y X-Performance-Id. No copiar payloads, cookies ni URL de conexión.
3. Comparar los IDs con las líneas `login_performance`. Separar primera petición después de inactividad de las siguientes cinco; no mezclar cold y warm en una única mediana.
4. `db.connect` dominante: revisar endpoint pooled, red, DNS/TLS, suspensión y coincidencia de regiones. El límite de 5 s es un timeout por conexión, no una espera deliberada: no concluir automáticamente que cuatro conexiones explican exactamente 20 s.
5. `.query` dominante: identificar la función por su etiqueta. La búsqueda por nombre normalizado y los joins pueden requerir EXPLAIN/índices si hay volumen; no se crean índices ni se consulta Neon desde esta tarea.
6. `auth.password_verify` dominante: medir CPU/carga de la instancia. No reducir iteraciones como atajo.
7. `template.render` alto: investigar carga/render del servidor. Waterfall alto con `http_ms` bajo: mirar arranque previo a ASGI, red, proxy y recursos del navegador.
8. Para un antes/después REAL, comparar una versión base y esta versión en el mismo entorno de desarrollo, región, datos y condiciones de inactividad. No usar la tabla offline como resultado de producción. No se declara resuelta la demora de 20 s hasta disponer de esas muestras.
