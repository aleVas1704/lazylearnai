"""Consultas exclusivas del catalogo academico oficial de Neon."""

from psycopg.rows import dict_row

from backend.core.database import connect


# Una misma conexion para materias y tareas: evita viajes adicionales a Neon.
def load_dashboard(
    url: str, user_id: int, selected_slug: str | None
) -> tuple[list, dict | None, list]:
    with (
        connect(
            url, label="student.dashboard.load_dashboard", connect_timeout=5, row_factory=dict_row
        ) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT DISTINCT m.id, 'materia-' || m.id AS slug,
                      m.nombre AS name, 'book-open' AS icon_name
               FROM public.ll_user_estudiante AS link
               JOIN public.inscritos AS ins ON ins.id_estudiante = link.estudiante_id
               JOIN public.clase_paralelo AS clase
                 ON clase.curso = ins.curso
                AND clase.paralelo = ins.paralelo
                AND clase.gestion = ins.gestion
               JOIN public.matera AS m ON m.id = clase.id_materia
               WHERE link.user_id = %s
               ORDER BY name, m.id""",
            (user_id,),
        )
        subjects = cursor.fetchall()
        selected = next((s for s in subjects if s["slug"] == selected_slug), None)
        if selected is None and subjects:
            selected = subjects[0]
        if not selected:
            return subjects, None, []
        cursor.execute(
            """SELECT DISTINCT t.id,
                      COALESCE(NULLIF(btrim(t.titulo), ''), 'Tarea sin titulo') AS title
               FROM public.ll_user_estudiante AS link
               JOIN public.inscritos AS ins ON ins.id_estudiante = link.estudiante_id
               JOIN public.clase_paralelo AS clase
                 ON clase.curso = ins.curso
                AND clase.paralelo = ins.paralelo
                AND clase.gestion = ins.gestion
               JOIN public.tarea AS t
                 ON t.id_docente = clase.id_docente
                AND t.id_materia = clase.id_materia
                AND t.gestion = clase.gestion
                AND t.curso = clase.curso
                AND t.paralelo = clase.paralelo
               WHERE link.user_id = %s AND clase.id_materia = %s
               ORDER BY t.id""",
            (user_id, selected["id"]),
        )
        tasks = cursor.fetchall()
        return subjects, selected, tasks


def task_is_available(url: str, user_id: int, task_id: int) -> bool:
    with (
        connect(url, label="student.dashboard.task_is_available", connect_timeout=5) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SET LOCAL statement_timeout = '5s'")
        cursor.execute(
            """SELECT 1
               FROM public.ll_user_estudiante AS link
               JOIN public.inscritos AS ins ON ins.id_estudiante = link.estudiante_id
               JOIN public.clase_paralelo AS clase
                 ON clase.curso = ins.curso
                AND clase.paralelo = ins.paralelo
                AND clase.gestion = ins.gestion
               JOIN public.tarea AS t
                 ON t.id_docente = clase.id_docente
                AND t.id_materia = clase.id_materia
                AND t.gestion = clase.gestion
                AND t.curso = clase.curso
                AND t.paralelo = clase.paralelo
               WHERE link.user_id = %s AND t.id = %s LIMIT 1""",
            (user_id, task_id),
        )
        return cursor.fetchone() is not None
