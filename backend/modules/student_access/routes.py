"""HTTP del acceso. Formulario URL-encoded estándar sin dependencia multipart."""

from urllib.parse import parse_qs

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.modules.student_access import service
from backend.modules.student_access.http import (
    COOKIE_NAME,
    PRIVATE_HEADERS,
    request_is_same_origin,
    secure_cookie,
)

router = APIRouter(tags=["Acceso de demostración"])


def login_page(
    request: Request,
    status_code: int = 200,
    errors: dict[str, str] | None = None,
    message: str | None = None,
) -> HTMLResponse:
    # No volver a incluir nombre, carnet, HMAC ni token en el HTML.
    return request.app.state.templates.TemplateResponse(
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
    # Evitar envíos de formularios desde otro sitio (incluidos ataques de login CSRF).
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
        if set(fields) - {"name", "identity_number"} or any(len(v) != 1 for v in fields.values()):
            raise ValueError()
    except (ValueError, UnicodeError):
        return login_page(
            request, 400, message="No se pudo leer el formulario. Inténtalo otra vez."
        )
    try:
        token = await run_in_threadpool(
            service.create_access,
            fields.get("name", [""])[0],
            fields.get("identity_number", [""])[0],
            request.cookies.get(COOKIE_NAME),
        )
    except service.InvalidFields as exc:
        return login_page(request, 422, errors=exc.errors)
    except service.AccessRejected:
        return login_page(
            request, 400, message="No se pudo completar el acceso con esos datos ficticios."
        )
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
