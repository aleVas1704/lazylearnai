"""Orquesta acceso, persistencia e invocaciones idempotentes al tutor."""

from dataclasses import dataclass
from uuid import UUID

import psycopg
from google.genai import types

from backend.core.config import database_url
from backend.modules.student_task_chat import gemini_client, prompts, repository

MAX_MESSAGE_LENGTH = 1200


class WorkspaceUnavailable(Exception):
    pass


class TaskNotFound(Exception):
    pass


class AiUnavailable(Exception):
    pass


class RateLimited(Exception):
    pass


class InvalidQuestion(Exception):
    pass


@dataclass(frozen=True)
class Workspace:
    task: dict[str, object]
    conversation: dict[str, object] | None
    messages: list[dict[str, object]]


def _url() -> str:
    url = database_url()
    if not url:
        raise WorkspaceUnavailable()
    return url


def load_workspace(profile_id: UUID, task_id: UUID) -> Workspace:
    try:
        data = repository.load_workspace(_url(), profile_id, task_id)
    except psycopg.Error:
        raise WorkspaceUnavailable() from None
    if data is None:
        raise TaskNotFound()
    return Workspace(data["task"], data["conversation"], data["messages"])


def _content(role: str, text: str) -> types.Content:
    return types.Content(role=role, parts=[types.Part.from_text(text=text)])


def start_task(profile_id: UUID, task_id: UUID) -> None:
    url = _url()
    try:
        claim = repository.claim_initial(url, profile_id, task_id)
    except psycopg.Error:
        raise WorkspaceUnavailable() from None
    if claim is None:
        raise TaskNotFound()
    if not claim["claimed"]:
        return
    conversation_id = claim["conversation_id"]
    try:
        answer = gemini_client.generate(
            [_content("user", prompts.initial_prompt(claim["task"]))],
            prompts.SYSTEM_PROMPT,
        )
        repository.complete_initial(url, conversation_id, answer)
    except (gemini_client.GeminiNotConfigured, gemini_client.GeminiUnavailable, psycopg.Error):
        try:
            repository.fail_initial(url, conversation_id)
        except psycopg.Error:
            pass
        raise AiUnavailable() from None


def ask_question(
    profile_id: UUID,
    task_id: UUID,
    request_id: UUID,
    raw_message: str,
) -> None:
    message = " ".join(raw_message.split()).strip()
    if not message or len(message) > MAX_MESSAGE_LENGTH:
        raise InvalidQuestion()
    url = _url()
    try:
        claim = repository.claim_question(url, profile_id, task_id, request_id, message)
    except psycopg.Error:
        raise WorkspaceUnavailable() from None
    if claim is None:
        raise TaskNotFound()
    if claim.get("error") == "rate_limited":
        raise RateLimited()
    if claim.get("error"):
        raise InvalidQuestion()
    if not claim["claimed"]:
        return
    conversation_id = claim["conversation_id"]
    message_id = claim["message_id"]
    try:
        history = repository.generation_history(url, conversation_id, message_id)
        while history and sum(len(item["content"]) for item in history) > 12_000:
            history.pop(0)
        contents = [
            _content("model" if item["role"] == "assistant" else "user", item["content"])
            for item in history
        ]
        contents.append(_content("user", prompts.follow_up_prompt(claim["task"], message)))
        answer = gemini_client.generate(contents, prompts.SYSTEM_PROMPT)
        repository.complete_question(url, conversation_id, message_id, answer)
    except (gemini_client.GeminiNotConfigured, gemini_client.GeminiUnavailable, psycopg.Error):
        try:
            repository.fail_question(url, message_id)
        except psycopg.Error:
            pass
        raise AiUnavailable() from None
