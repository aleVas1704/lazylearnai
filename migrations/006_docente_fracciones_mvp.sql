-- LazyLearnAI: MVP docente/matemáticas. APLICAR SOLO DESPUES DE 005.
-- No altera tablas académicas oficiales existentes ni tablas demo antiguas.
BEGIN;

CREATE TABLE IF NOT EXISTS public.ll_teacher_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES public.usuario(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS ll_teacher_sessions_exp_idx
    ON public.ll_teacher_sessions(expires_at);

CREATE TABLE IF NOT EXISTS public.ll_teacher_task_plans (
    task_id INTEGER PRIMARY KEY REFERENCES public.tarea(id) ON DELETE CASCADE,
    teacher_user_id INTEGER NOT NULL REFERENCES public.usuario(id) ON DELETE RESTRICT,
    teacher_instructions TEXT NOT NULL,
    source_filename TEXT,
    exercises JSONB NOT NULL CHECK (jsonb_typeof(exercises) = 'array'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ll_teacher_task_plans_owner_idx
    ON public.ll_teacher_task_plans(teacher_user_id);

CREATE TABLE IF NOT EXISTS public.ll_tutor_progress (
    conversation_id UUID PRIMARY KEY
        REFERENCES public.ll_task_conversations(id) ON DELETE CASCADE,
    exercise_index SMALLINT NOT NULL DEFAULT 1 CHECK (exercise_index BETWEEN 1 AND 10),
    stage VARCHAR(16) NOT NULL DEFAULT 'concept'
        CHECK (stage IN ('concept', 'mcm', 'equivalents', 'result', 'done')),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS public.ll_tutor_events (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL
        REFERENCES public.ll_task_conversations(id) ON DELETE CASCADE,
    kind VARCHAR(32) NOT NULL
        CHECK (kind IN ('paste', 'tab_hidden', 'tab_visible', 'answer_request')),
    exercise_index SMALLINT CHECK (exercise_index BETWEEN 1 AND 10),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ll_tutor_events_conversation_idx
    ON public.ll_tutor_events(conversation_id, created_at);

COMMIT;
