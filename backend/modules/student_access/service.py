"""Acceso estudiante usando usuarios/roles existentes en Neon.

No registra credenciales duplicadas. Las sesiones usan ll_student_sessions,
sin tablas student_demo_* ni identificadores de perfil UUID.
"""

import hashlib
import hmac
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import psycopg

from backend.core.config import database_url
from backend.modules.student_access import repository

SESSION_SECONDS = 8 * 60 * 60
UNAVAILABLE = "El acceso no está disponible en este momento. Inténtalo más tarde."


class InvalidFields(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors


class AccessUnavailable(Exception):
    pass


class AccessRejected(Exception):
    pass


@dataclass(frozen=True)
class StudentSession:
    user_id: int
    display_name: str


def normalize_fields(name: str, password: str) -> tuple[str, str]:
    name = " ".join(unicodedata.normalize("NFC", name).split())
    errors: dict[str, str] = {}
    if not 2 <= len(name) <= 80 or any(unicodedata.category(c).startswith("C") for c in name):
        errors["name"] = "Escribe tu nombre de usuario (entre 2 y 80 caracteres)."
    if not password or len(password) > 256:
        errors["password"] = "Introduce tu contraseña."
    if errors:
        raise InvalidFields(errors)
    return name, password


def hash_session(token: str | None) -> str | None:
    if not token or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def verify_password(password: str, stored: str, *, allow_legacy_plaintext: bool) -> bool:
    """Verifica PBKDF2 (cuentas nuevas) o, SOLO local, credenciales heredadas.

    No se debe habilitar el modo heredado en entornos públicos. No determina si
    contraseñas de 8 caracteres son realmente texto plano: eso debe confirmarse.
    """
    if stored.startswith("pbkdf2_sha256$"):
        try:
            algorithm, iterations_text, salt_hex, digest_hex = stored.split("$", 3)
            iterations = int(iterations_text)
            if algorithm != "pbkdf2_sha256" or not 200_000 <= iterations <= 1_200_000:
                return False
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
            if len(salt) < 16 or len(expected) != 32:
                return False
            given = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(given, expected)

    # Únicamente para pruebas HTTP loopback si el equipo confirmó texto plano.
    # Nunca activa para hashes desconocidos ni otros formatos explícitos.
    if allow_legacy_plaintext and len(stored) == 8:
        return hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8"))
    return False


def create_access(
    name: str,
    password: str,
    previous_token: str | None,
    *,
    allow_legacy_plaintext: bool = False,
) -> str:
    name, password = normalize_fields(name, password)
    url = database_url()
    if not url:
        raise AccessUnavailable()
    try:
        account = repository.lookup_student_account(url, name)
    except psycopg.Error:
        raise AccessUnavailable() from None
    if account is None or not verify_password(
        password, account["password"], allow_legacy_plaintext=allow_legacy_plaintext
    ):
        raise AccessRejected()

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    try:
        repository.save_access_for_neon_user(
            url=url,
            user_id=account["id"],
            token_hash=token_hash,
            expires_at=datetime.now(UTC) + timedelta(seconds=SESSION_SECONDS),
            previous_token_hash=hash_session(previous_token),
        )
    except repository.AccountRevoked:
        raise AccessRejected() from None
    except psycopg.Error:
        raise AccessUnavailable() from None
    return token


def has_session(token: str | None) -> bool:
    token_hash = hash_session(token)
    if token_hash is None:
        return False
    url = database_url()
    if not url:
        raise AccessUnavailable()
    try:
        return repository.session_profile(url, token_hash) is not None
    except psycopg.Error:
        raise AccessUnavailable() from None


def get_session(token: str | None) -> StudentSession | None:
    token_hash = hash_session(token)
    if token_hash is None:
        return None
    url = database_url()
    if not url:
        raise AccessUnavailable()
    try:
        profile = repository.session_profile(url, token_hash)
    except psycopg.Error:
        raise AccessUnavailable() from None
    return StudentSession(*profile) if profile else None


def revoke_session(token: str | None) -> None:
    token_hash = hash_session(token)
    url = database_url()
    if token_hash is None or not url:
        return
    try:
        repository.revoke_session(url, token_hash)
    except psycopg.Error:
        raise AccessUnavailable() from None
