-- Ejecutar manualmente después de revisar. No modifica ejercicios ni mensajes existentes.
ALTER TABLE public.ll_teacher_task_plans
    ADD COLUMN task_type TEXT NOT NULL DEFAULT 'fraction_add_sub'
        CHECK (task_type IN ('fraction_add_sub', 'mcm')),
    ADD COLUMN publication_id UUID;
CREATE UNIQUE INDEX ll_plan_publication_idx
    ON public.ll_teacher_task_plans(teacher_user_id, publication_id);
ALTER TABLE public.ll_teacher_task_plans ADD CONSTRAINT ll_plan_count_check
    CHECK ((task_type = 'fraction_add_sub' AND jsonb_array_length(exercises) = 10)
        OR (task_type = 'mcm' AND jsonb_array_length(exercises) = 1)) NOT VALID;
ALTER TABLE public.ll_tutor_progress
    ADD COLUMN turn_token UUID,
    ADD COLUMN turn_until TIMESTAMPTZ,
    ADD COLUMN version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.ll_tutor_progress ADD CONSTRAINT ll_progress_completion_check
    CHECK ((stage = 'done') = (completed_at IS NOT NULL)) NOT VALID;
-- NOT VALID conserva filas históricas; exige consistencia en nuevas escrituras.

ALTER TABLE public.ll_task_messages ADD COLUMN message_order BIGINT GENERATED ALWAYS AS IDENTITY;
CREATE UNIQUE INDEX ll_message_order_idx ON public.ll_task_messages(message_order);

CREATE TABLE public.ll_teacher_ai_requests (
    teacher_user_id INTEGER NOT NULL REFERENCES public.usuario(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('generate', 'summary')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ll_teacher_ai_budget_idx
    ON public.ll_teacher_ai_requests(teacher_user_id, kind, created_at);
