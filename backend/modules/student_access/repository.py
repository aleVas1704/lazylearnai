"""Autenticacion de usuarios oficiales y sesiones tecnicas LazyLearnAI."""

from datetime import datetime
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row


class AccountRevoked(Exception):
    """La cuenta dejo de tener el rol Estudiante."""


_STUDENT_ROLE = """EXISTS (
    SELECT 1 FROM public.user_rol AS user_role
    JOIN public.rol AS role ON role.id = user_role.rol_id
    WHERE user_role.user_id = usr.id AND lower(btrim(role.nombre)) = 'estudiante'
)"""


def lookup_student_account(url: str, name: str) -> dict[str, object] | None:
    """Buscar exactamente una cuenta con rol Estudiante."""
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            f"""SELECT usr.id, usr.name, usr.password
                FROM public.usuario AS usr
                WHERE lower(regexp_replace(btrim(usr.name), '[[:space:]]+', ' ', 'g'))
                      = lower(%s)
                  AND {_STUDENT_ROLE}
                ORDER BY usr.id
                LIMIT 2""",
            (name,),
        )
        records = cursor.fetchall()
    return records[0] if len(records) == 1 else None


def save_access_for_neon_user(
    *,
    url: str,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    previous_token_hash: str | None,
) -> None:
    """Crear cookie de sesion ligada directamente a usuario.id oficial."""
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            f"""SELECT usr.id FROM public.usuario AS usr
                WHERE usr.id = %s AND {_STUDENT_ROLE}
                FOR SHARE OF usr""",
            (user_id,),
        )
        if cursor.fetchone() is None:
            raise AccountRevoked()
        cursor.execute(
            """INSERT INTO public.ll_student_sessions
                   (id, user_id, token_hash, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (uuid4(), user_id, token_hash, expires_at),
        )
        if previous_token_hash:
            cursor.execute(
                "DELETE FROM public.ll_student_sessions WHERE token_hash = %s",
                (previous_token_hash,),
            )


def session_profile(url: str, token_hash: str) -> tuple[int, str] | None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            f"""SELECT usr.id, usr.name
                FROM public.ll_student_sessions AS sess
                JOIN public.usuario AS usr ON usr.id = sess.user_id
                WHERE sess.token_hash = %s AND sess.expires_at > now()
                  AND {_STUDENT_ROLE}""",
            (token_hash,),
        )
        return cursor.fetchone()


def revoke_session(url: str, token_hash: str) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            "DELETE FROM public.ll_student_sessions WHERE token_hash = %s",
            (token_hash,),
        )
