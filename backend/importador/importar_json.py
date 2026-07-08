"""Carga de lotes en formato JSON (RF11)."""

import json
from pathlib import Path

from .modelos import RegistroSena, registros_desde_lista


def cargar_registros_json(ruta) -> tuple[list[RegistroSena], list[str]]:
    """Lee un archivo JSON (lista u objeto {"senas": [...]})."""
    contenido = Path(ruta).read_text(encoding="utf-8")
    datos = json.loads(contenido)
    return registros_desde_lista(datos)
