"""Aplicar únicamente 006, previa confirmación explícita y sin borrar tablas."""

import argparse
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations" / "006_docente_fracciones_mvp.sql"
TABLES = ("ll_teacher_sessions", "ll_teacher_task_plans", "ll_tutor_progress", "ll_tutor_events")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    opts = parser.parse_args()
    url = os.getenv("DATABASE_URL_DIRECT")
    if not url:
        raise SystemExit("Falta DATABASE_URL_DIRECT en .env")
    if not opts.apply:
        print("=== DOCENTE MVP: INSPECCIÓN SOLO LECTURA ===")
        with psycopg.connect(
            url, connect_timeout=10, options="-c default_transaction_read_only=on"
        ) as db:
            print("Base:", db.execute("SELECT current_database()").fetchone()[0])
            for table in TABLES:
                exists = db.execute(
                    "SELECT to_regclass(%s) IS NOT NULL", (f"public.{table}",)
                ).fetchone()[0]
                print(f"  {table}: {'presente' if exists else 'pendiente'}")
        print("No se modificó nada. Para aplicar: --apply")
        return
    print("ATENCIÓN: se crearán solamente cuatro tablas ll_* en la base configurada.")
    print("No altera usuarios, matrículas, tareas oficiales existentes ni tablas demo.")
    print("Ejecuta solamente sobre la rama/base Neon autorizada por tu equipo.")
    if input("Escribe APLICAR MVP DOCENTE para continuar: ").strip() != "APLICAR MVP DOCENTE":
        raise SystemExit("Cancelado: sin cambios")
    with psycopg.connect(url, connect_timeout=10, autocommit=True) as db:
        db.execute(MIGRATION.read_text(encoding="utf-8"))
    print("LISTO: tablas auxiliares del docente creadas")


if __name__ == "__main__":
    main()
