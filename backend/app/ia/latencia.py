"""Registro de latencia por predicción, exportable a CSV (Capítulo V).

Columnas:
  - latencia_servidor_ms: procesamiento en el servidor (llegada del
    fotograma al handler → predicción lista). La mide esta app.
  - latencia_cliente_ms: ciclo completo captura→respuesta medido por
    el navegador con performance.now() y reportado en la petición
    siguiente ('latencia_previa_ms'); vacía si el cliente no lo envía.
    Esta columna es la que se compara con el umbral de la tesis
    (mediana ≤ 1 s, RNF02).

Privacidad: NO se registra la letra reconocida — una secuencia de
letras con marcas de tiempo permitiría reconstruir las palabras que
una persona deletreó, y eso es contenido de uso individual, no un
agregado. Solo tiempos, estado y confianza.
"""

import csv
import threading
from datetime import datetime, timezone
from pathlib import Path

CAMPOS = [
    "marca_tiempo",
    "latencia_servidor_ms",
    "latencia_cliente_ms",
    "estado",
    "confianza",
]

_candado = threading.Lock()


def registrar(
    resultado: dict,
    latencia_servidor_ms: float,
    dir_registros,
    latencia_cliente_ms: float | None = None,
) -> Path:
    """Añade una fila al CSV de latencias y devuelve su ruta."""
    ruta = Path(dir_registros) / "latencias.csv"
    with _candado:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        es_nuevo = not ruta.exists()
        with ruta.open("a", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
            if es_nuevo:
                escritor.writeheader()
            escritor.writerow(
                {
                    "marca_tiempo": datetime.now(timezone.utc).isoformat(),
                    "latencia_servidor_ms": round(latencia_servidor_ms, 2),
                    "latencia_cliente_ms": (
                        round(latencia_cliente_ms, 2)
                        if latencia_cliente_ms is not None
                        else ""
                    ),
                    "estado": resultado.get("estado", ""),
                    "confianza": resultado.get("confianza", ""),
                }
            )
    return ruta
