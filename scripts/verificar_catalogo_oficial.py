"""Prueba SQL no destructiva de materias y tareas del alumno de prueba."""

import os
import sys
import time
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.modules.student_dashboard import repository as dashboard
from backend.modules.student_task_chat import repository as chat


def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Falta DATABASE_URL")
    with psycopg.connect(
        url, connect_timeout=10, options="-c default_transaction_read_only=on"
    ) as db:
        matches = db.execute(
            "SELECT id FROM public.usuario WHERE name = %s", ("Alex Prueba",)
        ).fetchall()
        if len(matches) != 1:
            raise SystemExit("Se esperaba exactamente un Alex Prueba")
        user_id = matches[0][0]
        teacher = db.execute(
            "SELECT id FROM public.usuario WHERE name = %s", ("Docente Prueba",)
        ).fetchone()

    print("\n=== VERIFICACION CATALOGO OFICIAL (SOLO LECTURA) ===")
    started = time.perf_counter()
    subjects, selected, tasks = dashboard.load_dashboard(url, user_id, None)
    print(f"Dashboard: {(time.perf_counter() - started) * 1000:.0f} ms")
    print("Materias:", len(subjects))
    print("Materias del alumno:", ", ".join(s["name"] for s in subjects))
    print("Tareas de la materia seleccionada:", len(tasks))
    if selected and tasks:
        task_id = tasks[0]["id"]
        started = time.perf_counter()
        item = chat.load_workspace(url, user_id, task_id)
        print(f"Detalle de tarea: {(time.perf_counter() - started) * 1000:.0f} ms")
        print("Acceso a tarea propia:", "OK" if item else "ERROR")
        if teacher:
            denied = chat.load_workspace(url, teacher[0], task_id)
            print("Aislamiento de estudiante:", "OK" if denied is None else "ERROR")
    print("No se crearon sesiones, mensajes ni tareas.")


if __name__ == "__main__":
    main()
