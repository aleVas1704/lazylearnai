"""Métricas por petición: etiquetas internas, sin SQL, parámetros ni excepciones."""

import json
import logging
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from threading import Lock
from time import perf_counter
from uuid import uuid4

_current = ContextVar("request_metrics", default=None)
CATEGORIES = {
    "/student/access": "student.login",
    "/student/dashboard": "student.dashboard",
    "/teacher/access": "teacher.login",
    "/teacher/dashboard": "teacher.dashboard",
}


class Metrics:
    def __init__(self):
        self.phases = {}
        self.endpoint = "unknown"
        self.lock = Lock()

    def add(self, label, duration, failed):
        with self.lock:
            row = self.phases.setdefault(label, {"count": 0, "ms": 0.0, "errors": 0})
            row["count"] += 1
            row["ms"] += duration * 1000
            row["errors"] += int(failed)

    def snapshot(self):
        with self.lock:
            return {key: {**row, "ms": round(row["ms"], 2)} for key, row in self.phases.items()}


@contextmanager
def capture():
    metrics = Metrics()
    token = _current.set(metrics)
    try:
        yield metrics
    finally:
        _current.reset(token)


@contextmanager
def measure(label):
    started = perf_counter()
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        metrics = _current.get()
        if metrics is not None:
            metrics.add(label, perf_counter() - started, failed)


def timed(label):
    def decorate(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            with measure(label):
                return fn(*args, **kwargs)

        return wrapped

    return decorate


def note_endpoint(kind):
    metrics = _current.get()
    if metrics is not None:
        metrics.endpoint = (
            kind if kind in {"neon_pooled", "neon_direct", "other", "unknown"} else "unknown"
        )


class TimingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        category = CATEGORIES.get(scope.get("path"))
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        if category is None:
            started = perf_counter()
            try:
                return await self.app(scope, receive, send)
            finally:
                logging.getLogger("uvicorn.error").info(
                    "http_total_ms=%.1f", (perf_counter() - started) * 1000
                )
        started = perf_counter()
        status = 500
        request_id = uuid4().hex

        async def measured_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message = {
                    **message,
                    "headers": list(message.get("headers", []))
                    + [
                        (b"x-performance-id", request_id.encode("ascii")),
                        (
                            b"server-timing",
                            f"app;dur={(perf_counter() - started) * 1000:.2f}".encode("ascii"),
                        ),
                    ],
                }
            await send(message)

        with capture() as metrics:
            try:
                await self.app(scope, receive, measured_send)
            finally:
                logging.getLogger("uvicorn.error").info(
                    "login_performance %s",
                    json.dumps(
                        {
                            "request": request_id,
                            "route": category,
                            "status": status,
                            "http_ms": round((perf_counter() - started) * 1000, 2),
                            "database_endpoint": metrics.endpoint,
                            "phases": metrics.snapshot(),
                        },
                        separators=(",", ":"),
                    ),
                )


@timed("template.render")
def render_template(templates, **kwargs):
    return templates.TemplateResponse(**kwargs)
