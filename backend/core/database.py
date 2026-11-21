def ping_database(url: str) -> None:
    """Comprueba la conexión sin consultar datos de usuarios ni modificar tablas."""
    import psycopg

    with psycopg.connect(url, connect_timeout=5) as connection, connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        if cursor.fetchone() != (1,):
            raise RuntimeError("Respuesta inesperada de la base de datos")
