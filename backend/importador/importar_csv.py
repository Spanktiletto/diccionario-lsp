"""Carga de lotes en formato CSV (RF11).

Acepta coma o punto y coma como delimitador (detección automática) y
tolera el BOM que añade Excel al guardar como UTF-8.
"""

import csv
from pathlib import Path

from .modelos import RegistroSena, registros_desde_lista


def cargar_registros_csv(ruta) -> tuple[list[RegistroSena], list[str]]:
    with Path(ruta).open(newline="", encoding="utf-8-sig") as archivo:
        # El delimitador se decide sobre la línea de cabecera (nombres
        # de columna sin comillas): más fiable que olfatear una muestra
        # que puede cortar un campo entrecomillado a mitad.
        cabecera = archivo.readline()
        archivo.seek(0)
        delimitador = ";" if cabecera.count(";") > cabecera.count(",") else ","
        lector = csv.DictReader(archivo, delimiter=delimitador)
        filas = list(lector)
    return registros_desde_lista(filas)
