"""Validación y sesión de demo: nombre + carnet NO es autenticación segura."""

import hashlib
import hmac
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg

from backend.core.config import database_url, student_id_hmac_key
from backend.modules.student_access import repository

SESSION_SECONDS = 8 * 60 * 60
UNAVAILABLE = "El acceso de demostración no está disponible. Inténtalo más tarde."


class InvalidFields(Exception):
    def __init__(self, errors: dict[str, str]):
        self.errors = errors


class AccessUnavailable(Exception):
    pass


class AccessRejected(Exception):
    pass


@dataclass(frozen=True)
class StudentSession:
    profile_id: UUID
    display_name: str


def normalize_fields(name: str, identity_number: str) -> tuple[str, str]:
    name = " ".join(unicodedata.normalize("NFC", name).split())
    # Únicos separadores permitidos: espacio ASCII y guion ASCII. Conservar ceros.
    identity_number = identity_number.replace(" ", "").replace("-", "")
    errors = {}
    if not 2 <= len(name) <= 80 or any(unicodedata.category(c).startswith("C") for c in name):
        errors["name"] = "Escribe un nombre de entre 2 y 80 caracteres."
    if not re.fullmatch(r"[0-9]{5,12}", identity_number):
        errors["identity_number"] = "Usa un identificador ficticio de 5 a 12 dígitos."
    if errors:
        raise InvalidFields(errors)
    return name, identity_number


def hash_session(token: str | None) -> str | None:
    if not token or not re.fullmatch(r"[A-Za-z0-9_-]{43}", token):
        return None
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def create_access(name: str, identity_number: str, previous_token: str | None) -> str:
    name, identity_number = normalize_fields(name, identity_number)
    url, key = database_url(), student_id_hmac_key()
    if not url or not key:
        raise AccessUnavailable()
    identity_hmac = hmac.new(key, identity_number.encode("ascii"), hashlib.sha256).hexdigest()
    token = secrets.token_urlsafe(32)
    try:
        repository.save_access(
            url,
            name,
            identity_hmac,
            hashlib.sha256(token.encode("ascii")).hexdigest(),
            datetime.now(UTC) + timedelta(seconds=SESSION_SECONDS),
            hash_session(previous_token),
        )
    except repository.ProfileMismatch:
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
        return repository.session_exists(url, token_hash)
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
