"""Reglas del panel: solo materias inscritas y tareas publicadas/asignadas."""

from dataclasses import dataclass
from uuid import UUID

import psycopg

from backend.core.config import database_url
from backend.modules.student_dashboard import repository

ALLOWED_ICONS = {"book-open", "graduation-cap", "notebook-pen"}


class DashboardUnavailable(Exception):
    pass


@dataclass(frozen=True)
class DashboardData:
    subjects: list[dict[str, object]]
    selected_subject: dict[str, object] | None
    tasks: list[dict[str, object]]


def load_dashboard(profile_id: UUID, selected_slug: str | None) -> DashboardData:
    url = database_url()
    if not url:
        raise DashboardUnavailable()
    try:
        subjects = repository.list_subjects(url, profile_id)
        selected = next((item for item in subjects if item["slug"] == selected_slug), None)
        if selected is None and subjects:
            selected = subjects[0]
        tasks = repository.list_tasks(url, profile_id, selected["id"]) if selected else []
    except psycopg.Error:
        raise DashboardUnavailable() from None
    for item in subjects:
        if item["icon_name"] not in ALLOWED_ICONS:
            item["icon_name"] = "book-open"
    return DashboardData(subjects, selected, tasks)


def task_is_available(profile_id: UUID, task_id: UUID) -> bool:
    url = database_url()
    if not url:
        raise DashboardUnavailable()
    try:
        return repository.task_is_available(url, profile_id, task_id)
    except psycopg.Error:
        raise DashboardUnavailable() from None
