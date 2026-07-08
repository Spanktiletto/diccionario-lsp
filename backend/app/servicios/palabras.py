"""Búsqueda de palabras (RF01) y vista detallada (RF02)."""

from .. import db


def _escapar_like(texto: str) -> str:
    """Escapa los comodines de LIKE en la entrada del usuario."""
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def url_gif(ruta_gif: str | None) -> str | None:
    """Convierte la ruta relativa almacenada en BD en la URL pública."""
    return f"/media/gifs/{ruta_gif}" if ruta_gif else None


def buscar_por_prefijo(prefijo: str, limite: int = 10) -> list[dict]:
    """Autocompletado por prefijo, insensible a mayúsculas (índice
    LOWER + varchar_pattern_ops del esquema)."""
    patron = _escapar_like(prefijo.lower()) + "%"
    filas = db.consultar(
        """
        SELECT p.id_palabra, p.texto, c.nombre AS categoria
        FROM palabra p
        JOIN categoria c USING (id_categoria)
        WHERE LOWER(p.texto) LIKE %s
        ORDER BY p.texto
        LIMIT %s
        """,
        (patron, limite),
    )
    return [
        {"id": f["id_palabra"], "texto": f["texto"], "categoria": f["categoria"]}
        for f in filas
    ]


def obtener_detalle(id_palabra: int) -> dict | None:
    """Vista detallada: palabra + categoría + seña + relacionadas (wireframe 2)."""
    fila = db.consultar_uno(
        """
        SELECT p.id_palabra, p.texto, p.descripcion, p.es_letra, p.es_estatica,
               c.id_categoria, c.nombre AS categoria,
               s.ruta_gif, s.descripcion_ejecucion, s.clase_modelo
        FROM palabra p
        JOIN categoria c USING (id_categoria)
        LEFT JOIN sena s USING (id_palabra)
        WHERE p.id_palabra = %s
        """,
        (id_palabra,),
    )
    if fila is None:
        return None

    relacionadas = db.consultar(
        """
        SELECT id_palabra, texto FROM palabra
        WHERE id_categoria = %s AND id_palabra <> %s
        ORDER BY texto
        LIMIT 6
        """,
        (fila["id_categoria"], id_palabra),
    )

    sena = None
    if fila["ruta_gif"]:
        sena = {
            "url_gif": url_gif(fila["ruta_gif"]),
            "descripcion_ejecucion": fila["descripcion_ejecucion"],
            "clase_modelo": fila["clase_modelo"],
        }

    return {
        "id": fila["id_palabra"],
        "texto": fila["texto"],
        "descripcion": fila["descripcion"],
        "es_letra": fila["es_letra"],
        "es_estatica": fila["es_estatica"],
        "categoria": {"id": fila["id_categoria"], "nombre": fila["categoria"]},
        "sena": sena,
        "relacionadas": [
            {"id": r["id_palabra"], "texto": r["texto"]} for r in relacionadas
        ],
    }
