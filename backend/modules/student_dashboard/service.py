"""Panel academico utilizando solamente el catalogo oficial."""

from dataclasses import dataclass

import psycopg

from backend.core.config import database_url
from backend.core.database import reuse_connections
from backend.core.timing import timed
from backend.modules.student_access import service as access_service
from backend.modules.student_dashboard import repository

ALLOWED_ICONS = {"book-open", "graduation-cap", "notebook-pen"}


class DashboardUnavailable(Exception):
    pass


@dataclass(frozen=True)
class DashboardData:
    subjects: list[dict[str, object]]
    selected_subject: dict[str, object] | None
    tasks: list[dict[str, object]]


@timed("student.dashboard_load")
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


@timed("student.authenticated_dashboard")
@reuse_connections
def load_authenticated_dashboard(token: str | None, selected_slug: str | None):
    session = access_service.get_session(token)
    if session is None:
        return None, None
    try:
        return session, load_dashboard(session.user_id, selected_slug)
    except DashboardUnavailable:
        return session, None
