-- Materias y tareas de la demo. Aplicar manualmente después de 001_student_access.sql.
BEGIN;

CREATE TABLE IF NOT EXISTS student_demo_subjects (
    id UUID PRIMARY KEY,
    slug VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(80) NOT NULL,
    icon_name VARCHAR(40) NOT NULL,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_demo_subject_enrollments (
    id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES student_demo_profiles(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL REFERENCES student_demo_subjects(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (profile_id, subject_id)
);

CREATE TABLE IF NOT EXISTS student_demo_tasks (
    id UUID PRIMARY KEY,
    subject_id UUID NOT NULL REFERENCES student_demo_subjects(id) ON DELETE CASCADE,
    title VARCHAR(120) NOT NULL,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    is_demo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_demo_task_assignments (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES student_demo_tasks(id) ON DELETE CASCADE,
    profile_id UUID NOT NULL REFERENCES student_demo_profiles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (task_id, profile_id)
);

CREATE INDEX IF NOT EXISTS idx_student_demo_enrollments_profile
    ON student_demo_subject_enrollments(profile_id);
CREATE INDEX IF NOT EXISTS idx_student_demo_assignments_profile
    ON student_demo_task_assignments(profile_id);
CREATE INDEX IF NOT EXISTS idx_student_demo_tasks_subject_published
    ON student_demo_tasks(subject_id, is_published);

COMMIT;
