"""HTTP de acceso a partir de las cuentas ya existentes en public.usuario."""

import os
from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.core.timing import render_template
from backend.modules.student_access import service
from backend.modules.student_access.http import (
    COOKIE_NAME,
    PRIVATE_HEADERS,
    request_is_same_origin,
    secure_cookie,
)

router = APIRouter(tags=["Acceso de estudiante"])


def login_page(
    request: Request,
    status_code: int = 200,
    errors: dict[str, str] | None = None,
    message: str | None = None,
) -> HTMLResponse:
    return render_template(
        request.app.state.templates,
        request=request,
        name="pages/student_login.html",
        context={"title": "Acceso de estudiante", "errors": errors or {}, "message": message},
        status_code=status_code,
        headers=PRIVATE_HEADERS,
    )


@router.get("/", response_class=HTMLResponse)
def student_login(request: Request) -> HTMLResponse:
    return login_page(request)


@router.post("/student/access", response_class=HTMLResponse)
async def student_access(request: Request) -> Response:
    if not request_is_same_origin(request):
        return login_page(
            request, 403, message="Abre el formulario desde este sitio e inténtalo otra vez."
        )
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != (
        "application/x-www-form-urlencoded"
    ):
        return login_page(request, 415, message="Envía los datos desde el formulario de acceso.")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            return login_page(request, 413, message="El formulario supera el tamaño permitido.")
    try:
        fields = parse_qs(
            body.decode("utf-8"), keep_blank_values=True, max_num_fields=2, errors="strict"
        )
        if set(fields) - {"name", "password"} or any(len(v) != 1 for v in fields.values()):
            raise ValueError()
    except (ValueError, UnicodeError):
        return login_page(
            request, 400, message="No se pudo leer el formulario. Inténtalo otra vez."
        )

    # SOLO demo local: modo heredado deshabilitado por defecto, nunca en Vercel/HTTPS.
    local_dev = (
        not secure_cookie(request) and os.environ.get("STUDENT_ALLOW_LEGACY_PLAINTEXT") == "1"
    )
    try:
        token = await run_in_threadpool(
            service.create_access,
            fields.get("name", [""])[0],
            fields.get("password", [""])[0],
            request.cookies.get(COOKIE_NAME),
            allow_legacy_plaintext=local_dev,
        )
    except service.InvalidFields as exc:
        return login_page(request, 422, errors=exc.errors)
    except service.AccessRejected:
        return login_page(request, 400, message="Usuario o contraseña incorrectos.")
    except service.AccessUnavailable:
        return login_page(request, 503, message=service.UNAVAILABLE)

    response = RedirectResponse("/student/dashboard", status_code=303, headers=PRIVATE_HEADERS)
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=service.SESSION_SECONDS,
        httponly=True,
        secure=secure_cookie(request),
        samesite="lax",
        path="/",
    )
    return response


@router.get("/student/access/confirmed", response_class=HTMLResponse)
def student_confirmed(request: Request) -> Response:
    try:
        valid = service.has_session(request.cookies.get(COOKIE_NAME))
    except service.AccessUnavailable:
        return login_page(request, 503, message=service.UNAVAILABLE)
    if not valid:
        response = RedirectResponse("/", status_code=303, headers=PRIVATE_HEADERS)
        response.delete_cookie(
            COOKIE_NAME, path="/", secure=secure_cookie(request), httponly=True, samesite="lax"
        )
        return response
    return RedirectResponse("/student/dashboard", status_code=303, headers=PRIVATE_HEADERS)
