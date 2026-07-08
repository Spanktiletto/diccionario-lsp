"""Acceso a PostgreSQL mediante un pool de conexiones (psycopg 3)."""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None


def reiniciar_pool(url: str) -> None:
    """Abre el pool hacia `url`, cerrando el anterior si existía."""
    global _pool
    if _pool is not None:
        _pool.close()
    _pool = ConnectionPool(
        url,
        min_size=1,
        max_size=10,
        open=True,
        kwargs={"row_factory": dict_row},
    )


def conexion():
    """Conexión del pool como gestor de contexto (una transacción por bloque)."""
    return _pool.connection()


def consultar(sql: str, parametros=None) -> list[dict]:
    """Ejecuta una consulta y devuelve todas las filas como diccionarios."""
    with _pool.connection() as con:
        return con.execute(sql, parametros).fetchall()


def consultar_uno(sql: str, parametros=None) -> dict | None:
    """Ejecuta una consulta y devuelve la primera fila, o None."""
    with _pool.connection() as con:
        return con.execute(sql, parametros).fetchone()
