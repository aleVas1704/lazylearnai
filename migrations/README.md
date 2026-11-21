# Migraciones

La base inicial no necesita tablas. Cuando el problema esté definido, añadir scripts SQL numerados
(`001_crear_tablas.sql`, etc.) y ejecutar con una herramienta controlada usando `DATABASE_URL_DIRECT`
si corresponde. No ejecutar migraciones automáticamente al importar FastAPI ni en cada solicitud.
Probar primero en una base o rama de Neon de ensayo.
