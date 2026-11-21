"""Preparar UN usuario nuevo de demostración y datos de tareas en Neon.

Siempre opt-in. No altera contraseñas de usuarios existentes. Para desarrollo
compartido, crear primero una rama de base de datos en Neon.
"""

import argparse
import getpass
import hashlib
import hmac
import os
import re
import secrets
from pathlib import Path
from uuid import uuid4

import psycopg

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = [
    "001_student_access.sql",
    "002_student_dashboard.sql",
    "003_student_task_chat.sql",
    "004_neon_student_user_link.sql",
]


def make_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    iterations = 600_000
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${hashed.hex()}"


def validate_config() -> tuple[str, bytes]:
    url = os.environ.get("DATABASE_URL_DIRECT", "")
    key = os.environ.get("STUDENT_ID_HMAC_KEY", "").encode("utf-8")
    if not url or len(key) < 32:
        raise SystemExit("Faltan DATABASE_URL_DIRECT o STUDENT_ID_HMAC_KEY de 32+ bytes")
    return url, key


def inspect(url: str) -> None:
    with psycopg.connect(
        url, connect_timeout=10, options="-c default_transaction_read_only=on"
    ) as db:
        rows = db.execute(
            """SELECT u.name, r.nombre FROM public.usuario AS u
               JOIN public.user_rol AS ur ON ur.user_id = u.id
               JOIN public.rol AS r ON r.id = ur.rol_id
               ORDER BY u.id LIMIT 30"""
        ).fetchall()
        print("Usuarios y roles (sin contraseñas):")
        for name, role in rows:
            print(f"  {name!s} — {role!s}")
        print("Tablas auxiliares:")
        for name in (
            "student_demo_profiles",
            "student_demo_sessions",
            "student_demo_subjects",
            "student_demo_tasks",
            "student_task_conversations",
        ):
            exists = db.execute(
                "SELECT to_regclass(%s) IS NOT NULL", (f"public.{name}",)
            ).fetchone()[0]
            print(f"  {name}: {'presente' if exists else 'pendiente'}")


def apply_schema(db: psycopg.Connection) -> None:
    for migration in MIGRATIONS:
        path = ROOT / "migrations" / migration
        if not path.is_file():
            raise RuntimeError(f"No se encontró {path}")
        db.execute(path.read_text(encoding="utf-8"))
        print(f"Migración aplicada: {migration}")


def create_demo_account(db: psycopg.Connection, name: str, password: str) -> int:
    existing = db.execute(
        """SELECT id FROM public.usuario
           WHERE lower(regexp_replace(btrim(name), '[[:space:]]+', ' ', 'g')) = lower(%s)
           LIMIT 1""",
        (name,),
    ).fetchone()
    if existing:
        raise RuntimeError(
            "Ese nombre ya existe. Se conservó la cuenta original. Elige otro nombre."
        )
    role = db.execute(
        "SELECT id FROM public.rol WHERE lower(btrim(nombre)) = 'estudiante' ORDER BY id LIMIT 2"
    ).fetchall()
    if len(role) != 1:
        raise RuntimeError("Se esperaba exactamente un rol Estudiante existente en la tabla rol")
    with db.transaction():
        new_user_id = db.execute(
            "INSERT INTO public.usuario (name, password) VALUES (%s, %s) RETURNING id",
            (name, make_password_hash(password)),
        ).fetchone()[0]
        db.execute(
            "INSERT INTO public.user_rol (user_id, rol_id) VALUES (%s, %s)",
            (new_user_id, role[0][0]),
        )
    return new_user_id


def link_and_seed(db: psycopg.Connection, user_id: int, name: str, key: bytes) -> None:
    identity_hmac = hmac.new(
        key, f"neon-user:{user_id}".encode("ascii"), hashlib.sha256
    ).hexdigest()
    with db.transaction():
        profile_id = db.execute(
            """INSERT INTO public.student_demo_profiles
                  (id, display_name, identity_hmac, neon_user_id)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (neon_user_id) DO UPDATE SET display_name = EXCLUDED.display_name
               RETURNING id""",
            (uuid4(), name, identity_hmac, user_id),
        ).fetchone()[0]
    demo_sql = (ROOT / "migrations" / "demo_student_dashboard.sql").read_text(encoding="utf-8")
    if not re.fullmatch(r"[0-9a-f-]{36}", str(profile_id)):
        raise RuntimeError("UUID de perfil inesperado")
    # El SQL de demostración ya usa :'<profile_id>' de psql; solo se sustituye un UUID
    # generado por PostgreSQL/Python, nunca texto procedente de entrada del usuario.
    demo_sql = demo_sql.replace(":'profile_id'", f"'{profile_id}'")
    db.execute(demo_sql)
    print("Materias y seis tareas ficticias asignadas al nuevo perfil")


def main() -> None:
    parser = argparse.ArgumentParser(description="Integración de usuarios Neon con LazyLearnAI")
    parser.add_argument("--apply", action="store_true", help="Permitir escrituras explícitas")
    parser.add_argument("--name", default="Alex Prueba", help="Nombre de la cuenta nueva de prueba")
    args = parser.parse_args()
    url, key = validate_config()
    if not args.apply:
        inspect(url)
        print("\nModo solo lectura. Para preparar demo: --apply")
        return

    name = " ".join(args.name.split())
    if not 2 <= len(name) <= 80:
        raise SystemExit("Nombre de prueba inválido")
    print("ATENCIÓN: se añadirán tablas auxiliares y UNA cuenta de prueba a esta base Neon.")
    print("No se editarán contraseñas de las cuentas existentes.")
    print("Usa preferentemente una rama de Neon creada para desarrollo.")
    confirmation = input("Escribe CREAR DEMO para continuar: ").strip()
    if confirmation != "CREAR DEMO":
        raise SystemExit("Cancelado. No se modificó nada.")
    password = getpass.getpass("Elige contraseña para la cuenta de prueba: ")
    if len(password) < 12 or len(password) > 128:
        raise SystemExit("La contraseña de prueba debe tener 12 a 128 caracteres")
    if getpass.getpass("Repite la contraseña: ") != password:
        raise SystemExit("Las contraseñas no coinciden")

    with psycopg.connect(url, connect_timeout=10, autocommit=True) as db:
        apply_schema(db)
        user_id = create_demo_account(db, name, password)
        link_and_seed(db, user_id, name, key)
        print("\nLISTO: cuenta nueva creada para iniciar sesión")
        print("Nombre:", name)
        print("Contraseña: la que elegiste (no se mostrará)")
        print("No se modificaron las contraseñas de los usuarios existentes")


if __name__ == "__main__":
    main()
