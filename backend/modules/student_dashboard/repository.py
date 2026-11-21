"""Consultas parametrizadas del panel del estudiante."""

from uuid import UUID

import psycopg
from psycopg.rows import dict_row


def list_subjects(url: str, profile_id: UUID) -> list[dict[str, object]]:
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT subject.id, subject.slug, subject.name, subject.icon_name
                   FROM student_demo_subjects AS subject
                   JOIN student_demo_subject_enrollments AS enrollment
                     ON enrollment.subject_id = subject.id
                   WHERE enrollment.profile_id = %s AND subject.is_active
                   ORDER BY subject.sort_order, subject.name""",
            (profile_id,),
        )
        return cursor.fetchall()


def list_tasks(url: str, profile_id: UUID, subject_id: UUID) -> list[dict[str, object]]:
    with (
        psycopg.connect(url, connect_timeout=5, row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT task.id, task.title
                   FROM student_demo_tasks AS task
                   JOIN student_demo_task_assignments AS assignment ON assignment.task_id = task.id
                   WHERE assignment.profile_id = %s
                     AND task.subject_id = %s
                     AND task.is_published
                   ORDER BY task.created_at, task.title""",
            (profile_id, subject_id),
        )
        return cursor.fetchall()


def task_is_available(url: str, profile_id: UUID, task_id: UUID) -> bool:
    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT 1
               FROM student_demo_tasks AS task
               JOIN student_demo_task_assignments AS assignment ON assignment.task_id = task.id
               WHERE assignment.profile_id = %s AND task.id = %s AND task.is_published""",
            (profile_id, task_id),
        )
        return cursor.fetchone() is not None
