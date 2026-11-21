"""Panel academico utilizando solamente el catalogo oficial."""

from dataclasses import dataclass

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


def load_dashboard(user_id: int, selected_slug: str | None) -> DashboardData:
    url = database_url()
    if not url:
        raise DashboardUnavailable()
    try:
        subjects, selected, tasks = repository.load_dashboard(url, user_id, selected_slug)
    except psycopg.Error:
        raise DashboardUnavailable() from None
    for item in subjects:
        if item["icon_name"] not in ALLOWED_ICONS:
            item["icon_name"] = "book-open"
    return DashboardData(subjects, selected, tasks)


def task_is_available(user_id: int, task_id: int) -> bool:
    url = database_url()
    if not url:
        raise DashboardUnavailable()
    try:
        return repository.task_is_available(url, user_id, task_id)
    except psycopg.Error:
        raise DashboardUnavailable() from None
