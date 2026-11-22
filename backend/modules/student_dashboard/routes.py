"""HTTP del panel protegido y logout."""

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.core.timing import render_template
from backend.modules.student_access import service as access_service
from backend.modules.student_access.http import (
    COOKIE_NAME,
    PRIVATE_HEADERS,
    request_is_same_origin,
    secure_cookie,
)
from backend.modules.student_dashboard import service

router = APIRouter(tags=["Panel de estudiante"])


async def current_session(request: Request) -> access_service.StudentSession | None:
    return await run_in_threadpool(access_service.get_session, request.cookies.get(COOKIE_NAME))


def login_redirect() -> RedirectResponse:
    return RedirectResponse("/", status_code=303, headers=PRIVATE_HEADERS)


@router.get("/student/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    subject: str | None = Query(default=None, max_length=64, pattern=r"^[a-z0-9-]+$"),
) -> Response:
    try:
        session, data = await run_in_threadpool(
            service.load_authenticated_dashboard, request.cookies.get(COOKIE_NAME), subject
        )
    except access_service.AccessUnavailable:
        return Response(
            "El panel no está disponible. Inténtalo más tarde.",
            status_code=503,
            headers=PRIVATE_HEADERS,
        )
    if session is None:
        return login_redirect()
    if data is None:
        return render_template(
            request.app.state.templates,
            request=request,
            name="pages/student_dashboard.html",
            context={
                "title": "Panel del estudiante",
                "student_name": session.display_name,
                "subjects": [],
                "selected_subject": None,
                "tasks": [],
                "service_unavailable": True,
            },
            status_code=503,
            headers=PRIVATE_HEADERS,
        )
    return render_template(
        request.app.state.templates,
        request=request,
        name="pages/student_dashboard.html",
        context={
            "title": "Panel del estudiante",
            "student_name": session.display_name,
            "subjects": data.subjects,
            "selected_subject": data.selected_subject,
            "tasks": data.tasks,
            "service_unavailable": False,
        },
        headers=PRIVATE_HEADERS,
    )


@router.post("/student/logout")
async def logout(request: Request) -> Response:
    if not request_is_same_origin(request):
        return Response(status_code=403, headers=PRIVATE_HEADERS)
    try:
        await run_in_threadpool(access_service.revoke_session, request.cookies.get(COOKIE_NAME))
    except access_service.AccessUnavailable:
        return Response(
            "No se pudo cerrar la sesión en el servidor. Inténtalo otra vez.",
            status_code=503,
            headers=PRIVATE_HEADERS,
        )
    response = login_redirect()
    response.delete_cookie(
        COOKIE_NAME, path="/", secure=secure_cookie(request), httponly=True, samesite="lax"
    )
    return response
