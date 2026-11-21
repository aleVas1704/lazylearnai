"""Rutas protegidas del espacio de trabajo y su conversación."""

from urllib.parse import parse_qs
from uuid import UUID, uuid4

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.modules.student_access import service as access_service
from backend.modules.student_access.http import COOKIE_NAME, PRIVATE_HEADERS, request_is_same_origin
from backend.modules.student_task_chat import service

router = APIRouter(tags=["Tutor de tareas"])


async def _session(request: Request) -> access_service.StudentSession | None:
    return await run_in_threadpool(access_service.get_session, request.cookies.get(COOKIE_NAME))


def _login_redirect() -> RedirectResponse:
    return RedirectResponse("/", status_code=303, headers=PRIVATE_HEADERS)


async def _workspace_page(
    request: Request,
    user_id: int,
    task_id: int,
    *,
    status_code: int = 200,
    error: str | None = None,
    draft: str = "",
    request_id: UUID | None = None,
) -> Response:
    try:
        workspace = await run_in_threadpool(service.load_workspace, user_id, task_id)
    except service.TaskNotFound:
        return Response("Tarea no disponible.", status_code=404, headers=PRIVATE_HEADERS)
    except service.WorkspaceUnavailable:
        return Response(
            "Las tareas no están disponibles. Inténtalo más tarde.",
            status_code=503,
            headers=PRIVATE_HEADERS,
        )
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="pages/student_task_chat.html",
        context={
            "title": str(workspace.task["title"]),
            "task": workspace.task,
            "conversation": workspace.conversation,
            "messages": workspace.messages,
            "error": error,
            "draft": draft,
            "request_id": request_id or uuid4(),
            "max_message_length": service.MAX_MESSAGE_LENGTH,
        },
        status_code=status_code,
        headers=PRIVATE_HEADERS,
    )


@router.post("/student/tasks/{task_id}/start")
async def start_task(request: Request, task_id: int) -> Response:
    if not request_is_same_origin(request):
        return Response(status_code=403, headers=PRIVATE_HEADERS)
    try:
        session = await _session(request)
    except access_service.AccessUnavailable:
        return Response(
            "Las tareas no están disponibles.", status_code=503, headers=PRIVATE_HEADERS
        )
    if session is None:
        return _login_redirect()
    try:
        await run_in_threadpool(service.start_task, session.user_id, task_id)
    except service.TaskNotFound:
        return Response("Tarea no disponible.", status_code=404, headers=PRIVATE_HEADERS)
    except service.WorkspaceUnavailable:
        return Response(
            "Las tareas no están disponibles.", status_code=503, headers=PRIVATE_HEADERS
        )
    except service.AiUnavailable:
        return await _workspace_page(
            request,
            session.user_id,
            task_id,
            status_code=200,
            error="El tutor no pudo iniciar la explicacion. Comprueba GEMINI_API_KEY y reintenta.",
        )
    return RedirectResponse(f"/student/tasks/{task_id}", status_code=303, headers=PRIVATE_HEADERS)


@router.get("/student/tasks/{task_id}", response_class=HTMLResponse)
async def task_workspace(request: Request, task_id: int) -> Response:
    try:
        session = await _session(request)
    except access_service.AccessUnavailable:
        return Response(
            "Las tareas no están disponibles.", status_code=503, headers=PRIVATE_HEADERS
        )
    if session is None:
        return _login_redirect()
    return await _workspace_page(request, session.user_id, task_id)


@router.post("/student/tasks/{task_id}/messages", response_class=HTMLResponse)
async def send_message(request: Request, task_id: int) -> Response:
    if not request_is_same_origin(request):
        return Response(status_code=403, headers=PRIVATE_HEADERS)
    if request.headers.get("content-type", "").split(";")[0].strip().lower() != (
        "application/x-www-form-urlencoded"
    ):
        return Response("Formulario no válido.", status_code=415, headers=PRIVATE_HEADERS)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 4096:
            return Response(
                "La pregunta supera el tamaño permitido.", status_code=413, headers=PRIVATE_HEADERS
            )
    try:
        fields = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=2)
        if set(fields) != {"message", "request_id"} or any(len(v) != 1 for v in fields.values()):
            raise ValueError()
        message = fields["message"][0]
        request_id = UUID(fields["request_id"][0])
    except (ValueError, UnicodeError):
        return Response("No se pudo leer la pregunta.", status_code=400, headers=PRIVATE_HEADERS)
    try:
        session = await _session(request)
    except access_service.AccessUnavailable:
        return Response(
            "Las tareas no están disponibles.", status_code=503, headers=PRIVATE_HEADERS
        )
    if session is None:
        return _login_redirect()
    try:
        await run_in_threadpool(
            service.ask_question,
            session.user_id,
            task_id,
            request_id,
            message,
        )
    except service.InvalidQuestion:
        return await _workspace_page(
            request,
            session.user_id,
            task_id,
            status_code=422,
            error=f"Escribe una pregunta de hasta {service.MAX_MESSAGE_LENGTH} caracteres.",
            draft=message,
            request_id=request_id,
        )
    except service.RateLimited:
        return await _workspace_page(
            request,
            session.user_id,
            task_id,
            status_code=429,
            error="Has enviado varias preguntas. Espera unos minutos antes de continuar.",
            draft=message,
            request_id=request_id,
        )
    except service.AiUnavailable:
        return await _workspace_page(
            request,
            session.user_id,
            task_id,
            status_code=503,
            error="El tutor no pudo responder ahora. Reintenta para continuar sin duplicar tu pregunta.",
            draft=message,
            request_id=request_id,
        )
    except service.TaskNotFound:
        return Response("Tarea no disponible.", status_code=404, headers=PRIVATE_HEADERS)
    except service.WorkspaceUnavailable:
        return Response(
            "Las tareas no están disponibles.", status_code=503, headers=PRIVATE_HEADERS
        )
    return RedirectResponse(f"/student/tasks/{task_id}", status_code=303, headers=PRIVATE_HEADERS)
