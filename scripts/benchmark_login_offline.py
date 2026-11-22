"""Benchmark reproducible SIN red ni credenciales; costes artificiales declarados."""

import argparse
import hashlib
import json
import os
import statistics
import time
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

from psycopg.rows import dict_row

from backend.modules.student_access import service as access
from backend.modules.student_dashboard import service as dashboard
from backend.modules.teacher_portal import auth, data

PASSWORD = "offline-example"
SALT = b"0123456789abcdef"
STORED = (
    "pbkdf2_sha256$200000$"
    + SALT.hex()
    + "$"
    + hashlib.pbkdf2_hmac("sha256", PASSWORD.encode(), SALT, 200000).hex()
)


class DatabaseDouble:
    def __init__(self, delay=True):
        self.connects = self.queries = self.commits = self.closes = 0
        self.delay = delay
        self.statements = []

    def pause(self, seconds):
        if self.delay:
            time.sleep(seconds)

    def connect(self, *args, **kwargs):
        self.connects += 1
        self.pause(0.005)
        return ConnectionDouble(self, kwargs.get("row_factory"))


class ConnectionDouble:
    def __init__(self, database, row_factory):
        self.database = database
        self.row_factory = row_factory
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, kind, *_):
        self.database.commits += 1
        self.database.pause(0.001)
        self.close()

    @contextmanager
    def transaction(self):
        try:
            yield self
        finally:
            self.database.commits += 1
            self.database.pause(0.001)

    def close(self):
        self.closed = True
        self.database.closes += 1

    def cursor(self, **kwargs):
        return CursorDouble(self, kwargs.get("row_factory", self.row_factory))

    def execute(self, query, params=()):
        return self.cursor().execute(query, params)


class CursorDouble:
    def __init__(self, conn, row_factory):
        self.conn, self.row_factory = conn, row_factory
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def close(self):
        pass

    def execute(self, sql, params=()):
        db = self.conn.database
        db.queries += 1
        db.statements.append(sql)
        db.pause(0.002)
        q = " ".join(sql.split())
        self.rows = []
        if "SELECT usr.id, usr.name, usr.password" in q:
            self.rows = [{"id": 1, "name": "Offline", "password": STORED}]
        elif "SELECT usr.id, usr.password" in q:
            self.rows = [{"id": 1, "password": STORED}]
        elif "SELECT usr.id FROM public.usuario" in q:
            self.rows = [{"id": 1}]
        elif "SELECT usr.id, usr.name" in q:
            self.rows = [{"id": 1, "name": "Offline"}]
        elif "SELECT DISTINCT m.id" in q:
            self.rows = [
                {"id": 1, "slug": "materia-1", "name": "Matemáticas", "icon_name": "book-open"}
            ]
        elif "SELECT DISTINCT t.id" in q:
            self.rows = [{"id": 8, "title": "Fracciones"}]
        elif "SELECT c.id_docente" in q:
            self.rows = [
                {
                    "id_docente": 1,
                    "id_materia": 1,
                    "gestion": 2026,
                    "curso": i,
                    "paralelo": "A",
                    "materia": "Matemáticas",
                    "curso_nombre": str(i),
                    "nivel": "secundaria",
                    "student_count": 25,
                }
                for i in range(1, 7)
            ]
        elif "SELECT count(*) FROM public.inscritos" in q:
            self.rows = [{"count": 25}]
        elif q.startswith(("SET ", "INSERT ", "DELETE ")) or "ll_teacher_task_plans" in q:
            pass
        else:
            raise AssertionError("SQL inesperado en benchmark offline")
        return self

    def fetchall(self):
        return (
            self.rows
            if self.row_factory is dict_row
            else [tuple(row.values()) for row in self.rows]
        )

    def fetchone(self):
        rows = self.fetchall()
        return rows[0] if rows else None


@contextmanager
def offline(database):
    with ExitStack() as stack:
        stack.enter_context(patch.dict(os.environ, {}, clear=True))
        stack.enter_context(patch("psycopg.connect", side_effect=database.connect))
        for module, name in [
            (access, "database_url"),
            (dashboard, "database_url"),
            (auth, "_url"),
            (data, "_url"),
        ]:
            stack.enter_context(
                patch.object(module, name, return_value="postgresql://offline.invalid/test")
            )
        yield


def student_flow():
    token = access.create_access("Offline", PASSWORD, None)
    if hasattr(dashboard, "load_authenticated_dashboard"):
        dashboard.load_authenticated_dashboard(token, None)
    else:
        session = access.get_session(token)
        dashboard.load_dashboard(session.user_id, None)


def teacher_flow():
    token = auth.sign_in("Offline", PASSWORD, None)
    session = auth.get_session(token)
    if hasattr(data, "load_dashboard"):
        data.load_dashboard(session.user_id)
    else:
        data.list_classes(session.user_id)
        data.list_tasks(session.user_id)
        data.list_reports(session.user_id)


def measure(samples=7):
    result = {
        "mode": "offline synthetic latency; NOT Neon measurements",
        "costs_ms": {"connect": 5, "statement": 2, "transaction_end": 1},
        "samples": samples,
    }
    for name, flow in [("student", student_flow), ("teacher_6_classes", teacher_flow)]:
        elapsed = []
        for _ in range(samples):
            db = DatabaseDouble()
            with offline(db):
                started = time.perf_counter()
                flow()
                elapsed.append((time.perf_counter() - started) * 1000)
        result[name] = {
            "median_ms": round(statistics.median(elapsed), 2),
            "min_ms": round(min(elapsed), 2),
            "max_ms": round(max(elapsed), 2),
            "connections": db.connects,
            "statements": db.queries,
            "transactions": db.commits,
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = measure()
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
