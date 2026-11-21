-- Tablas auxiliares para usar SOLO el catalogo academico oficial.
-- No altera ninguna tabla de la estructura entregada por el companero.
-- Aplicar unicamente en la rama de DESARROLLO de Neon, con confirmacion.

CREATE TABLE IF NOT EXISTS public.ll_user_estudiante (
    user_id INTEGER PRIMARY KEY REFERENCES public.usuario(id) ON DELETE RESTRICT,
    estudiante_id INTEGER NOT NULL UNIQUE REFERENCES public.estudiante(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.ll_user_docente (
    user_id INTEGER PRIMARY KEY REFERENCES public.usuario(id) ON DELETE RESTRICT,
    docente_id INTEGER NOT NULL UNIQUE REFERENCES public.docente(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.ll_student_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.usuario(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ll_student_sessions_expires_idx
    ON public.ll_student_sessions(expires_at);

CREATE TABLE IF NOT EXISTS public.ll_task_conversations (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.usuario(id) ON DELETE RESTRICT,
    task_id INTEGER NOT NULL REFERENCES public.tarea(id) ON DELETE RESTRICT,
    initial_status VARCHAR(16) NOT NULL DEFAULT 'new'
        CHECK (initial_status IN ('new', 'pending', 'ready', 'failed')),
    initial_started_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, task_id)
);

CREATE TABLE IF NOT EXISTS public.ll_task_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL
        REFERENCES public.ll_task_conversations(id) ON DELETE CASCADE,
    role VARCHAR(16) NOT NULL CHECK (role IN ('student', 'assistant')),
    message_kind VARCHAR(16) NOT NULL CHECK (message_kind IN ('initial', 'question', 'reply')),
    status VARCHAR(16) NOT NULL DEFAULT 'complete'
        CHECK (status IN ('pending', 'answered', 'failed', 'complete')),
    content TEXT NOT NULL CHECK (char_length(content) BETWEEN 1 AND 4000),
    client_request_id UUID,
    reply_to_message_id UUID REFERENCES public.ll_task_messages(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (conversation_id, client_request_id),
    UNIQUE (reply_to_message_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ll_task_messages_one_initial_idx
    ON public.ll_task_messages(conversation_id) WHERE message_kind = 'initial';
CREATE INDEX IF NOT EXISTS ll_task_messages_conversation_created_idx
    ON public.ll_task_messages(conversation_id, created_at);
