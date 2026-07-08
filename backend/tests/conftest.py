"""Fixtures compartidas: BD de pruebas real (PostgreSQL) + app Flask.

Requiere el PostgreSQL local en marcha (docker compose up -d): las
pruebas de integración usan la base de datos real, como exige el plan
de pruebas de la tesis (§4.8). La BD diccionario_lsp_test se recrea
desde cero en cada sesión con el schema y los seeds oficiales.
"""

from pathlib import Path

import psycopg
import pytest

from app import crear_app
from app.config import RAIZ_PROYECTO, Config


def _url_administrativa(url: str) -> str:
    """URL hacia la BD 'postgres' del mismo servidor (para CREATE DATABASE)."""
    base, _, _ = url.rpartition("/")
    return f"{base}/postgres"


def _nombre_bd(url: str) -> str:
    return url.rsplit("/", 1)[1].split("?")[0]


def _ejecutar_archivo_sql(conexion: psycopg.Connection, ruta: Path) -> None:
    """Ejecuta un archivo SQL sentencia a sentencia.

    Suficiente para schema.sql y los seeds (sin ';' embebidos en datos);
    BEGIN/COMMIT se omiten porque psycopg ya gestiona la transacción.
    """
    contenido = ruta.read_text(encoding="utf-8")
    # Primero fuera los comentarios (pueden contener ';'), luego dividir.
    sin_comentarios = "\n".join(
        linea
        for linea in contenido.splitlines()
        if not linea.lstrip().startswith("--")
    )
    for trozo in sin_comentarios.split(";"):
        sentencia = trozo.strip()
        if sentencia and sentencia.upper() not in {"BEGIN", "COMMIT"}:
            conexion.execute(sentencia)


@pytest.fixture(scope="session")
def url_bd_pruebas() -> str:
    """Crea la BD de pruebas desde cero con schema + seeds del abecedario."""
    url = Config.DATABASE_URL_TEST
    nombre = _nombre_bd(url)
    try:
        administrativa = psycopg.connect(_url_administrativa(url), autocommit=True)
    except psycopg.OperationalError as excepcion:  # pragma: no cover
        pytest.exit(
            f"No hay PostgreSQL disponible ({excepcion}). "
            "Levanta la BD local con: docker compose up -d",
            returncode=3,
        )
    with administrativa:
        administrativa.execute(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)')
        administrativa.execute(f'CREATE DATABASE "{nombre}"')

    with psycopg.connect(url) as conexion:
        _ejecutar_archivo_sql(conexion, RAIZ_PROYECTO / "db" / "schema.sql")
        _ejecutar_archivo_sql(
            conexion, RAIZ_PROYECTO / "db" / "seeds" / "abecedario.sql"
        )
        conexion.commit()
    return url


@pytest.fixture()
def url_bd(url_bd_pruebas: str):
    """URL de la BD de pruebas; al terminar limpia lo que no sea seed."""
    yield url_bd_pruebas
    with psycopg.connect(url_bd_pruebas) as conexion:
        conexion.execute(
            """
            DELETE FROM sena WHERE id_palabra IN (
                SELECT p.id_palabra FROM palabra p
                JOIN categoria c USING (id_categoria)
                WHERE c.nombre <> 'Abecedario' OR NOT p.es_letra
            )
            """
        )
        conexion.execute(
            """
            DELETE FROM palabra
            WHERE NOT es_letra OR id_categoria IN (
                SELECT id_categoria FROM categoria WHERE nombre <> 'Abecedario'
            )
            """
        )
        conexion.execute("DELETE FROM categoria WHERE nombre <> 'Abecedario'")
        conexion.commit()


@pytest.fixture()
def app(url_bd: str, tmp_path: Path):
    """Aplicación Flask contra la BD de pruebas y registros en tmp."""
    return crear_app(
        {
            "DATABASE_URL": url_bd,
            "TESTING": True,
            "DIR_REGISTROS": tmp_path / "registros",
        }
    )


@pytest.fixture()
def cliente(app):
    return app.test_client()
