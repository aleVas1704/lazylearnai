-- DATOS EXPLÍCITOS DE DEMOSTRACIÓN. No representan asignaciones de un docente real.
-- Uso con psql, después de 001, 002 y 003:
--   psql "$env:DATABASE_URL_DIRECT" -v profile_id='UUID-DEL-PERFIL' -f migrations/demo_student_dashboard.sql
-- El perfil debe pertenecer únicamente a una identidad ficticia de la base de prueba.
BEGIN;

INSERT INTO student_demo_subjects (id, slug, name, icon_name, sort_order)
VALUES
    ('10000000-0000-4000-8000-000000000001', 'matematicas', 'Matemáticas', 'graduation-cap', 10),
    ('10000000-0000-4000-8000-000000000002', 'lenguaje', 'Lenguaje', 'book-open', 20),
    ('10000000-0000-4000-8000-000000000003', 'ciencias-sociales', 'Ciencias Sociales', 'notebook-pen', 30)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    icon_name = EXCLUDED.icon_name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE;

INSERT INTO student_demo_subject_enrollments (id, profile_id, subject_id)
SELECT md5(:'profile_id' || subject.id::text)::uuid, :'profile_id'::uuid, subject.id
FROM student_demo_subjects AS subject
WHERE subject.slug IN ('matematicas', 'lenguaje', 'ciencias-sociales')
ON CONFLICT (profile_id, subject_id) DO NOTHING;

INSERT INTO student_demo_tasks (id, subject_id, title, description, statement, is_published, is_demo)
SELECT data.id, subject.id, data.title, data.description, data.statement, TRUE, TRUE
FROM (
    VALUES
        ('20000000-0000-4000-8000-000000000001'::uuid, 'matematicas', 'Tarea Mate 1', 'Practica ecuaciones lineales aplicadas a una situación cotidiana.', 'En una librería, tres cuadernos iguales y un lápiz de Bs 4 cuestan Bs 25. Plantea una ecuación y calcula cuánto cuesta cada cuaderno.'),
        ('20000000-0000-4000-8000-000000000002'::uuid, 'matematicas', 'Tarea Mate 2', 'Compara fracciones y justifica el procedimiento.', 'Ordena de menor a mayor las fracciones 3/4, 2/3 y 5/6. Explica cómo encontraste un denominador común.'),
        ('20000000-0000-4000-8000-000000000003'::uuid, 'matematicas', 'Tarea Mate 3', 'Calcula perímetros y áreas de figuras compuestas.', 'Un patio rectangular mide 8 m de largo y 5 m de ancho. ¿Cuál es su perímetro y cuál es su área? Muestra las fórmulas.'),
        ('20000000-0000-4000-8000-000000000004'::uuid, 'lenguaje', 'Tarea Lenguaje 1', 'Identifica la idea principal de un texto breve.', 'Lee el texto entregado en clase y escribe la idea principal en una oración. Luego anota dos detalles que la apoyen.'),
        ('20000000-0000-4000-8000-000000000005'::uuid, 'lenguaje', 'Tarea Lenguaje 2', 'Practica el uso de conectores en un párrafo.', 'Redacta un párrafo de cinco oraciones sobre el cuidado del agua. Usa al menos tres conectores diferentes.'),
        ('20000000-0000-4000-8000-000000000006'::uuid, 'ciencias-sociales', 'Tarea Ciencias Sociales 1', 'Relaciona hechos históricos con sus consecuencias.', 'Elige un hecho importante de la historia de Bolivia y explica una causa y una consecuencia en un máximo de ocho oraciones.')
) AS data(id, subject_slug, title, description, statement)
JOIN student_demo_subjects AS subject ON subject.slug = data.subject_slug
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    statement = EXCLUDED.statement,
    is_published = EXCLUDED.is_published,
    is_demo = TRUE;

INSERT INTO student_demo_task_assignments (id, task_id, profile_id)
SELECT md5(task.id::text || :'profile_id')::uuid, task.id, :'profile_id'::uuid
FROM student_demo_tasks AS task
WHERE task.id IN (
    '20000000-0000-4000-8000-000000000001',
    '20000000-0000-4000-8000-000000000002',
    '20000000-0000-4000-8000-000000000003',
    '20000000-0000-4000-8000-000000000004',
    '20000000-0000-4000-8000-000000000005',
    '20000000-0000-4000-8000-000000000006'
)
ON CONFLICT (task_id, profile_id) DO NOTHING;

COMMIT;
