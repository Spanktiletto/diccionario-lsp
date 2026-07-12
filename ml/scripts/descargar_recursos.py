"""Descarga los recursos externos del pipeline (una sola vez).

Único recurso: el detector oficial de manos de MediaPipe
(hand_landmarker.task, Apache 2.0), requerido por la Tasks API que
sustituyó a la antigua mp.solutions. No se versiona en el repositorio.

Uso (desde la raíz del repositorio):

    python ml/scripts/descargar_recursos.py
"""

import sys
import urllib.request

from comun import DIR_MODELOS

URL_DETECTOR = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
TAMANO_MINIMO = 1_000_000  # el asset real ronda los 7.8 MB


def principal() -> int:
    destino = DIR_MODELOS / "hand_landmarker.task"
    if destino.exists() and destino.stat().st_size >= TAMANO_MINIMO:
        print(f"El detector ya está en {destino} — nada que hacer.")
        return 0

    print(f"Descargando {URL_DETECTOR} …")
    temporal = destino.with_suffix(".task.tmp")
    urllib.request.urlretrieve(URL_DETECTOR, temporal)
    if temporal.stat().st_size < TAMANO_MINIMO:
        temporal.unlink(missing_ok=True)
        print("La descarga parece incompleta; inténtalo de nuevo.")
        return 1
    temporal.replace(destino)
    print(f"Detector guardado en {destino} ({destino.stat().st_size / 1e6:.1f} MB).")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
