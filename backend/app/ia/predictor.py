"""Predicción de señas — contrato del módulo de IA.

El pipeline completo (OpenCV → MediaPipe Hands → normalización con la
muñeca como origen y escala por distancia máxima → vector de 63
características → red densa Keras 63→128→64→24 → softmax → umbral de
confianza 0.8) se integra en la etapa de IA. Esta interfaz ya define el
contrato que consume la ruta /api/reconocer, de modo que el frontend y
las pruebas pueden desarrollarse contra él.

Privacidad (RNF04): la imagen recibida vive solo en memoria durante la
predicción y se descarta; este módulo NUNCA debe persistirla.
"""


class ModeloNoDisponible(RuntimeError):
    """El modelo entrenado aún no está instalado en el servidor."""


def predecir(imagen_jpeg: bytes) -> dict:
    """Predice la letra ejecutada en el fotograma JPEG recibido.

    Devuelve uno de:
      {"estado": "ok", "letra": "A", "confianza": 0.93}
      {"estado": "sin_mano"}                         (flujo alterno 3a de CU05)
      {"estado": "no_reconocida", "confianza": 0.55} (confianza < umbral, 5a)

    Lanza ModeloNoDisponible mientras el modelo no esté entrenado e
    integrado (se implementa en la etapa del pipeline de IA).
    """
    raise ModeloNoDisponible(
        "El modelo de reconocimiento aún no está disponible en el servidor"
    )
