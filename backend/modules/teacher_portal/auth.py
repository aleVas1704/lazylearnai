"""Sesiones independientes del docente, basadas en usuario/rol oficiales."""

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from backend.core.config import database_url
from backend.core.database import connect
from backend.core.timing import timed
from backend.modules.student_access.service import hash_session, normalize_fields, verify_password

COOKIE_NAME = "ll_teacher_session"
SESSION_SECONDS = 8 * 60 * 60


@dataclass(frozen=True)
class TeacherSession:
    user_id: int
    display_name: str


_ROLE_SQL = """EXISTS (
    SELECT 1 FROM public.user_rol AS ur JOIN public.rol AS r ON r.id = ur.rol_id
    WHERE ur.user_id = usr.id AND lower(btrim(r.nombre)) = 'docente'
)"""


def _url() -> str:
    url = database_url()
    if not url:
        raise psycopg.OperationalError("DATABASE_URL no configurada")
    return url


@timed("teacher.authentication")
def sign_in(name: str, password: str, previous_token: str | None) -> str | None:
    name, password = normalize_fields(name, password)
    with (
        connect(
            _url(), label="teacher.auth.sign_in", connect_timeout=5, row_factory=dict_row
        ) as db,
        db.cursor() as cur,
    ):
        cur.execute(
            f"""SELECT usr.id, usr.password FROM public.usuario AS usr
               WHERE lower(regexp_replace(btrim(usr.name), '[[:space:]]+', ' ', 'g'))
                     = lower(%s) AND {_ROLE_SQL}
               ORDER BY usr.id LIMIT 2""",
            (name,),
        )
        matches = cur.fetchall()
        if len(matches) != 1 or not verify_password(
            password, matches[0]["password"], allow_legacy_plaintext=False
        ):
            return None
        token = secrets.token_urlsafe(32)
        cur.execute(
            """INSERT INTO public.ll_teacher_sessions (id, user_id, token_hash, expires_at)
               VALUES (%s, %s, %s, %s)""",
            (
                uuid4(),
                matches[0]["id"],
                hashlib.sha256(token.encode()).hexdigest(),
                datetime.now(UTC) + timedelta(seconds=SESSION_SECONDS),
            ),
        )
        old = hash_session(previous_token)
        if old:
            cur.execute("DELETE FROM public.ll_teacher_sessions WHERE token_hash = %s", (old,))
        return token


@timed("teacher.session")
def get_session(token: str | None) -> TeacherSession | None:
    hashed = hash_session(token)
    if not hashed:
        return None
    with connect(_url(), label="teacher.auth.get_session", connect_timeout=5) as db:
        result = db.execute(
            f"""SELECT usr.id, usr.name FROM public.ll_teacher_sessions AS s
               JOIN public.usuario AS usr ON usr.id = s.user_id
               WHERE s.token_hash = %s AND s.expires_at > now() AND {_ROLE_SQL}""",
            (hashed,),
        ).fetchone()
        return TeacherSession(*result) if result else None


def sign_out(token: str | None) -> None:
    hashed = hash_session(token)
    if hashed:
        with connect(_url(), label="teacher.auth.sign_out", connect_timeout=5) as db:
            db.execute("DELETE FROM public.ll_teacher_sessions WHERE token_hash = %s", (hashed,))
