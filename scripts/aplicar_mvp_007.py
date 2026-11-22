"""Inspeccionar/aplicar 007 manualmente; nunca se ejecuta en arranque o build."""

import argparse
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION = "APLICAR 007 EN DESARROLLO"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    opts = parser.parse_args()
    url = os.environ.get("DATABASE_URL_DIRECT") or os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("Falta la conexión en el entorno local. No compartas su valor.")
    if opts.apply and input(f"Escribe {CONFIRMATION}: ").strip() != CONFIRMATION:
        raise SystemExit("Cancelado. Sin cambios.")
    try:
        with psycopg.connect(
            url,
            connect_timeout=10,
            options="" if opts.apply else "-c default_transaction_read_only=on",
        ) as db:
            db.execute("SET LOCAL lock_timeout = '5s'")
            db.execute("SET LOCAL statement_timeout = '30s'")
            columns = db.execute("""SELECT table_name, column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND
                (table_name, column_name) IN
                (('ll_teacher_task_plans','task_type'), ('ll_teacher_task_plans','publication_id'),
                 ('ll_tutor_progress','turn_token'), ('ll_tutor_progress','turn_until'),
                 ('ll_tutor_progress','version'), ('ll_task_messages','message_order'))""").fetchall()
            if not opts.apply:
                print(f"Inspección solo lectura: {len(columns)}/6 columnas de 007 presentes.")
                print("No se consultaron mensajes, nombres ni credenciales.")
            elif columns:
                raise SystemExit(
                    "007 está aplicada o parcialmente presente. Revisar esquema; no se ejecutó SQL."
                )
            else:
                db.execute(
                    (ROOT / "migrations/007_topic_validators.sql").read_text(encoding="utf-8-sig")
                )
                print("007 aplicada en una transacción. No se editaron ejercicios ni mensajes.")
    except psycopg.Error:
        raise SystemExit(
            "No se pudo completar la operación. Transacción revertida; revisa conexión y esquema localmente."
        ) from None


if __name__ == "__main__":
    main()
