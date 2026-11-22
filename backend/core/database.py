"""Conexiones instrumentadas; reutilización limitada a una operación síncrona.

No hay conexión global ni caché de permisos. Cada repositorio conserva su
transacción; la conexión se cierra al salir de connection_scope, incluso ante error.
"""

import sys
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from threading import get_ident

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import tuple_row

from backend.core.timing import measure, note_endpoint

_scope = ContextVar("database_scope", default=None)


def endpoint_kind(url):
    try:
        host = conninfo_to_dict(url).get("host", "").lower()
    except (psycopg.Error, ValueError):
        return "unknown"
    if host.endswith((".neon.tech", ".neon.build")):
        return "neon_pooled" if "-pooler." in host else "neon_direct"
    return "other"


@contextmanager
def connection_scope():
    """Exclusivo al hilo actual, nunca cruza peticiones ni conserva transacciones."""
    current = _scope.get()
    if current is not None:
        if current["owner"] != get_ident():
            raise RuntimeError("Connection scope cannot cross threads")
        yield
        return
    current = {"owner": get_ident(), "connections": {}}
    token = _scope.set(current)
    try:
        yield
    finally:
        _scope.reset(token)
        for conn in current["connections"].values():
            with measure("db.close"):
                conn.close()


class ObservedCursor:
    def __init__(self, cursor, label):
        self.raw, self.label = cursor, label

    def __enter__(self):
        self.raw.__enter__()
        return self

    def __exit__(self, *args):
        return self.raw.__exit__(*args)

    def execute(self, *args, **kwargs):
        with measure(self.label + ".query"):
            self.raw.execute(*args, **kwargs)
        return self

    def fetchone(self):
        with measure(self.label + ".fetch"):
            return self.raw.fetchone()

    def fetchall(self):
        with measure(self.label + ".fetch"):
            return self.raw.fetchall()


class ObservedConnection:
    def __init__(self, conn, label):
        self.raw, self.label = conn, label

    def cursor(self):
        return ObservedCursor(self.raw.cursor(), self.label)

    def execute(self, *args, **kwargs):
        with measure(self.label + ".query"):
            cursor = self.raw.execute(*args, **kwargs)
        return ObservedCursor(cursor, self.label)


@contextmanager
def connect(url, *, label, connect_timeout=5, row_factory=None):
    note_endpoint(endpoint_kind(url))
    current = _scope.get()
    if current is not None and current["owner"] != get_ident():
        raise RuntimeError("Connection scope cannot cross threads")
    raw = current["connections"].get(url) if current is not None else None
    if raw is None:
        with measure("db.connect"):
            raw = psycopg.connect(
                url,
                connect_timeout=connect_timeout,
                row_factory=row_factory or tuple_row,
                prepare_threshold=None,
            )
        if current is not None:
            current["connections"][url] = raw
    else:
        with measure("db.reuse"):
            raw.row_factory = row_factory or tuple_row
    manager = raw.transaction() if current is not None else raw
    with measure(label + ".transaction_begin"):
        entered = manager.__enter__()
    conn = raw if current is not None else entered
    try:
        yield ObservedConnection(conn, label)
    except BaseException:
        with measure(label + ".transaction_end"):
            suppress = manager.__exit__(*sys.exc_info())
        if not suppress:
            raise
    else:
        with measure(label + ".transaction_end"):
            manager.__exit__(None, None, None)


def ping_database(url: str) -> None:
    """Chequeo manual existente, nunca invocado automáticamente."""
    with connect(url, label="health") as conn:
        if conn.execute("SELECT 1").fetchone() != (1,):
            raise RuntimeError("Respuesta inesperada de la base de datos")


def reuse_connections(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with connection_scope():
            return fn(*args, **kwargs)

    return wrapped
