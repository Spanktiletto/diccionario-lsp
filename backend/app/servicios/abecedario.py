"""Abecedario dactilológico completo (RF04): 27 letras, 24 reconocibles."""

from .. import db
from .palabras import url_gif

# Orden alfabético español (la collation de la BD pondría la Ñ tras la Z).
ORDEN_ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"


def listar() -> list[dict]:
    filas = db.consultar(
        """
        SELECT p.id_palabra, p.texto AS letra, p.es_estatica,
               s.ruta_gif, s.clase_modelo
        FROM palabra p
        JOIN sena s USING (id_palabra)
        WHERE p.es_letra
        -- strpos = 0 (texto fuera del alfabeto) va al final, no antes
        -- de la 'A'; p.texto desempata de forma determinista.
        ORDER BY NULLIF(strpos(%s, p.texto), 0) NULLS LAST, p.texto
        """,
        (ORDEN_ALFABETO,),
    )
    return [
        {
            "id": f["id_palabra"],
            "letra": f["letra"],
            "es_estatica": f["es_estatica"],
            "url_gif": url_gif(f["ruta_gif"]),
            "clase_modelo": f["clase_modelo"],
        }
        for f in filas
    ]
