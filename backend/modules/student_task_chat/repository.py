"""SQL parametrizado para tareas, conversaciones e idempotencia."""

from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

TASK_SQL = """SELECT DISTINCT task.id,
                     COALESCE(NULLIF(btrim(task.titulo), ''), 'Tarea sin titulo') AS title,
                     COALESCE(task.descripcion, '') AS description,
                     COALESCE(task.descripcion, '') AS statement,
                     'materia-' || m.id AS subject_slug, m.nombre AS subject_name
              FROM public.ll_user_estudiante AS link
              JOIN public.inscritos AS ins ON ins.id_estudiante = link.estudiante_id
              JOIN public.clase_paralelo AS clase
                ON clase.curso = ins.curso
               AND clase.paralelo = ins.paralelo
               AND clase.gestion = ins.gestion
              JOIN public.tarea AS task
                ON task.id_docente = clase.id_docente
               AND task.id_materia = clase.id_materia
               AND task.gestion = clase.gestion
               AND task.curso = clase.curso
               AND task.paralelo = clase.paralelo
              JOIN public.matera AS m ON m.id = clase.id_materia
              WHERE link.user_id = %s AND task.id = %s"""


def load_workspace(url: str, user_id: int, task_id: int) -> dict[str, object] | None:
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(TASK_SQL, (user_id, task_id))
        task = cursor.fetchone()
        if not task:
            return None
        cursor.execute(
            """SELECT id, initial_status FROM public.ll_task_conversations
               WHERE user_id = %s AND task_id = %s""",
            (user_id, task_id),
        )
        conversation = cursor.fetchone()
        messages: list[dict[str, object]] = []
        if conversation:
            cursor.execute(
                """SELECT id, role, message_kind, status, content, created_at
                   FROM public.ll_task_messages
                   WHERE conversation_id = %s
                   ORDER BY created_at, id""",
                (conversation["id"],),
            )
            messages = cursor.fetchall()
        return {"task": task, "conversation": conversation, "messages": messages}


def claim_initial(url: str, user_id: int, task_id: int) -> dict[str, object] | None:
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(TASK_SQL, (user_id, task_id))
        task = cursor.fetchone()
        if not task:
            return None
        conversation_id = uuid4()
        cursor.execute(
            """INSERT INTO public.ll_task_conversations (id, user_id, task_id)
               VALUES (%s, %s, %s)
               ON CONFLICT (user_id, task_id) DO NOTHING""",
            (conversation_id, user_id, task_id),
        )
        cursor.execute(
            """SELECT id, initial_status, initial_started_at
               FROM public.ll_task_conversations
               WHERE user_id = %s AND task_id = %s FOR UPDATE""",
            (user_id, task_id),
        )
        conversation = cursor.fetchone()
        # Un estado pending reciente ya pertenece a otra solicitud. Los bloqueos vencidos
        # pueden reclamarse después de dos minutos.
        if conversation["initial_status"] == "ready":
            return {"claimed": False, "task": task, "conversation_id": conversation["id"]}
        if conversation["initial_status"] == "pending":
            cursor.execute(
                """SELECT initial_started_at > now() - interval '2 minutes' AS is_recent
                   FROM public.ll_task_conversations WHERE id = %s""",
                (conversation["id"],),
            )
            recent_pending = cursor.fetchone()["is_recent"]
            if recent_pending:
                return {"claimed": False, "task": task, "conversation_id": conversation["id"]}
        cursor.execute(
            """UPDATE public.ll_task_conversations
               SET initial_status = 'pending', initial_started_at = now(), updated_at = now()
               WHERE id = %s""",
            (conversation["id"],),
        )
        return {"claimed": True, "task": task, "conversation_id": conversation["id"]}


def complete_initial(url: str, conversation_id: UUID, content: str) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """INSERT INTO public.ll_task_messages
                   (id, conversation_id, role, message_kind, status, content)
               VALUES (%s, %s, 'assistant', 'initial', 'complete', %s)
               ON CONFLICT DO NOTHING""",
            (uuid4(), conversation_id, content),
        )
        cursor.execute(
            """UPDATE public.ll_task_conversations
               SET initial_status = 'ready', updated_at = now() WHERE id = %s""",
            (conversation_id,),
        )


def fail_initial(url: str, conversation_id: UUID) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute(
            """UPDATE public.ll_task_conversations
               SET initial_status = 'failed', updated_at = now() WHERE id = %s""",
            (conversation_id,),
        )


def claim_question(
    url: str,
    user_id: int,
    task_id: int,
    request_id: UUID,
    content: str,
) -> dict[str, object] | None:
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(TASK_SQL, (user_id, task_id))
        task = cursor.fetchone()
        if not task:
            return None
        cursor.execute(
            """SELECT id FROM public.ll_task_conversations
               WHERE user_id = %s AND task_id = %s FOR UPDATE""",
            (user_id, task_id),
        )
        conversation = cursor.fetchone()
        if not conversation:
            return {"error": "not_started", "task": task}
        cursor.execute(
            """SELECT id, status, content FROM public.ll_task_messages
               WHERE conversation_id = %s AND client_request_id = %s FOR UPDATE""",
            (conversation["id"], request_id),
        )
        existing = cursor.fetchone()
        if existing:
            if existing["content"] != content:
                return {"error": "request_conflict", "task": task}
            if existing["status"] == "failed":
                cursor.execute(
                    "UPDATE public.ll_task_messages SET status = 'pending' WHERE id = %s",
                    (existing["id"],),
                )
                return {
                    "claimed": True,
                    "task": task,
                    "conversation_id": conversation["id"],
                    "message_id": existing["id"],
                }
            return {"claimed": False, "task": task, "message_id": existing["id"]}
        cursor.execute(
            """SELECT count(*) AS recent_count FROM public.ll_task_messages
               WHERE conversation_id = %s AND role = 'student'
                 AND created_at > now() - interval '10 minutes'""",
            (conversation["id"],),
        )
        if cursor.fetchone()["recent_count"] >= 10:
            return {"error": "rate_limited", "task": task}
        message_id = uuid4()
        cursor.execute(
            """INSERT INTO public.ll_task_messages
                   (id, conversation_id, role, message_kind, status, content, client_request_id)
               VALUES (%s, %s, 'student', 'question', 'pending', %s, %s)""",
            (message_id, conversation["id"], content, request_id),
        )
        return {
            "claimed": True,
            "task": task,
            "conversation_id": conversation["id"],
            "message_id": message_id,
        }


def generation_history(url: str, conversation_id: UUID, exclude_id: UUID) -> list[dict[str, str]]:
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """SELECT role, content FROM public.ll_task_messages
               WHERE conversation_id = %s AND id <> %s
                 AND (role = 'assistant' OR status = 'answered')
               ORDER BY created_at DESC, id DESC LIMIT 12""",
            (conversation_id, exclude_id),
        )
        return list(reversed(cursor.fetchall()))


def complete_question(url: str, conversation_id: UUID, message_id: UUID, content: str) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """INSERT INTO public.ll_task_messages
                   (id, conversation_id, role, message_kind, status, content, reply_to_message_id)
               VALUES (%s, %s, 'assistant', 'reply', 'complete', %s, %s)
               ON CONFLICT (reply_to_message_id) DO NOTHING""",
            (uuid4(), conversation_id, content, message_id),
        )
        cursor.execute(
            "UPDATE public.ll_task_messages SET status = 'answered' WHERE id = %s",
            (message_id,),
        )


def fail_question(url: str, message_id: UUID) -> None:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE public.ll_task_messages SET status = 'failed' WHERE id = %s",
            (message_id,),
        )
