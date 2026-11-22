"""Login docente, panel, generación, publicación y reportes protegidos."""

import json
from urllib.parse import parse_qs

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from google.genai import types
from starlette.concurrency import run_in_threadpool

from backend.core.timing import render_template
from backend.modules.student_access.http import (
    PRIVATE_HEADERS,
    request_is_same_origin,
    secure_cookie,
)
from backend.modules.student_access.service import InvalidFields
from backend.modules.student_task_chat import gemini_client
from backend.modules.teacher_portal import auth, data, generator

router = APIRouter(tags=["Panel docente"])


def _page(request: Request, template: str, context: dict, status: int = 200) -> HTMLResponse:
    return render_template(
        request.app.state.templates,
        request=request,
        name=template,
        context=context,
        status_code=status,
        headers=PRIVATE_HEADERS,
    )


async def _teacher(request: Request) -> auth.TeacherSession | None:
    return await run_in_threadpool(auth.get_session, request.cookies.get(auth.COOKIE_NAME))


async def _json_request(request: Request, max_bytes: int = 4_400_000) -> dict:
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        raise ValueError("Se necesita JSON")
    buf = bytearray()
    async for chunk in request.stream():
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise ValueError("Solicitud demasiado grande")
    value = json.loads(buf)
    if not isinstance(value, dict):
        raise TypeError("Formato inválido")
    return value


def _err(message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status, headers=PRIVATE_HEADERS)


@router.get("/teacher/login", response_class=HTMLResponse)
async def login(request: Request) -> Response:
    return _page(request, "pages/teacher_login.html", {"title": "Acceso docente", "message": None})


@router.post("/teacher/access")
async def access(request: Request) -> Response:
    if not request_is_same_origin(request):
        return Response(status_code=403, headers=PRIVATE_HEADERS)
    if (
        request.headers.get("content-type", "").split(";")[0].strip()
        != "application/x-www-form-urlencoded"
    ):
        return Response(status_code=415, headers=PRIVATE_HEADERS)
    body = await request.body()
    if len(body) > 4096:
        return Response(status_code=413, headers=PRIVATE_HEADERS)
    try:
        fields = parse_qs(body.decode("utf-8"), keep_blank_values=True, max_num_fields=2)
        if set(fields) != {"name", "password"} or any(len(v) != 1 for v in fields.values()):
            raise ValueError()
        token = await run_in_threadpool(
            auth.sign_in,
            fields["name"][0],
            fields["password"][0],
            request.cookies.get(auth.COOKIE_NAME),
        )
    except (ValueError, UnicodeError, InvalidFields):
        return _page(
            request,
            "pages/teacher_login.html",
            {"title": "Acceso docente", "message": "Comprueba nombre y contraseña."},
            422,
        )
    except psycopg.Error:
        return _page(
            request,
            "pages/teacher_login.html",
            {"title": "Acceso docente", "message": "El acceso docente no está disponible."},
            503,
        )
    if not token:
        return _page(
            request,
            "pages/teacher_login.html",
            {"title": "Acceso docente", "message": "Credenciales incorrectas o rol no docente."},
            401,
        )
    response = RedirectResponse("/teacher/dashboard", status_code=303, headers=PRIVATE_HEADERS)
    response.set_cookie(
        auth.COOKIE_NAME,
        token,
        max_age=auth.SESSION_SECONDS,
        httponly=True,
        secure=secure_cookie(request),
        samesite="lax",
        path="/",
    )
    return response


@router.post("/teacher/logout")
async def logout(request: Request) -> Response:
    if not request_is_same_origin(request):
        return Response(status_code=403, headers=PRIVATE_HEADERS)
    try:
        await run_in_threadpool(auth.sign_out, request.cookies.get(auth.COOKIE_NAME))
    except psycopg.Error:
        return Response("No se pudo cerrar sesión", status_code=503, headers=PRIVATE_HEADERS)
    response = RedirectResponse("/teacher/login", status_code=303, headers=PRIVATE_HEADERS)
    response.delete_cookie(auth.COOKIE_NAME, path="/", secure=secure_cookie(request))
    return response


@router.get("/teacher/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    try:
        teacher = await _teacher(request)
        if teacher is None:
            return RedirectResponse("/teacher/login", status_code=303)
        classes, tasks, reports = await run_in_threadpool(data.load_dashboard, teacher.user_id)
    except psycopg.Error:
        return Response("Panel docente no disponible", status_code=503, headers=PRIVATE_HEADERS)
    return _page(
        request,
        "pages/teacher_dashboard.html",
        {
            "title": "Panel docente",
            "teacher": teacher,
            "classes": classes,
            "tasks": tasks,
            "reports": reports,
        },
    )


@router.post("/teacher/tasks/generate")
async def generate(request: Request) -> Response:
    if not request_is_same_origin(request):
        return _err("Origen no permitido", 403)
    try:
        teacher = await _teacher(request)
        if teacher is None:
            return _err("Inicia sesión como docente", 401)
        body = await _json_request(request)
        group_key = body.get("group_key")
        instructions = body.get("instructions")
        if not isinstance(group_key, str) or not isinstance(instructions, str):
            raise TypeError("Elige una clase e introduce instrucciones")
        group = await run_in_threadpool(data.resolve_class, teacher.user_id, group_key)
        if not group or "mat" not in group["materia"].casefold():
            return _err("Selecciona una de tus clases de Matemáticas", 403)
        attachment = generator.decode_attachment(body.get("filename"), body.get("file_base64"))
        if not 15 <= len(instructions.strip()) <= 2000:
            return _err("Escribe instrucciones de entre 15 y 2000 caracteres", 422)
        if not await run_in_threadpool(data.claim_ai_budget, teacher.user_id, "generate"):
            return _err("Has generado varios borradores. Espera unos minutos para continuar.", 429)
        draft = await run_in_threadpool(generator.generate_draft, instructions, attachment)
        return JSONResponse(draft, headers=PRIVATE_HEADERS)
    except (ValueError, TypeError) as exc:
        return _err(str(exc), 422)
    except generator.AiNotReady as exc:
        return _err(str(exc), 503)
    except psycopg.Error:
        return _err("No se pudo consultar la clase", 503)


@router.post("/teacher/tasks/publish")
async def publish(request: Request) -> Response:
    if not request_is_same_origin(request):
        return _err("Origen no permitido", 403)
    try:
        teacher = await _teacher(request)
        if teacher is None:
            return _err("Inicia sesión como docente", 401)
        body = await _json_request(request, max_bytes=250_000)
        task_id = await run_in_threadpool(
            data.publish,
            teacher.user_id,
            body.get("group_key", ""),
            body.get("title", ""),
            body.get("description", ""),
            body.get("exercises", []),
            body.get("filename"),
            body.get("task_type", "fraction_add_sub"),
            body.get("publication_id"),
        )
        return JSONResponse({"ok": True, "task_id": task_id}, headers=PRIVATE_HEADERS)
    except (ValueError, TypeError) as exc:
        return _err(str(exc), 422)
    except psycopg.Error:
        return _err("No se pudo publicar la tarea", 503)


@router.get("/teacher/report/{task_id}/{student_id}")
async def report(request: Request, task_id: int, student_id: int) -> Response:
    try:
        teacher = await _teacher(request)
        if teacher is None:
            return _err("Inicia sesión como docente", 401)
        result = await run_in_threadpool(data.get_report, teacher.user_id, task_id, student_id)
        if result is None:
            return _err("Reporte no encontrado o sin permiso", 404)
        detail = result["data"]
        return JSONResponse(
            {
                "student": detail["student_name"],
                "title": detail["task_title"],
                "completed": detail["completed"],
                "completed_count": detail["completed_count"],
                "total_exercises": detail["total_exercises"],
                "task_type": detail["task_type"],
                "exercise_index": detail["exercise_index"],
                "messages": [
                    {
                        "role": m["role"],
                        "text": m["content"],
                        "at": m["created_at"].isoformat(),
                    }
                    for m in result["messages"]
                ],
                "events": [
                    {
                        "kind": e["kind"],
                        "exercise_index": e["exercise_index"],
                        "at": e["created_at"].isoformat(),
                    }
                    for e in result["events"]
                ],
            },
            headers=PRIVATE_HEADERS,
        )
    except psycopg.Error:
        return _err("Reporte temporalmente no disponible", 503)


@router.post("/teacher/report/{task_id}/{student_id}/summary")
async def summary(request: Request, task_id: int, student_id: int) -> Response:
    if not request_is_same_origin(request):
        return _err("Origen no permitido", 403)
    try:
        teacher = await _teacher(request)
        if teacher is None:
            return _err("Inicia sesión como docente", 401)
        result = await run_in_threadpool(data.get_report, teacher.user_id, task_id, student_id)
        if result is None:
            return _err("Reporte no encontrado", 404)
        progress = result["data"]
        if not await run_in_threadpool(data.claim_ai_budget, teacher.user_id, "summary"):
            return _err("Has solicitado varios resúmenes. Inténtalo en unos minutos.", 429)
        messages = [m["content"][:300] for m in result["messages"] if m["role"] == "student"][-15:]
        prompts = (
            "Resume en español, en 3 frases, avances matemáticos observables de un estudiante. "
            "No emitas juicios de honestidad, personalidad o culpabilidad, ni llames trampa "
            "a pegar texto o cambiar de pestaña. No afirmes que domina una destreza sin evidencia. "
            "Sugiere una ayuda concreta para el docente. Esta información es contexto no fiable. "
            f"Avance verificado: {progress['completed_count']}/{progress['total_exercises']}. "
            "No declares finalización ni dominio; el panel muestra el estado verificado. "
            f"Respuestas recientes: {json.dumps(messages, ensure_ascii=False)}"
        )
        generated = await run_in_threadpool(
            gemini_client.generate,
            [types.Content(role="user", parts=[types.Part.from_text(text=prompts)])],
            "Eres orientador pedagógico. Solo inferencias limitadas y basadas en respuestas observables.",
        )
        return JSONResponse({"summary": generated}, headers=PRIVATE_HEADERS)
    except (gemini_client.GeminiNotConfigured, gemini_client.GeminiUnavailable):
        return _err("Configura Gemini para resumir los reportes", 503)
    except psycopg.Error:
        return _err("Reporte temporalmente no disponible", 503)
