"""SQL de la demo. Cada acceso crea perfil y sesión en una sola transacción."""

from datetime import datetime
from uuid import UUID, uuid4

import psycopg


class ProfileMismatch(Exception):
    """El nombre no coincide. No transportar datos del perfil en el error."""


def save_access(
    url: str,
    display_name: str,
    identity_hmac: str,
    token_hash: str,
    expires_at: datetime,
    previous_token_hash: str | None,
) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """INSERT INTO student_demo_profiles (id, display_name, identity_hmac)
                   VALUES (%s, %s, %s) ON CONFLICT (identity_hmac) DO NOTHING""",
            (uuid4(), display_name, identity_hmac),
        )
        cursor.execute(
            "SELECT id, display_name FROM student_demo_profiles WHERE identity_hmac = %s",
            (identity_hmac,),
        )
        profile = cursor.fetchone()
        if profile is None or profile[1].casefold() != display_name.casefold():
            raise ProfileMismatch()
        cursor.execute(
            """INSERT INTO student_demo_sessions (id, profile_id, token_hash, expires_at)
                   VALUES (%s, %s, %s, %s)""",
            (uuid4(), profile[0], token_hash, expires_at),
        )
        if previous_token_hash:
            cursor.execute(
                "DELETE FROM student_demo_sessions WHERE token_hash = %s",
                (previous_token_hash,),
            )


def session_exists(url: str, token_hash: str) -> bool:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT 1 FROM student_demo_sessions
                   WHERE token_hash = %s AND expires_at > now()""",
            (token_hash,),
        )
        return cursor.fetchone() is not None


def session_profile(url: str, token_hash: str) -> tuple[UUID, str] | None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT profile.id, profile.display_name
               FROM student_demo_sessions AS session
               JOIN student_demo_profiles AS profile ON profile.id = session.profile_id
               WHERE session.token_hash = %s AND session.expires_at > now()""",
            (token_hash,),
        )
        return cursor.fetchone()


def revoke_session(url: str, token_hash: str) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute("DELETE FROM student_demo_sessions WHERE token_hash = %s", (token_hash,))
