"""Predicción de señas — pipeline de inferencia (tesis §4.5.1).

fotograma JPEG → OpenCV (decodificación) → MediaPipe Hands
(21 landmarks) → normalización (muñeca como origen, escala por
distancia máxima) → vector de 63 características → red densa Keras
63→128→64→24 → softmax → umbral de confianza 0.8.

Privacidad (RNF04): la imagen recibida vive solo en memoria durante la
predicción y se descarta; este módulo NUNCA la persiste.

El modelo y sus recursos se cargan de forma perezosa en la primera
predicción y se reutilizan. Si el modelo entrenado aún no existe (o
faltan las dependencias de IA), se lanza ModeloNoDisponible y la ruta
responde 503 sin afectar al resto del diccionario.
"""

import json
import threading

from ..config import Config
from . import landmarks as modulo_landmarks


class ModeloNoDisponible(RuntimeError):
    """El modelo entrenado aún no está instalado en el servidor."""


# Recursos cargados una sola vez; MediaPipe Hands no es seguro entre
# hilos, así que toda la predicción va detrás de un candado (suficiente
# para el ritmo de ~1 fotograma/s por visitante).
_candado = threading.Lock()
_recursos = None


def _cargar_recursos():
    """Carga modelo, clases y detector; falla con mensajes claros."""
    try:
        import cv2  # noqa: F401 — valida que la dependencia exista
        from tensorflow import keras
    except ImportError as excepcion:
        raise ModeloNoDisponible(
            "Faltan las dependencias de IA en el servidor "
            f"({excepcion.name}); instala backend/requirements.txt"
        ) from excepcion

    if not Config.RUTA_MODELO.exists():
        raise ModeloNoDisponible(
            "El modelo de reconocimiento aún no está disponible en el "
            "servidor (entrena con ml/scripts/entrenar.py)"
        )
    if not Config.RUTA_CLASES.exists():
        raise ModeloNoDisponible(
            f"No existe el mapa de clases {Config.RUTA_CLASES}"
        )

    modelo = keras.models.load_model(Config.RUTA_MODELO)
    datos_clases = json.loads(Config.RUTA_CLASES.read_text(encoding="utf-8"))
    clases = list(datos_clases["clases"])
    salidas = int(modelo.output_shape[-1])
    if salidas != len(clases):
        raise ModeloNoDisponible(
            f"El modelo tiene {salidas} salidas pero clases.json define "
            f"{len(clases)} clases: reentrena o corrige el mapa"
        )
    try:
        detector = modulo_landmarks.crear_detector()
    except FileNotFoundError as excepcion:
        raise ModeloNoDisponible(str(excepcion)) from excepcion
    return {"modelo": modelo, "clases": clases, "detector": detector}


def _obtener_recursos():
    global _recursos
    if _recursos is None:
        _recursos = _cargar_recursos()
    return _recursos


def reiniciar():
    """Descarta los recursos cargados (para tests y recarga del modelo)."""
    global _recursos
    with _candado:
        _recursos = None


def predecir(imagen_jpeg: bytes) -> dict:
    """Predice la letra ejecutada en el fotograma JPEG recibido.

    Devuelve uno de:
      {"estado": "ok", "letra": "A", "confianza": 0.93}
      {"estado": "sin_mano"}                         (flujo alterno 3a de CU05)
      {"estado": "no_reconocida", "confianza": 0.55} (confianza < umbral, 5a)

    Lanza ValueError si los bytes no son una imagen decodificable y
    ModeloNoDisponible si el modelo no está instalado.
    """
    import numpy as np

    with _candado:
        recursos = _obtener_recursos()

        import cv2

        pixeles = np.frombuffer(imagen_jpeg, dtype=np.uint8)
        imagen = cv2.imdecode(pixeles, cv2.IMREAD_COLOR)
        if imagen is None:
            raise ValueError("el campo 'imagen' no es un JPEG decodificable")

        puntos = modulo_landmarks.extraer_landmarks(
            imagen, recursos["detector"]
        )
        if puntos is None:
            return {"estado": "sin_mano"}

        vector = modulo_landmarks.normalizar_landmarks(puntos)
        probabilidades = recursos["modelo"].predict(
            vector[np.newaxis, :], verbose=0
        )[0]
        indice = int(np.argmax(probabilidades))
        confianza = float(probabilidades[indice])

        if confianza < Config.UMBRAL_CONFIANZA:
            return {"estado": "no_reconocida", "confianza": round(confianza, 4)}
        return {
            "estado": "ok",
            "letra": recursos["clases"][indice],
            "confianza": round(confianza, 4),
        }
