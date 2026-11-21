# 03 · Contrato de backend y PostgreSQL/Neon (demo)

## Aclaración de seguridad obligatoria

Nombre + Carnet de identidad **NO es login seguro** y no debe usarse para verificar identidad de personas reales; permite suplantaciones. Solo implementar un **acceso de demostración** con identidades sintéticas y BD de prueba. En producción escolar se exige un sistema de autenticación verdadero y controles de privacidad para menores.

## HTTP propuesto

| Método y ruta | Resultado esperado |
| --- | --- |
| `GET /` | Página de acceso Jinja2; 200 incluso si DATABASE_URL no existe |
| `POST /student/access` | Valida nombre + documento, persiste identidad de prueba y sesión, redirige 303 |
| `GET /student/access/confirmed` | Confirmación mínima de sesión demostrativa; no inventar dashboard |
| `GET /health` | Sigue siendo 200, sin depender de base de datos |
| `GET /health/db` | Estado de Neon según configuración existente |
| `GET /demo` y `/preview` | Preservar la demostración anterior si sigue siendo posible |

Los nombres de las rutas son una propuesta concreta para coordinar el trabajo. Si el repositorio ya tiene otros contratos aprobados por el equipo, respetarlos y actualizar esta documentación.

## Entradas

`name` es cadena obligatoria con espacios normalizados, 2–80 caracteres. `identity_number` debe tratarse como **cadena**, no entero; para demo usar una validación simple y consistente de 5–12 dígitos luego de retirar separadores aceptados, explicando sus límites. No afirmar validación de un documento oficial ni usar datos reales. Ambos viajan en cuerpo POST, nunca query params.

## Esquema mínimo sugerido

La migración manual debe ser `migrations/001_student_access.sql`, idempotente para CREATE TABLE/INDEX, sin DROP. Generar UUID desde Python (`uuid.uuid4`) para evitar extensiones adicionales. El código debe usar tipos y nombres coherentes con el esquema final.

```sql
CREATE TABLE IF NOT EXISTS student_demo_profiles (
  id UUID PRIMARY KEY,
  display_name VARCHAR(80) NOT NULL,
  identity_hmac CHAR(64) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_demo_sessions (
  id UUID PRIMARY KEY,
  profile_id UUID NOT NULL REFERENCES student_demo_profiles(id),
  token_hash CHAR(64) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_student_demo_sessions_expiry
  ON student_demo_sessions(expires_at);
```

No almacenar documento en texto claro, contraseña, contraseñas derivadas del carnet ni respuestas completas del formulario. El `identity_hmac` se calcula con `hmac.new(secret, normalized_id.encode(), hashlib.sha256).hexdigest()`. El secreto `STUDENT_ID_HMAC_KEY` se configura solo en servidor; debe tener entropía suficiente. No usar SHA256 simple del carnet, ya que ese espacio de valores es pequeño.

**Si se repite el mismo documento ficticio**, buscar por HMAC y reutilizar el perfil sin duplicar; si nombre no coincide, responder con error genérico y no revelar si el documento ya existe.

**Sesión:** generar un token aleatorio (`secrets.token_urlsafe(32)`), guardar `sha256(token)` en tabla y el token sin hash exclusivamente en cookie `HttpOnly`, `SameSite=Lax`, `Secure` en HTTPS, caducidad corta (ej. 8 h) y `Path=/`. No revelar el token en HTML/logs.

## Separación recomendada

- `routes.py`: entrada HTTP, errores, formulario, cookies, redirect.
- `service.py`: normalización/validación, HMAC, creación de token, reglas.
- `repository.py`: conexiones `psycopg`, SQL parametrizado, buscar/crear perfil y sesión.
- `backend/core/config.py`: lectura de `DATABASE_URL` y `STUDENT_ID_HMAC_KEY` desde variables de entorno.

No abrir conexión a Neon durante el render de GET si no es necesario, no ejecutar migraciones al arrancar o desplegar, ni exponer errores de SQL al navegador. Usar HTTPS en el servidor público; en desarrollo HTTP local se admite cookie sin `Secure`, configurada explícitamente para el entorno.

## Configuración manual

1. Crear proyecto PostgreSQL/Neon **de prueba** y copiar cadena pooled a `DATABASE_URL` en `.env` local, excluido por `.gitignore`.
2. Generar `STUDENT_ID_HMAC_KEY` aleatoria; registrar solo en `.env` y Vercel Environment Variables, nunca en README.
3. Aplicar manualmente `migrations/001_student_access.sql` con cliente PostgreSQL; sin ejecución automática.
4. Comprobar `/health/db` y luego enviar formulario con **datos ficticios**.

Si Neon no está disponible, permitir revisar el HTML/CSS y mostrar un error de servicio controlado al intentar registrar la demo; no inventar una persistencia silenciosa en memoria.
