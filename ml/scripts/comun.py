"""Utilidades comunes de los scripts de ML.

Carga el módulo compartido de landmarks POR RUTA DE ARCHIVO (sin
importar el paquete Flask del backend) y define el formato del dataset:
un CSV de vectores de landmarks etiquetados — NUNCA imágenes (ética,
Capítulo III de la tesis).
"""

import csv
import importlib.util
import json
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_LANDMARKS = RAIZ_PROYECTO / "backend" / "app" / "ia" / "landmarks.py"
RUTA_CLASES = RAIZ_PROYECTO / "ml" / "modelos" / "clases.json"
RUTA_DATASET = RAIZ_PROYECTO / "ml" / "dataset" / "landmarks.csv"
DIR_MODELOS = RAIZ_PROYECTO / "ml" / "modelos"

# Columnas del CSV: etiqueta + procedencia + 63 coordenadas crudas.
COLUMNAS_META = ["letra", "participante", "marca_tiempo"]
COLUMNAS_COORDENADAS = [
    f"lm{indice:02d}_{eje}" for indice in range(21) for eje in ("x", "y", "z")
]
COLUMNAS = COLUMNAS_META + COLUMNAS_COORDENADAS


def cargar_modulo_landmarks():
    """Importa backend/app/ia/landmarks.py sin tocar el paquete Flask."""
    especificacion = importlib.util.spec_from_file_location(
        "landmarks_compartido", RUTA_LANDMARKS
    )
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def cargar_clases() -> tuple[list[str], set[str]]:
    """Mapa canónico letra↔índice (fuente única: ml/modelos/clases.json)."""
    datos = json.loads(RUTA_CLASES.read_text(encoding="utf-8"))
    return list(datos["clases"]), set(datos["letras_dinamicas"])


def cargar_dataset(ruta=None):
    """Lee el CSV de landmarks y devuelve (X crudo, letras, participantes).

    X es un arreglo (n, 63) con las coordenadas crudas tal como salieron
    de MediaPipe; la normalización se aplica después, con el módulo
    compartido, para que entrenamiento e inferencia sean idénticos.
    """
    import numpy as np

    ruta = Path(ruta) if ruta else RUTA_DATASET
    if not ruta.is_file():
        raise SystemExit(
            f"No existe el dataset {ruta}. Captura muestras reales con "
            "ml/scripts/capturar_muestras.py"
        )
    vectores, letras, participantes = [], [], []
    with ruta.open(newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        faltantes = set(COLUMNAS) - set(lector.fieldnames or [])
        if faltantes:
            raise SystemExit(
                f"El dataset {ruta} no tiene las columnas esperadas "
                f"(faltan: {', '.join(sorted(faltantes))})"
            )
        for fila in lector:
            letras.append(fila["letra"])
            participantes.append(fila["participante"])
            vectores.append(
                [float(fila[col]) for col in COLUMNAS_COORDENADAS]
            )
    if not vectores:
        raise SystemExit(f"El dataset {ruta} está vacío")
    return np.asarray(vectores, dtype="float32"), letras, participantes
