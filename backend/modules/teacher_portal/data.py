"""Consultas docentes, clase autorizada, publicación y reportes observables."""

from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from backend.core.config import database_url
from backend.core.database import connect, reuse_connections
from backend.core.timing import timed
from backend.modules.guided_math.strategies import progress_view, strategy
from backend.modules.student_task_chat.repository import order_messages


def _url() -> str:
    url = database_url()
    if not url:
        raise psycopg.OperationalError("DATABASE_URL no configurada")
    return url


def claim_ai_budget(teacher_id: int, kind: str) -> bool:
    """Cuota compartida entre procesos; transacción cerrada antes de llamar a IA."""
    if kind not in {"generate", "summary"}:
        return False
    limit = 3 if kind == "generate" else 10
    with connect(_url(), label="teacher.dashboard.claim_ai_budget", connect_timeout=5) as db:
        db.execute("SET LOCAL statement_timeout = '5s'")
        db.execute("SELECT pg_advisory_xact_lock(%s, %s)", (731007, teacher_id))
        count = db.execute(
            """SELECT count(*) FROM public.ll_teacher_ai_requests
               WHERE teacher_user_id = %s AND kind = %s
                 AND created_at > now() - interval '10 minutes'""",
            (teacher_id, kind),
        ).fetchone()[0]
        if count >= limit:
            return False
        db.execute(
            "DELETE FROM public.ll_teacher_ai_requests WHERE teacher_user_id = %s AND created_at < now() - interval '1 day'",
            (teacher_id,),
        )
        db.execute(
            "INSERT INTO public.ll_teacher_ai_requests (teacher_user_id, kind) VALUES (%s, %s)",
            (teacher_id, kind),
        )
        return True


def _class_sql() -> str:
    return """SELECT c.id_docente, c.id_materia, c.gestion, c.curso, c.paralelo,
                     m.nombre AS materia, cu.curso AS curso_nombre,
                     cu.nivel_academico::text AS nivel,
                     (SELECT count(*) FROM public.inscritos AS ins
                      WHERE ins.curso = c.curso AND ins.paralelo = c.paralelo
                        AND ins.gestion = c.gestion) AS student_count
              FROM public.ll_user_docente AS link
              JOIN public.clase_paralelo AS c ON c.id_docente = link.docente_id
              JOIN public.matera AS m ON m.id = c.id_materia
              JOIN public.curso AS cu ON cu.id = c.curso
              WHERE link.user_id = %s"""


def list_classes(teacher_id: int) -> list[dict]:
    with connect(
        _url(), label="teacher.dashboard.list_classes", connect_timeout=5, row_factory=dict_row
    ) as db:
        classes = db.execute(
            _class_sql() + " ORDER BY materia, curso_nombre, c.paralelo", (teacher_id,)
        ).fetchall()
        for c in classes:
            c["key"] = (
                f"{c['id_docente']}:{c['id_materia']}:{c['gestion']}:{c['curso']}:{c['paralelo']}"
            )
            c["label"] = (
                f"{c['materia']} — {c['curso_nombre']} {c['nivel']} {c['paralelo']} ({c['gestion']})"
            )
        return classes


def resolve_class(teacher_id: int, group_key: str) -> dict | None:
    for row in list_classes(teacher_id):
        if row["key"] == group_key:
            return row
    return None


def publish(
    teacher_id: int,
    group_key: str,
    title: str,
    instructions: str,
    exercises: list[dict],
    source_filename: str | None,
    task_type: str = "fraction_add_sub",
    publication_id: str | None = None,
) -> int:
    if not all(isinstance(v, str) for v in (group_key, title, instructions)):
        raise ValueError("Completa los datos de la tarea")
    if source_filename is not None and not isinstance(source_filename, str):
        raise ValueError("Nombre de archivo inválido")
    if publication_id is not None and not isinstance(publication_id, str):
        raise ValueError("Identificador de publicación inválido")
    publication_id = UUID(publication_id) if publication_id else None

    group = resolve_class(teacher_id, group_key)
    if not group or "mat" not in group["materia"].casefold():
        raise ValueError("Selecciona una clase de Matemáticas asignada al docente")
    title = " ".join(title.split())[:120]
    instructions = instructions.strip()
    if len(title) < 4 or not 10 <= len(instructions) <= 2000:
        raise ValueError("Completa el título y las instrucciones de la tarea")
    validated = strategy(task_type).validate_plan(exercises)
    if source_filename:
        source_filename = source_filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1][:100]
    from psycopg.types.json import Jsonb

    with connect(
        _url(), label="teacher.dashboard.publish", connect_timeout=5, row_factory=dict_row
    ) as db:
        # Comprobar propiedad de la clase en la misma transacción.
        owned = db.execute(
            """SELECT 1 FROM public.ll_user_docente AS link
               JOIN public.clase_paralelo AS c ON c.id_docente = link.docente_id
               WHERE link.user_id = %s AND c.id_docente = %s
                 AND c.id_materia = %s AND c.gestion = %s
                 AND c.curso = %s AND c.paralelo = %s FOR SHARE OF c""",
            (
                teacher_id,
                group["id_docente"],
                group["id_materia"],
                group["gestion"],
                group["curso"],
                group["paralelo"],
            ),
        ).fetchone()
        if not owned:
            raise ValueError("Clase no disponible")
        if publication_id:
            # Serializa reintentos del mismo borrador antes de insertar una nueva tarea.
            db.execute("SELECT pg_advisory_xact_lock(%s)", (publication_id.int % (2**63 - 1),))
            existing = db.execute(
                "SELECT task_id FROM public.ll_teacher_task_plans WHERE teacher_user_id = %s AND publication_id = %s",
                (teacher_id, publication_id),
            ).fetchone()
            if existing:
                return existing["task_id"]
        task_id = db.execute(
            """INSERT INTO public.tarea
                 (titulo, descripcion, id_docente, id_materia, gestion, curso, paralelo)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                title,
                instructions,
                group["id_docente"],
                group["id_materia"],
                group["gestion"],
                group["curso"],
                group["paralelo"],
            ),
        ).fetchone()["id"]
        db.execute(
            """INSERT INTO public.ll_teacher_task_plans
                 (task_id, teacher_user_id, teacher_instructions, source_filename, exercises, task_type, publication_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                task_id,
                teacher_id,
                instructions,
                source_filename,
                Jsonb(validated),
                task_type,
                publication_id,
            ),
        )
        return task_id


def list_tasks(teacher_id: int) -> list[dict]:
    with connect(
        _url(), label="teacher.dashboard.list_tasks", connect_timeout=5, row_factory=dict_row
    ) as db:
        rows = db.execute(
            """SELECT t.id, t.titulo AS title, t.curso, t.paralelo, t.gestion,
                      m.nombre AS materia,
                      c.curso AS curso_nombre,
                      p.created_at,
                      (SELECT count(*) FROM public.ll_task_conversations AS conv
                       WHERE conv.task_id = t.id) AS started
               FROM public.ll_teacher_task_plans AS p
               JOIN public.tarea AS t ON t.id = p.task_id
               JOIN public.matera AS m ON m.id = t.id_materia
               JOIN public.curso AS c ON c.id = t.curso
               WHERE p.teacher_user_id = %s AND EXISTS (
                   SELECT 1 FROM public.ll_user_docente owner
                   JOIN public.clase_paralelo assigned ON assigned.id_docente = owner.docente_id
                   WHERE owner.user_id = %s AND assigned.id_docente = t.id_docente
                     AND assigned.id_materia = t.id_materia AND assigned.gestion = t.gestion
                     AND assigned.curso = t.curso AND assigned.paralelo = t.paralelo) ORDER BY p.created_at DESC""",
            (teacher_id, teacher_id),
        ).fetchall()
        return rows


def list_reports(teacher_id: int) -> list[dict]:
    with connect(
        _url(), label="teacher.dashboard.list_reports", connect_timeout=5, row_factory=dict_row
    ) as db:
        rows = db.execute(
            """SELECT c.task_id, c.user_id, usr.name AS student_name, t.titulo AS title,
                      c.created_at, p.completed_at, p.exercise_index, p.stage, plan.task_type,
                      GREATEST(0, floor(extract(epoch FROM
                          (COALESCE(p.completed_at, p.last_seen_at) - c.created_at)) / 60))::int
                          AS minutes_observed,
                      (SELECT count(*) FROM public.ll_task_messages AS msg
                       WHERE msg.conversation_id = c.id AND msg.role = 'student') AS messages,
                      (SELECT count(*) FROM public.ll_tutor_events AS ev
                       WHERE ev.conversation_id = c.id AND ev.kind = 'paste') AS pasted,
                      (SELECT count(*) FROM public.ll_tutor_events AS ev
                       WHERE ev.conversation_id = c.id AND ev.kind = 'tab_hidden') AS tab_hidden,
                      (SELECT count(*) FROM public.ll_tutor_events AS ev
                       WHERE ev.conversation_id = c.id AND ev.kind = 'answer_request')
                          AS answer_requests
               FROM public.ll_task_conversations AS c
               JOIN public.ll_teacher_task_plans AS plan ON plan.task_id = c.task_id
               JOIN public.tarea AS t ON t.id = c.task_id
               JOIN public.usuario AS usr ON usr.id = c.user_id
               LEFT JOIN public.ll_tutor_progress AS p ON p.conversation_id = c.id
               WHERE plan.teacher_user_id = %s AND EXISTS (
                   SELECT 1 FROM public.ll_user_docente owner
                   JOIN public.clase_paralelo assigned ON assigned.id_docente = owner.docente_id
                   WHERE owner.user_id = %s AND assigned.id_docente = t.id_docente
                     AND assigned.id_materia = t.id_materia AND assigned.gestion = t.gestion
                     AND assigned.curso = t.curso AND assigned.paralelo = t.paralelo)
               ORDER BY c.created_at DESC""",
            (teacher_id, teacher_id),
        ).fetchall()

        return [progress_view(row) for row in rows]


def get_report(teacher_id: int, task_id: int, student_id: int) -> dict | None:
    with connect(
        _url(), label="teacher.dashboard.get_report", connect_timeout=5, row_factory=dict_row
    ) as db:
        row = db.execute(
            """SELECT conv.id, conv.created_at, usr.name AS student_name,
                      t.titulo AS task_title, prog.exercise_index, prog.stage,
                      prog.completed_at, prog.last_seen_at, plan.task_type
               FROM public.ll_task_conversations AS conv
               JOIN public.ll_teacher_task_plans AS plan ON plan.task_id = conv.task_id
               JOIN public.tarea AS t ON t.id = conv.task_id
               JOIN public.usuario AS usr ON usr.id = conv.user_id
               LEFT JOIN public.ll_tutor_progress AS prog ON prog.conversation_id = conv.id
               WHERE plan.teacher_user_id = %s AND EXISTS (
                   SELECT 1 FROM public.ll_user_docente owner
                   JOIN public.clase_paralelo assigned ON assigned.id_docente = owner.docente_id
                   WHERE owner.user_id = %s AND assigned.id_docente = t.id_docente
                     AND assigned.id_materia = t.id_materia AND assigned.gestion = t.gestion
                     AND assigned.curso = t.curso AND assigned.paralelo = t.paralelo) AND conv.task_id = %s
                 AND conv.user_id = %s""",
            (teacher_id, teacher_id, task_id, student_id),
        ).fetchone()
        if not row:
            return None
        msgs = db.execute(
            """SELECT id, role, content, created_at, message_kind, reply_to_message_id, message_order FROM public.ll_task_messages
               WHERE conversation_id = %s ORDER BY created_at, message_order""",
            (row["id"],),
        ).fetchall()
        events = db.execute(
            """SELECT kind, exercise_index, created_at FROM public.ll_tutor_events
               WHERE conversation_id = %s ORDER BY created_at LIMIT 250""",
            (row["id"],),
        ).fetchall()
        return {"data": progress_view(row), "messages": order_messages(msgs), "events": events}


@timed("teacher.dashboard_load")
@reuse_connections
def load_dashboard(teacher_id: int):
    return list_classes(teacher_id), list_tasks(teacher_id), list_reports(teacher_id)
