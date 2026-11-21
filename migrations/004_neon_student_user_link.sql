-- Integración no destructiva: enlaces entre cuentas de Neon y el perfil técnico
-- usado actualmente por el dashboard/chat. No modifica public.usuario ni sus passwords.
-- Requiere aplicar 001, 002 y 003 previamente.
BEGIN;

ALTER TABLE public.student_demo_profiles
  ADD COLUMN IF NOT EXISTS neon_user_id INTEGER;

DO $migration$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'student_demo_profiles_neon_user_fk'
      AND conrelid = 'public.student_demo_profiles'::regclass
  ) THEN
    ALTER TABLE public.student_demo_profiles
      ADD CONSTRAINT student_demo_profiles_neon_user_fk
      FOREIGN KEY (neon_user_id) REFERENCES public.usuario(id) ON DELETE RESTRICT;
  END IF;
END;
$migration$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_student_demo_profiles_neon_user
  ON public.student_demo_profiles(neon_user_id);

COMMIT;
