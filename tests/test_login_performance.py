"""Regresión de permisos y métricas, sin conexión a servicios externos."""

import json
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from unittest.mock import MagicMock, patch

import psycopg
from fastapi.testclient import TestClient
from psycopg.rows import dict_row

from backend.core import database, timing
from backend.main import app
from backend.modules.student_access import repository
from backend.modules.student_access import service as access
from backend.modules.student_dashboard import service as dashboard
from backend.modules.teacher_portal import data
from scripts.benchmark_login_offline import (
    PASSWORD,
    DatabaseDouble,
    offline,
    student_flow,
    teacher_flow,
)


class LoginPerformanceTests(unittest.TestCase):
    def test_student_flow_reuses_connections_not_permissions(self):
        db = DatabaseDouble(delay=False)
        with offline(db), timing.capture() as metrics:
            student_flow()
        self.assertEqual(db.connects, 2)
        self.assertEqual(db.closes, 2)
        self.assertEqual(db.commits, 4)
        self.assertEqual(db.queries, 10)
        sql = "\n".join(db.statements)
        self.assertIn("FOR SHARE OF usr", sql)
        self.assertEqual(sql.count("lower(btrim(role.nombre)) = 'estudiante'"), 3)
        self.assertIn("sess.expires_at > now()", sql)
        self.assertIn("t.id_docente = clase.id_docente", sql)
        self.assertEqual(metrics.snapshot()["db.reuse"]["count"], 2)
        self.assertIn("auth.password_verify", metrics.snapshot())

    def test_teacher_dashboard_has_no_query_per_class(self):
        db = DatabaseDouble(delay=False)
        with offline(db):
            teacher_flow()
        self.assertEqual(db.connects, 3)
        self.assertEqual(db.queries, 6)
        self.assertEqual(db.closes, 3)
        sql = "\n".join(db.statements)
        self.assertIn("lower(btrim(r.nombre)) = 'docente'", sql)
        self.assertIn("plan.teacher_user_id = %s", sql)
        self.assertIn("assigned.id_docente = t.id_docente", sql)

    def test_revoked_role_rejects_session_creation(self):
        db = DatabaseDouble(delay=False)
        with (
            offline(db),
            patch.object(
                repository, "save_access_for_neon_user", side_effect=repository.AccountRevoked
            ),
            self.assertRaises(access.AccessRejected),
        ):
            access.create_access("Offline", PASSWORD, None)
        self.assertEqual(db.connects, 1)
        self.assertEqual(db.closes, 1)

    def test_bad_password_rejects_and_closes(self):
        db = DatabaseDouble(delay=False)
        with offline(db), self.assertRaises(access.AccessRejected):
            access.create_access("Offline", "wrong", None)
        self.assertEqual(db.connects, 1)
        self.assertEqual(db.closes, 1)
        self.assertFalse(any("INSERT" in query for query in db.statements))

    def test_invalid_or_expired_session_never_loads_dashboard(self):
        db = DatabaseDouble(delay=False)
        with offline(db), patch.object(dashboard, "load_dashboard") as load:
            self.assertEqual(dashboard.load_authenticated_dashboard(None, None), (None, None))
            load.assert_not_called()
        self.assertEqual(db.connects, 0)
        with (
            offline(db),
            patch.object(repository, "session_profile", return_value=None),
            patch.object(dashboard, "load_dashboard") as load,
        ):
            self.assertEqual(dashboard.load_authenticated_dashboard("a" * 43, None), (None, None))
            load.assert_not_called()

    def test_row_factories_and_scope_lifetime(self):
        db = DatabaseDouble(delay=False)
        with offline(db):
            for _ in range(2):
                with database.connection_scope():
                    with database.connect("offline", label="test", row_factory=dict_row) as conn:
                        self.assertEqual(
                            conn.execute("SELECT usr.id FROM public.usuario").fetchone(), {"id": 1}
                        )
                    with database.connect("offline", label="test") as conn:
                        self.assertEqual(
                            conn.execute("SELECT usr.id FROM public.usuario").fetchone(), (1,)
                        )
        self.assertEqual(db.connects, 2)
        self.assertEqual(db.closes, 2)

    def test_rollback_and_close_on_exception(self):
        raw = MagicMock()
        tx = MagicMock()
        raw.transaction.return_value = tx
        tx.__exit__.return_value = False
        error = psycopg.OperationalError("secret connection details")
        raw.execute.side_effect = error
        with (
            patch("psycopg.connect", return_value=raw),
            timing.capture() as metrics,
            self.assertRaises(psycopg.OperationalError),
            database.connection_scope(),
            database.connect("offline", label="test") as conn,
        ):
            conn.execute("SELECT sensitive_column", ("secret password",))
        self.assertIs(tx.__exit__.call_args.args[0], psycopg.OperationalError)
        raw.close.assert_called_once()
        self.assertEqual(metrics.snapshot()["test.query"]["errors"], 1)
        self.assertNotIn("secret", json.dumps(metrics.snapshot()))

    def test_scope_never_crosses_threads(self):
        with database.connection_scope(), ThreadPoolExecutor(max_workers=1) as executor:
            context = copy_context()

            def misuse():
                with database.connect("offline", label="test"):
                    pass

            with self.assertRaises(RuntimeError):
                executor.submit(context.run, misuse).result()

    def test_parallel_scopes_are_isolated(self):
        def work():
            with database.connection_scope(), database.connect("offline", label="test") as conn:
                return conn.raw

        def connect(*args, **kwargs):
            return MagicMock()

        with (
            patch("psycopg.connect", side_effect=connect),
            ThreadPoolExecutor(max_workers=2) as executor,
        ):
            futures = [executor.submit(work) for _ in range(2)]
            raws = [f.result() for f in futures]
        self.assertIsNot(raws[0], raws[1])
        for raw in raws:
            raw.close.assert_called_once()

    def test_endpoint_classification_never_returns_dsn(self):
        for host, kind in [
            ("ep-example-pooler.us-east-1.aws.neon.tech", "neon_pooled"),
            ("ep-example.us-east-1.aws.neon.tech", "neon_direct"),
            ("example.invalid", "other"),
        ]:
            self.assertEqual(
                database.endpoint_kind(f"postgresql://fake:never-log@{host}/private"), kind
            )
        self.assertEqual(database.endpoint_kind("not a connection string"), "unknown")

    def test_http_logs_and_headers_no_sensitive_values(self):
        db = DatabaseDouble(delay=False)
        with (
            offline(db),
            patch("backend.modules.student_access.routes.secure_cookie", return_value=False),
            self.assertLogs("uvicorn.error", level="INFO") as logs,
            TestClient(app) as client,
        ):
            response = client.post(
                "/student/access",
                data={"name": "Offline", "password": PASSWORD},
                headers={"Origin": "http://testserver"},
                follow_redirects=False,
            )
            self.assertEqual(response.status_code, 303)
            self.assertIn("HttpOnly", response.headers["set-cookie"])
            self.assertIn("SameSite=lax", response.headers["set-cookie"])
            token = client.cookies.get("ll_student_session")
            page = client.get("/student/dashboard")
            self.assertEqual(page.status_code, 200)
            self.assertIn("server-timing", page.headers)
            self.assertNotEqual(
                response.headers["x-performance-id"], page.headers["x-performance-id"]
            )
        records = [
            json.loads(line.split("login_performance ", 1)[1])
            for line in logs.output
            if "login_performance " in line
        ]
        self.assertEqual(len(records), 2)
        self.assertIn("student.authentication", records[0]["phases"])
        self.assertIn("template.render", records[1]["phases"])
        text = "\n".join(logs.output)
        for secret in [PASSWORD, token, "Offline", "SELECT ", "postgresql://", "offline.invalid"]:
            self.assertNotIn(secret, text)

    def test_dashboard_failure_preserves_error_and_closes(self):
        db = DatabaseDouble(delay=False)
        with (
            offline(db),
            patch.object(
                dashboard.repository,
                "load_dashboard",
                side_effect=psycopg.OperationalError("hidden"),
            ),
        ):
            session, result = dashboard.load_authenticated_dashboard("a" * 43, None)
            self.assertEqual(session.user_id, 1)
            self.assertIsNone(result)
        self.assertEqual(db.closes, 1)

    def test_class_results_are_unchanged(self):
        db = DatabaseDouble(delay=False)
        with offline(db):
            classes = data.list_classes(1)
        self.assertEqual(len(classes), 6)
        self.assertEqual(classes[0]["student_count"], 25)
        self.assertEqual(classes[0]["key"], "1:1:2026:1:A")
        self.assertEqual(db.queries, 1)


if __name__ == "__main__":
    unittest.main()
