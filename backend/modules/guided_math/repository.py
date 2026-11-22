"""Reserva y guardado breves: ninguna llamada de IA dentro de una transacción."""

from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from backend.modules.guided_math.strategies import strategy
from backend.modules.student_task_chat.repository import TASK_SQL


def task_and_plan(cursor, user_id, task_id):
    cursor.execute(TASK_SQL, (user_id, task_id))
    task = cursor.fetchone()
    if not task:
        return None
    cursor.execute(
        "SELECT exercises, task_type FROM public.ll_teacher_task_plans WHERE task_id = %s",
        (task_id,),
    )
    plan = cursor.fetchone()
    if not plan:
        return None
    engine = strategy(plan["task_type"])
    return {
        "task": task,
        "task_type": engine.task_type,
        "exercises": engine.validate_plan(plan["exercises"]),
    }


def claim(url, user_id, task_id, request_id, message):
    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as db, db.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '5s'")
        data = task_and_plan(cur, user_id, task_id)
        if not data:
            return {"error": "access"}
        cur.execute(
            """SELECT c.id, p.exercise_index, p.stage, p.version,
                             p.turn_until > now() AS busy
                      FROM public.ll_task_conversations c
                      JOIN public.ll_tutor_progress p ON p.conversation_id = c.id
                      WHERE c.user_id = %s AND c.task_id = %s FOR UPDATE OF c, p""",
            (user_id, task_id),
        )
        progress = cur.fetchone()
        if not progress:
            return {"error": "not_started"}
        cid = progress["id"]
        cur.execute(
            """SELECT id, content, status FROM public.ll_task_messages
                       WHERE conversation_id = %s AND client_request_id = %s""",
            (cid, request_id),
        )
        existing = cur.fetchone()
        if existing and existing["content"] != message:
            return {"error": "conflict"}
        if existing and existing["status"] == "answered":
            return {"claimed": False}
        if progress["busy"]:
            return {"error": "busy"}
        # Un turno interrumpido debe recuperarse con su mismo request_id; nunca reconsumir IA.
        cur.execute(
            "SELECT id FROM public.ll_task_messages WHERE conversation_id = %s AND status = 'pending' AND role = 'student'",
            (cid,),
        )
        pending = cur.fetchone()
        if pending and (not existing or pending["id"] != existing["id"]):
            return {"error": "busy"}
        cur.execute(
            "SELECT count(*) AS n FROM public.ll_task_messages WHERE conversation_id = %s AND role = 'student' AND created_at > now() - interval '10 minutes'",
            (cid,),
        )
        if cur.fetchone()["n"] >= 40 and not existing:
            return {"error": "busy"}
        sid = existing["id"] if existing else uuid4()
        token = uuid4()
        if not existing:
            cur.execute(
                """INSERT INTO public.ll_task_messages
                (id, conversation_id, role, message_kind, status, content, client_request_id)
                VALUES (%s, %s, 'student', 'question', 'pending', %s, %s)""",
                (sid, cid, message, request_id),
            )
        cur.execute(
            "UPDATE public.ll_tutor_progress SET turn_token = %s, turn_until = now() + interval '45 seconds' WHERE conversation_id = %s",
            (token, cid),
        )
        cur.execute(
            """SELECT role, content FROM public.ll_task_messages
                       WHERE conversation_id = %s AND id <> %s
                       ORDER BY created_at DESC, message_order DESC LIMIT 6""",
            (cid, sid),
        )
        return {
            **data,
            "claimed": True,
            "progress": progress,
            "cid": cid,
            "sid": sid,
            "token": token,
            "recover": bool(existing),
            "history": list(reversed(cur.fetchall())),
        }


def finish(url, turn, reply, index, stage, answer_request=False):
    with psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as db, db.cursor() as cur:
        cur.execute("SET LOCAL statement_timeout = '5s'")
        cur.execute(
            """SELECT version, turn_token FROM public.ll_tutor_progress
                       WHERE conversation_id = %s FOR UPDATE""",
            (turn["cid"],),
        )
        current = cur.fetchone()
        if (
            current["version"] != turn["progress"]["version"]
            or current["turn_token"] != turn["token"]
        ):
            return False
        cur.execute(
            """INSERT INTO public.ll_task_messages
            (id, conversation_id, role, message_kind, status, content, reply_to_message_id)
            VALUES (%s, %s, 'assistant', 'reply', 'complete', %s, %s)""",
            (uuid4(), turn["cid"], reply[:4000], turn["sid"]),
        )
        cur.execute(
            "UPDATE public.ll_task_messages SET status = 'answered' WHERE id = %s", (turn["sid"],)
        )
        cur.execute(
            """UPDATE public.ll_tutor_progress SET exercise_index = %s, stage = %s,
            completed_at = CASE WHEN %s = 'done' THEN COALESCE(completed_at, now()) ELSE NULL END,
            last_seen_at = now(), turn_token = NULL, turn_until = NULL, version = version + 1
            WHERE conversation_id = %s""",
            (index, stage, stage, turn["cid"]),
        )
        cur.execute(
            "UPDATE public.ll_task_conversations SET updated_at = now() WHERE id = %s",
            (turn["cid"],),
        )
        if answer_request:
            cur.execute(
                "INSERT INTO public.ll_tutor_events (id, conversation_id, kind, exercise_index) VALUES (%s, %s, 'answer_request', %s)",
                (uuid4(), turn["cid"], turn["progress"]["exercise_index"]),
            )
        return True
