"""Métricas de uso anónimas y AGREGADAS (RF10): solo contadores.

No se registra información personal ni identificable: ni IPs, ni
marcas de tiempo por evento, ni el contenido de las búsquedas.
Se persisten en un JSON fuera de la base de datos (el esquema de
3 tablas de la tesis no contempla métricas y no debe ampliarse).
"""

import json
import os
import threading
from pathlib import Path

EVENTOS_VALIDOS = frozenset({"busqueda", "reconocimiento"})

_candado = threading.Lock()


def _ruta(dir_registros) -> Path:
    return Path(dir_registros) / "metricas.json"


def _leer(dir_registros) -> dict:
    ruta = _ruta(dir_registros)
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def registrar(evento: str, dir_registros) -> int:
    """Incrementa el contador agregado del evento y devuelve su total."""
    if evento not in EVENTOS_VALIDOS:
        raise ValueError(f"evento desconocido: {evento!r}")
    with _candado:
        datos = _leer(dir_registros)
        datos[evento] = int(datos.get(evento, 0)) + 1
        ruta = _ruta(dir_registros)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        # Escritura atómica: si el proceso muere a mitad, el archivo
        # anterior queda intacto (metricas.json es el único almacén
        # durable de las métricas RF10 del Capítulo V).
        temporal = ruta.with_suffix(".json.tmp")
        temporal.write_text(
            json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(temporal, ruta)
        return datos[evento]


def resumen(dir_registros) -> dict:
    """Totales agregados por evento (siempre incluye todos los eventos)."""
    with _candado:
        datos = _leer(dir_registros)
    return {evento: int(datos.get(evento, 0)) for evento in sorted(EVENTOS_VALIDOS)}
