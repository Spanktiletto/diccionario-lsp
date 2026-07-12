"""Captura de muestras del dataset (tesis §4.5.2) — herramienta del operador.

Ejecuta MediaPipe Hands sobre el video de la cámara y guarda SOLO los
vectores de landmarks etiquetados con la letra: NUNCA se almacena
ninguna imagen (consideraciones éticas del Capítulo III).

Uso (desde la raíz del repositorio, con el venv de ml/ o del backend):

    python ml/scripts/capturar_muestras.py --letra A --participante P01

Controles en la ventana:
    ESPACIO  guarda la muestra del fotograma actual
    C        activa/desactiva la captura continua (~5 muestras/s)
    ESC      termina y muestra el resumen

Por cada clase se recomiendan ≥ 300 muestras de varias personas,
variando ángulo, distancia, mano dominante e iluminación.
"""

import argparse
import csv
import sys
import time
from datetime import datetime, timezone

from comun import (
    COLUMNAS,
    RUTA_DATASET,
    cargar_clases,
    cargar_modulo_landmarks,
)

INTERVALO_CONTINUO_S = 0.2


def _preparar_csv():
    RUTA_DATASET.parent.mkdir(parents=True, exist_ok=True)
    es_nuevo = not RUTA_DATASET.exists()
    archivo = RUTA_DATASET.open("a", newline="", encoding="utf-8")
    escritor = csv.writer(archivo)
    if es_nuevo:
        escritor.writerow(COLUMNAS)
    return archivo, escritor


def _contar_muestras(letra: str) -> int:
    if not RUTA_DATASET.exists():
        return 0
    with RUTA_DATASET.open(newline="", encoding="utf-8") as archivo:
        return sum(1 for fila in csv.DictReader(archivo) if fila["letra"] == letra)


def principal() -> int:
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--letra", required=True, help="letra a capturar (A-Y, estática)")
    analizador.add_argument("--participante", required=True, help="código anónimo, p. ej. P01")
    analizador.add_argument("--camara", type=int, default=0, help="índice de la cámara (0)")
    argumentos = analizador.parse_args()

    letra = argumentos.letra.strip().upper()
    clases, dinamicas = cargar_clases()
    if letra in dinamicas:
        print(f"La letra {letra} es dinámica (J, Z, Ñ): el modelo no la reconoce; no se captura.")
        return 2
    if letra not in clases:
        print(f"Letra desconocida: {letra}. Clases válidas: {', '.join(clases)}")
        return 2

    import cv2

    landmarks = cargar_modulo_landmarks()
    detector = landmarks.crear_detector()

    camara = cv2.VideoCapture(argumentos.camara)
    if not camara.isOpened():
        print("No se pudo abrir la cámara.")
        return 1

    archivo, escritor = _preparar_csv()
    guardadas_sesion = 0
    total_previas = _contar_muestras(letra)
    continuo = False
    ultima_guardada = 0.0

    print(f"Capturando letra {letra} (participante {argumentos.participante}).")
    print(f"Muestras previas de {letra}: {total_previas}. Objetivo de la tesis: >= 300.")
    print("ESPACIO = guardar · C = captura continua · ESC = salir")

    try:
        while True:
            leido, fotograma = camara.read()
            if not leido:
                print("La cámara dejó de responder.")
                break

            puntos = landmarks.extraer_landmarks(fotograma, detector)

            # Vista para el operador (espejada solo en pantalla); los
            # landmarks se guardan del fotograma SIN espejar, igual que
            # los que recibirá el servidor.
            vista = cv2.flip(fotograma, 1)
            estado = "mano detectada" if puntos is not None else "sin mano"
            color = (0, 160, 0) if puntos is not None else (0, 0, 200)
            cv2.putText(vista, f"{letra} | {estado} | sesion: {guardadas_sesion} | total: {total_previas + guardadas_sesion}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            if continuo:
                cv2.putText(vista, "CAPTURA CONTINUA", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 120, 255), 2)
            cv2.imshow("Captura de muestras — solo landmarks, sin imagenes", vista)

            tecla = cv2.waitKey(1) & 0xFF
            ahora = time.monotonic()
            guardar = tecla == 32 or (
                continuo and ahora - ultima_guardada >= INTERVALO_CONTINUO_S
            )
            if tecla == 27:  # ESC
                break
            if tecla in (ord("c"), ord("C")):
                continuo = not continuo
            if guardar and puntos is not None:
                escritor.writerow(
                    [letra, argumentos.participante,
                     datetime.now(timezone.utc).isoformat()]
                    + [f"{valor:.6f}" for valor in puntos.reshape(63)]
                )
                guardadas_sesion += 1
                ultima_guardada = ahora
    finally:
        archivo.close()
        camara.release()
        cv2.destroyAllWindows()
        detector.close()

    total = total_previas + guardadas_sesion
    print(f"\nSesión terminada: {guardadas_sesion} muestras nuevas de {letra}.")
    print(f"Total acumulado de {letra}: {total} " + ("(objetivo alcanzado)" if total >= 300 else "(faltan para 300)"))
    print(f"Dataset: {RUTA_DATASET} — solo vectores, ninguna imagen.")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
