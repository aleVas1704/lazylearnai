-- Contenido de tareas y conversaciones del tutor. Aplicar manualmente después de 002.
BEGIN;

ALTER TABLE student_demo_tasks
    ADD COLUMN IF NOT EXISTS description TEXT NOT NULL DEFAULT '';
ALTER TABLE student_demo_tasks
    ADD COLUMN IF NOT EXISTS statement TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS student_task_conversations (
    id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES student_demo_profiles(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES student_demo_tasks(id) ON DELETE CASCADE,
    initial_status VARCHAR(16) NOT NULL DEFAULT 'new'
        CHECK (initial_status IN ('new', 'pending', 'ready', 'failed')),
    initial_started_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (profile_id, task_id)
);

CREATE TABLE IF NOT EXISTS student_task_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL
        REFERENCES student_task_conversations(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL CHECK (role IN ('student', 'assistant')),
    message_kind VARCHAR(16) NOT NULL CHECK (message_kind IN ('initial', 'question', 'reply')),
    status VARCHAR(16) NOT NULL DEFAULT 'complete'
        CHECK (status IN ('pending', 'answered', 'failed', 'complete')),
    content TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 4000),
    client_request_id UUID,
    reply_to_message_id UUID REFERENCES student_task_messages(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, client_request_id),
    UNIQUE (reply_to_message_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_task_messages_one_initial
    ON student_task_messages(conversation_id)
    WHERE message_kind = 'initial';
CREATE INDEX IF NOT EXISTS idx_student_task_messages_conversation_created
    ON student_task_messages(conversation_id, created_at);

COMMIT;
