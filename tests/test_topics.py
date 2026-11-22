"""Pruebas completamente offline: SQL simulado, red y entorno real bloqueados."""

import copy
import os
import socket
import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.main import app
from backend.modules.guided_math import repository, service
from backend.modules.guided_math.strategies import progress_view, strategy
from backend.modules.student_task_chat.repository import order_messages
from backend.modules.teacher_portal import data, generator


class MemoryDB:
    def __init__(self):
        self.cid = uuid4()
        self.progress = None
        self.messages = []
        self.open = 0
        self.result = []
        self.fail_finish = False
        self.task_type = "mcm"
        self.exercises = [{"a": 4, "b": 6}]

    def __enter__(self):
        self.open += 1
        self.snapshot = copy.deepcopy((self.progress, self.messages))
        return self

    def __exit__(self, kind, *_):
        self.open -= 1
        if kind:
            self.progress, self.messages = self.snapshot

    def cursor(self):
        db = self

        class Cursor:
            def __enter__(self):
                return db

            def __exit__(self, *_):
                pass

        return Cursor()

    def execute(self, sql, params=()):
        q = " ".join(sql.split())
        self.result = []
        if q.startswith("SET "):
            pass
        elif "SELECT DISTINCT task.id" in q:
            self.result = (
                [{"id": 9, "title": "MCM", "description": "", "is_guided": True}]
                if params == (2, 9)
                else []
            )
        elif q.startswith("SELECT conv.id, conv.created_at"):
            self.result = (
                [
                    {
                        **self.progress,
                        "created_at": datetime.now(UTC),
                        "task_type": "mcm",
                        "student_name": "Estudiante ficticio",
                        "task_title": "MCM",
                        "last_seen_at": datetime.now(UTC),
                    }
                ]
                if params == (1, 1, 9, 2)
                else []
            )
        elif q.startswith("SELECT id, role, content, created_at"):
            self.result = list(reversed(self.messages))
        elif q.startswith("SELECT kind, exercise_index"):
            self.result = []
        elif q.startswith("SELECT exercises"):
            self.result = [{"task_type": self.task_type, "exercises": self.exercises}]
        elif q.startswith("INSERT INTO public.ll_task_conversations"):
            pass
        elif q.startswith("SELECT id FROM public.ll_task_conversations"):
            self.result = [{"id": self.cid}]
        elif q.startswith("INSERT INTO public.ll_tutor_progress"):
            if self.progress is None:
                self.progress = {
                    "id": self.cid,
                    "exercise_index": 1,
                    "stage": "concept",
                    "version": 0,
                    "busy": False,
                    "completed_at": None,
                }
        elif q.startswith("SELECT c.id, p.exercise_index"):
            self.result = [dict(self.progress)] if self.progress else []
        elif q.startswith("SELECT id, content, status"):
            self.result = [m for m in self.messages if m.get("client_request_id") == params[1]]
        elif q.startswith("SELECT id FROM public.ll_task_messages"):
            self.result = [m for m in self.messages if m["status"] == "pending"]
        elif q.startswith("SELECT count(*)"):
            self.result = [{"n": sum(m["role"] == "student" for m in self.messages)}]
        elif q.startswith("SELECT role, content"):
            self.result = list(reversed([m for m in self.messages if m["id"] != params[1]]))[:6]
        elif q.startswith("UPDATE public.ll_tutor_progress SET turn_token"):
            self.progress.update(turn_token=params[0], busy=True)
        elif q.startswith("SELECT version, turn_token"):
            self.result = [dict(self.progress)]
        elif q.startswith("INSERT INTO public.ll_task_messages"):
            initial = "'initial'" in q
            student = "'student'" in q
            if initial and any(m["message_kind"] == "initial" for m in self.messages):
                return self
            self.messages.append(
                {
                    "id": params[0],
                    "role": "student" if student else "assistant",
                    "message_kind": "initial" if initial else ("question" if student else "reply"),
                    "status": "pending" if student else "complete",
                    "content": params[2],
                    "client_request_id": params[3] if student else None,
                    "reply_to_message_id": params[3] if not student and not initial else None,
                    "created_at": datetime(2026, 1, 1, tzinfo=UTC),
                    "message_order": len(self.messages) + 1,
                }
            )
        elif q.startswith("UPDATE public.ll_task_messages SET status"):
            next(m for m in self.messages if m["id"] == params[0])["status"] = "answered"
        elif q.startswith("UPDATE public.ll_tutor_progress SET exercise_index"):
            if self.fail_finish:
                raise RuntimeError("simulated persistence failure")
            self.progress.update(
                exercise_index=params[0],
                stage=params[1],
                completed_at=datetime.now(UTC) if params[1] == "done" else None,
                version=self.progress["version"] + 1,
                busy=False,
                turn_token=None,
            )
        elif q.startswith(
            ("UPDATE public.ll_task_conversations", "INSERT INTO public.ll_tutor_events")
        ):
            pass
        else:
            raise AssertionError("Unexpected SQL: " + q)
        return self

    def fetchone(self):
        return self.result[0] if self.result else None

    def fetchall(self):
        return self.result


REAL_CONNECT = socket.socket.connect


def offline_connect(sock, address):
    if isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
        return REAL_CONNECT(sock, address)  # socketpair interno de asyncio en Windows
    raise AssertionError("External network forbidden")


class OfflineTests(unittest.TestCase):
    real_generate = staticmethod(service.gemini_client.generate)

    def setUp(self):
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {}, clear=True).start()
        patch.object(socket.socket, "connect", offline_connect).start()
        patch("psycopg.connect", side_effect=AssertionError("Real DB forbidden")).start()
        patch.object(service, "_url", return_value="offline").start()
        self.ai = patch.object(
            service.gemini_client,
            "generate",
            return_value="El MCM es el menor múltiplo compartido. Escribe los múltiplos y busca el primero común.",
        ).start()

    def setup_memory(self):
        db = MemoryDB()
        patch("psycopg.connect", return_value=db).start()
        service.start_task(2, 9)
        service.start_task(2, 9)
        self.assertEqual(len(db.messages), 1)
        self.ai.assert_not_called()
        return db

    def test_two_messages_full_orchestration(self):
        db = self.setup_memory()

        def explain(*args, **kwargs):
            self.assertEqual(db.open, 0, "Gemini must run outside transaction")
            return "El MCM es el menor múltiplo compartido. Escribe los múltiplos de ambos números."

        self.ai.side_effect = explain
        rid = uuid4()
        service.send_message(2, 9, rid, "¿Qué es el MCM y cómo se saca?")
        self.assertEqual(progress_view({**db.progress, "task_type": "mcm"})["completed_count"], 0)
        self.assertIsNone(db.progress["completed_at"])
        service.send_message(2, 9, rid, "¿Qué es el MCM y cómo se saca?")
        self.ai.assert_called_once()
        done_id = uuid4()
        service.send_message(2, 9, done_id, "Es 12")
        service.send_message(2, 9, done_id, "Es 12")
        self.ai.assert_called_once()
        self.assertEqual(db.progress["stage"], "done")
        self.assertIsNotNone(db.progress["completed_at"])
        self.assertEqual(progress_view({**db.progress, "task_type": "mcm"})["completed_count"], 1)
        messages = order_messages(list(reversed(db.messages)))
        self.assertEqual(
            [m["role"] for m in messages],
            ["assistant", "student", "assistant", "student", "assistant"],
        )
        self.assertEqual(len(messages), 5)
        self.assertNotIn("12", messages[2]["content"])
        self.assertIn("Completaste esta actividad", messages[4]["content"])
        patch.object(data, "_url", return_value="offline").start()
        report = data.get_report(1, 9, 2)
        self.assertEqual(report["data"]["completed_count"], 1)
        self.assertEqual(report["data"]["total_exercises"], 1)
        self.assertTrue(report["data"]["completed"])
        self.assertEqual(
            [m["content"] for m in report["messages"]], [m["content"] for m in messages]
        )
        self.assertIsNone(data.get_report(99, 9, 2))

    def test_ten_fractions_complete_in_service(self):
        db = MemoryDB()
        db.task_type = "fraction_add_sub"
        db.exercises = [{"a_num": 3, "a_den": 4, "operator": "+", "b_num": 1, "b_den": 6}] * 10
        patch("psycopg.connect", return_value=db).start()
        service.start_task(2, 9)
        for index in range(1, 11):
            for message in ["MCM", "12", "9/12 y 2/12", "11/12"]:
                service.send_message(2, 9, uuid4(), message)
            self.assertEqual(db.progress["exercise_index"], min(10, index + 1))
            self.assertEqual(
                progress_view({**db.progress, "task_type": db.task_type})["completed_count"], index
            )
        self.assertEqual(db.progress["stage"], "done")
        self.assertIsNotNone(db.progress["completed_at"])

    def test_rendered_panels_and_report_api(self):
        from backend.modules.student_access.service import StudentSession
        from backend.modules.student_task_chat.service import Workspace
        from backend.modules.teacher_portal.auth import TeacherSession

        db = self.setup_memory()
        service.send_message(2, 9, uuid4(), "¿Qué es el MCM y cómo se saca?")
        service.send_message(2, 9, uuid4(), "Es 12")
        progress = progress_view({**db.progress, "task_type": "mcm"})
        patch.object(data, "_url", return_value="offline").start()
        patch(
            "backend.modules.teacher_portal.routes._teacher",
            return_value=TeacherSession(1, "Docente ficticio"),
        ).start()
        patch(
            "backend.modules.student_task_chat.routes._session",
            return_value=StudentSession(2, "Estudiante ficticio"),
        ).start()
        task = {
            "id": 9,
            "title": "MCM",
            "description": "Practica",
            "statement": "MCM",
            "is_guided": True,
            "subject_slug": "mat",
            "subject_name": "Matemáticas",
        }
        patch(
            "backend.modules.student_task_chat.service.load_workspace",
            return_value=Workspace(task, {"initial_status": "ready"}, order_messages(db.messages)),
        ).start()
        patch.object(service, "progress_for_student", return_value=progress).start()
        patch.object(data, "list_classes", return_value=[]).start()
        patch.object(data, "list_tasks", return_value=[]).start()
        patch.object(
            data,
            "list_reports",
            return_value=[
                {
                    **progress,
                    "student_name": "Estudiante ficticio",
                    "title": "MCM",
                    "messages": 2,
                    "minutes_observed": 0,
                    "pasted": 0,
                    "tab_hidden": 0,
                    "answer_requests": 0,
                    "task_id": 9,
                    "user_id": 2,
                }
            ],
        ).start()
        with TestClient(app) as client:
            student = client.get("/student/tasks/9")
            self.assertEqual(student.status_code, 200)
            self.assertIn("Actividad completada · 1/1", student.text)
            teacher = client.get("/teacher/dashboard")
            self.assertEqual(teacher.status_code, 200)
            self.assertIn("Completada 1/1", teacher.text)
            report = client.get("/teacher/report/9/2").json()
            self.assertTrue(report["completed"])
            self.assertEqual(len(report["messages"]), 5)
        self.ai.assert_called_once()

    def test_negative_answers_and_positive_grammar(self):
        engine = strategy("mcm")
        ex = {"a": 4, "b": 6}
        for message in [
            "No entiendo",
            "¿es 12?",
            "No sé si será 12",
            "6",
            "18",
            "",
            "Tengo 12 años",
            "Dame la respuesta",
            "¿Qué es el MCM y cómo se saca?",
            "12 o 18",
            "12 porque no sé",
        ]:
            with self.subTest(message=message):
                self.assertEqual(engine.evaluate_response(ex, 1, "concept", message)[1], "concept")
        for message in [
            "12",
            "Es 12",
            "12, porque es el menor múltiplo común",
            "El MCM es 12.",
        ]:
            self.assertTrue(engine.evaluate_response(ex, 1, "concept", message)[2])

    def test_fallback_errors_spoilers_and_markdown(self):
        from backend.modules.student_task_chat.gemini_client import GeminiUnavailable

        for reply in ["El resultado es **12**", "Es doce", "", GeminiUnavailable()]:
            with self.subTest(reply=reply):
                self.ai.side_effect = reply if isinstance(reply, Exception) else None
                self.ai.return_value = reply
                result = service._mcm_reply({"a": 4, "b": 6}, "Ayuda", "Explicación local")
                self.assertEqual(result, "Explicación local")
        self.ai.side_effect = None
        self.ai.return_value = "Busca el **menor** múltiplo común."
        self.assertNotIn("**", service._mcm_reply({"a": 4, "b": 6}, "Ayuda", "Respaldo"))

    def test_concurrent_turn_and_expired_recovery(self):
        db = self.setup_memory()
        rid = uuid4()
        turn = repository.claim("offline", 2, 9, rid, "Ayuda")
        with self.assertRaises(service.TooManyMessages):
            service.send_message(2, 9, uuid4(), "12")
        with self.assertRaises(service.TooManyMessages):
            service.send_message(2, 9, rid, "Ayuda")
        db.progress["busy"] = False  # vence la reserva; recuperar sin repetir llamada IA
        service.send_message(2, 9, rid, "Ayuda")
        self.ai.assert_not_called()
        self.assertFalse(repository.finish("offline", turn, "Vieja respuesta", 1, "concept"))
        self.assertEqual(len(db.messages), 3)

    def test_atomic_failure_and_retry(self):
        db = self.setup_memory()
        rid = uuid4()
        db.fail_finish = True
        with self.assertRaises(RuntimeError):
            service.send_message(2, 9, rid, "12")
        self.assertEqual(db.progress["stage"], "concept")
        self.assertIsNone(db.progress["completed_at"])
        self.assertEqual(len(db.messages), 2)
        db.fail_finish = False
        db.progress["busy"] = False
        service.send_message(2, 9, rid, "12")
        self.assertEqual(db.progress["stage"], "done")
        self.assertEqual(len(db.messages), 3)

    def test_foreign_student_and_request_conflict(self):
        self.setup_memory()
        with self.assertRaises(service.InvalidMessage):
            service.send_message(3, 9, uuid4(), "12")
        rid = uuid4()
        service.send_message(2, 9, rid, "12")
        with self.assertRaises(service.InvalidMessage):
            service.send_message(2, 9, rid, "18")

    def test_sdk_short_timeout_and_no_retry(self):
        from backend.modules.student_task_chat import gemini_client

        # Ejecuta el adaptador real con cliente SDK simulado, jamás con credenciales reales.
        original_generate = type(self).real_generate
        patch.object(gemini_client, "gemini_api_key", return_value="offline-placeholder").start()
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.return_value.text = "Explicación breve"
        factory = patch.object(gemini_client.genai, "Client", return_value=client).start()
        self.assertEqual(
            original_generate([], "Tutor", timeout_ms=8000, max_tokens=350), "Explicación breve"
        )
        opts = factory.call_args.kwargs["http_options"]
        self.assertEqual(opts.timeout, 8000)
        self.assertEqual(opts.retry_options.attempts, 1)
        self.assertEqual(
            client.models.generate_content.call_args.kwargs["config"].max_output_tokens, 350
        )

    def test_closed_plan_registry(self):
        self.assertEqual(strategy().total_exercises, 10)
        for value in [
            [{"a": True, "b": 6}],
            [{"a": 0, "b": 6}],
            [{"a": 101, "b": 6}],
            [],
            [{"a": 4, "b": 6, "answer": 12}],
        ]:
            with self.assertRaises(ValueError):
                strategy("mcm").validate_plan(value)
        with self.assertRaises(ValueError):
            strategy("linear_equation")

    def test_teacher_ai_budget(self):
        patch.object(data, "_url", return_value="offline").start()
        db = MagicMock()
        db.__enter__.return_value = db
        patch("psycopg.connect", return_value=db).start()
        db.execute.return_value.fetchone.return_value = (3,)
        self.assertFalse(data.claim_ai_budget(1, "generate"))
        self.assertFalse(any("INSERT" in c.args[0] for c in db.execute.call_args_list))
        db.execute.return_value.fetchone.return_value = (2,)
        self.assertTrue(data.claim_ai_budget(1, "generate"))
        self.assertTrue(any("INSERT" in c.args[0] for c in db.execute.call_args_list))

    def test_routes_require_session_and_origin(self):
        with TestClient(app) as client:
            for path in [
                "/teacher/tasks/publish",
                "/teacher/tasks/generate",
                "/student/tasks/9/start",
                "/student/tasks/9/messages",
            ]:
                self.assertEqual(client.post(path).status_code, 403)
                self.assertEqual(
                    client.post(path, headers={"Origin": "https://foreign.test"}).status_code, 403
                )
            self.assertEqual(
                client.post(
                    "/teacher/tasks/publish", headers={"Origin": "http://testserver"}, json={}
                ).status_code,
                401,
            )
            self.assertEqual(client.get("/teacher/report/9/2").status_code, 401)
            self.assertEqual(
                client.get("/student/tasks/9", follow_redirects=False).status_code, 303
            )

    def test_publish_new_mcm_and_retry(self):
        group = {
            "id_docente": 1,
            "id_materia": 2,
            "gestion": 2026,
            "curso": 1,
            "paralelo": "A",
            "materia": "Matemáticas",
        }
        patch.object(data, "resolve_class", return_value=group).start()
        patch.object(data, "_url", return_value="offline").start()
        db = MagicMock()
        db.__enter__.return_value = db
        patch("psycopg.connect", return_value=db).start()
        db.execute.return_value.fetchone.side_effect = [{"owned": 1}, None, {"id": 9}]
        rid = str(uuid4())
        args = (
            1,
            "group",
            "Mínimo común múltiplo de 4 y 6",
            "Encuentra el MCM de ambos números.",
            [{"a": 4, "b": 6}],
            None,
            "mcm",
            rid,
        )
        self.assertEqual(data.publish(*args), 9)
        sql = " ".join(str(c.args[0]) for c in db.execute.call_args_list)
        self.assertNotIn("UPDATE public.tarea", sql)
        self.assertNotIn("DELETE", sql)
        db.execute.return_value.fetchone.side_effect = [{"owned": 1}, {"task_id": 9}]
        self.assertEqual(data.publish(*args), 9)
        self.ai.assert_not_called()
        patch.object(data, "resolve_class", return_value=None).start()
        with self.assertRaises(ValueError):
            data.publish(*args)

    def test_gemini_fraction_generation_and_file_checks(self):
        import json

        ex = {"a_num": 3, "a_den": 4, "operator": "+", "b_num": 1, "b_den": 6}
        patch.object(generator, "gemini_api_key", return_value="fake-offline").start()
        client = MagicMock()
        client.__enter__.return_value = client
        client.models.generate_content.return_value.text = json.dumps(
            {"title": "Fracciones", "description": "Resuelve paso a paso", "exercises": [ex] * 10}
        )
        patch.object(generator.genai, "Client", return_value=client).start()
        draft = generator.generate_draft("Diez ejercicios de 3/4 + 1/6", None)
        self.assertEqual(len(draft["exercises"]), 10)
        with self.assertRaises(generator.InvalidAttachment):
            generator.decode_attachment("x.pdf", "YWJj")


if __name__ == "__main__":
    unittest.main()
