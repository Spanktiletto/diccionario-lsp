"""Exploración por categorías temáticas (RF03)."""

from .. import db
from .palabras import url_gif


def listar() -> list[dict]:
    filas = db.consultar(
        """
        SELECT c.id_categoria, c.nombre, c.descripcion,
               COUNT(p.id_palabra) AS total_palabras
        FROM categoria c
        LEFT JOIN palabra p USING (id_categoria)
        GROUP BY c.id_categoria
        ORDER BY c.nombre
        """
    )
    return [
        {
            "id": f["id_categoria"],
            "nombre": f["nombre"],
            "descripcion": f["descripcion"],
            "total_palabras": f["total_palabras"],
        }
        for f in filas
    ]


def obtener(id_categoria: int) -> dict | None:
    fila = db.consultar_uno(
        "SELECT id_categoria, nombre, descripcion FROM categoria WHERE id_categoria = %s",
        (id_categoria,),
    )
    if fila is None:
        return None
    return {
        "id": fila["id_categoria"],
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
    }


def palabras_de(id_categoria: int) -> list[dict]:
    filas = db.consultar(
        """
        SELECT p.id_palabra, p.texto, p.es_letra, p.es_estatica, s.ruta_gif
        FROM palabra p
        LEFT JOIN sena s USING (id_palabra)
        WHERE p.id_categoria = %s
        ORDER BY p.texto
        """,
        (id_categoria,),
    )
    return [
        {
            "id": f["id_palabra"],
            "texto": f["texto"],
            "es_letra": f["es_letra"],
            "es_estatica": f["es_estatica"],
            "url_gif": url_gif(f["ruta_gif"]),
        }
        for f in filas
    ]
