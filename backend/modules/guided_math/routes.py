"""Registro opcional de actividad del navegador para tareas guiadas."""

import json

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from backend.modules.guided_math import service
from backend.modules.student_access import service as student_access
from backend.modules.student_access.http import COOKIE_NAME, PRIVATE_HEADERS, request_is_same_origin

router = APIRouter(tags=["Progreso matemático"])


@router.post("/student/tasks/{task_id}/activity")
async def activity(request: Request, task_id: int) -> Response:
    if not request_is_same_origin(request):
        return Response(status_code=403, headers=PRIVATE_HEADERS)
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        return Response(status_code=415, headers=PRIVATE_HEADERS)
    body = await request.body()
    if len(body) > 128:
        return Response(status_code=413, headers=PRIVATE_HEADERS)
    try:
        value = json.loads(body)
        if not isinstance(value, dict) or set(value) != {"kind"}:
            return Response(status_code=400, headers=PRIVATE_HEADERS)
        session = await run_in_threadpool(
            student_access.get_session, request.cookies.get(COOKIE_NAME)
        )
        if session is None:
            return Response(status_code=401, headers=PRIVATE_HEADERS)
        accepted = await run_in_threadpool(
            service.record_activity, session.user_id, task_id, value["kind"]
        )
        return JSONResponse({"recorded": accepted}, headers=PRIVATE_HEADERS)
    except (ValueError, TypeError, UnicodeError):
        return Response(status_code=400, headers=PRIVATE_HEADERS)
    except (psycopg.Error, student_access.AccessUnavailable):
        return Response(status_code=503, headers=PRIVATE_HEADERS)
