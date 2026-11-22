"""Política HTTP compartida por las pantallas protegidas del estudiante."""

from urllib.parse import urlsplit

from fastapi import Request

from backend.core.config import student_local_http_enabled

COOKIE_NAME = "ll_student_session"
PRIVATE_HEADERS = {"Cache-Control": "no-store", "Referrer-Policy": "same-origin"}


def secure_cookie(request: Request) -> bool:
    local_http = (
        student_local_http_enabled()
        and request.url.hostname in {"localhost", "127.0.0.1", "::1"}
        and request.url.scheme == "http"
    )
    return not local_http


def request_is_same_origin(request: Request) -> bool:
    """Validar formularios POST sin depender de JavaScript ni de un campo oculto."""
    expected = str(request.base_url).rstrip("/")
    origin = request.headers.get("origin")
    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site == "cross-site":
        return False
    if origin:
        # El navegador integrado usa Origin:null junto con Sec-Fetch-Site:same-origin.
        return origin == expected or (origin == "null" and fetch_site == "same-origin")
    referer = request.headers.get("referer")
    if not referer:
        return fetch_site == "same-origin"
    try:
        parsed = urlsplit(referer)
    except ValueError:
        return False
    return f"{parsed.scheme}://{parsed.netloc}" == expected
