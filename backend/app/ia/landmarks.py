"""Extracción de landmarks (MediaPipe Hands) y normalización — MÓDULO COMPARTIDO.

Este archivo es la ÚNICA implementación del preproceso del pipeline
(tesis §4.5.1): tanto el backend (inferencia en /api/reconocer) como
los scripts de ML (captura y entrenamiento) deben usar estas mismas
funciones para que el preproceso sea idéntico bit a bit.

Los scripts de ml/scripts/ lo cargan por ruta de archivo (importlib),
por lo que este módulo NO debe importar nada del resto de la app ni
de Flask; las dependencias pesadas (cv2, mediapipe) se importan de
forma perezosa dentro de las funciones que las usan.
"""

from pathlib import Path

import numpy as np

NUM_LANDMARKS = 21
TAMANO_VECTOR = NUM_LANDMARKS * 3  # 63 características (x, y, z × 21)

# MediaPipe >= 0.10.3x eliminó la API legada mp.solutions; el detector
# de manos vive en la Tasks API (HandLandmarker) y necesita el asset
# oficial hand_landmarker.task (los mismos 21 landmarks de la tesis).
_RAIZ_PROYECTO = Path(__file__).resolve().parents[3]
RUTA_DETECTOR = _RAIZ_PROYECTO / "ml" / "modelos" / "hand_landmarker.task"

# Parámetros compartidos entre captura e inferencia: cada fotograma se
# procesa aislado (modo IMAGE), igual que los JPEG que recibe el
# servidor (coherencia captura↔inferencia).
NUM_MANOS = 1
CONFIANZA_DETECCION = 0.5


def normalizar_landmarks(landmarks) -> np.ndarray:
    """Normaliza 21 landmarks (x, y, z) al vector de 63 características.

    Tesis §4.5.1: las coordenadas se trasladan tomando la muñeca
    (landmark 0) como origen y se escalan por la distancia máxima entre
    puntos, de modo que la representación sea invariante a la posición
    de la mano en el encuadre y a su distancia a la cámara.
    """
    puntos = np.asarray(landmarks, dtype=np.float32).reshape(
        NUM_LANDMARKS, 3
    )
    puntos = puntos - puntos[0]  # muñeca como origen
    distancia_maxima = float(np.linalg.norm(puntos, axis=1).max())
    if distancia_maxima > 0:
        puntos = puntos / distancia_maxima
    return puntos.reshape(TAMANO_VECTOR)


def crear_detector():
    """Crea el detector de manos (MediaPipe HandLandmarker) compartido.

    Lanza FileNotFoundError si falta el asset hand_landmarker.task:
    se descarga una sola vez con `python ml/scripts/descargar_recursos.py`.
    """
    from mediapipe.tasks.python import BaseOptions, vision  # perezoso

    if not RUTA_DETECTOR.exists():
        raise FileNotFoundError(
            f"Falta el detector de manos {RUTA_DETECTOR}. "
            "Descárgalo una sola vez con: "
            "python ml/scripts/descargar_recursos.py"
        )
    opciones = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(RUTA_DETECTOR)),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=NUM_MANOS,
        min_hand_detection_confidence=CONFIANZA_DETECCION,
    )
    return vision.HandLandmarker.create_from_options(opciones)


def extraer_landmarks(imagen_bgr, detector) -> np.ndarray | None:
    """Extrae los 21 landmarks de la primera mano detectada, o None.

    Devuelve un arreglo (21, 3) con las coordenadas crudas de MediaPipe
    (x, y relativas al encuadre; z relativa a la muñeca). La
    normalización se aplica aparte con normalizar_landmarks().
    """
    import cv2  # perezoso
    import mediapipe as mp

    rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    imagen_mp = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    resultado = detector.detect(imagen_mp)
    if not resultado.hand_landmarks:
        return None
    mano = resultado.hand_landmarks[0]
    return np.array(
        [[punto.x, punto.y, punto.z] for punto in mano],
        dtype=np.float32,
    )
