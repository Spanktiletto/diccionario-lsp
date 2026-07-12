"""POST /api/reconocer — reconocimiento de señas por cámara (RF05/RF06).

El fotograma llega como JPEG codificado en base64 (opcionalmente como
data URI), se procesa en memoria y se descarta: nunca se persiste ni
se registra su contenido (RNF04).

Instrumentación (Capítulo V): cada predicción atendida añade una fila
al CSV de latencias con el tiempo de procesamiento EN SERVIDOR y, si
el cliente lo reporta, la latencia completa captura→respuesta del
ciclo anterior (campo opcional 'latencia_previa_ms'). El contador
agregado 'reconocimiento' (RF10) también se incrementa aquí, del lado
del servidor, sin depender del cliente.
"""

import base64
import binascii
import time

from flask import Blueprint, current_app, jsonify, request

from ..ia import latencia, predictor
from ..servicios import metricas as servicio_metricas

bp = Blueprint("reconocer", __name__, url_prefix="/api/reconocer")

# Máxima latencia de cliente plausible; valores mayores se descartan.
LATENCIA_CLIENTE_MAX_MS = 60_000


@bp.post("")
def reconocer():
    inicio = time.perf_counter()

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        datos = {}
    imagen_b64 = datos.get("imagen")
    if not isinstance(imagen_b64, str) or not imagen_b64:
        return jsonify({"error": "se requiere el campo 'imagen' (JPEG en base64)"}), 400

    # Acepta tanto base64 puro como data URI (data:image/jpeg;base64,...).
    if imagen_b64.startswith("data:"):
        _, _, imagen_b64 = imagen_b64.partition(",")

    try:
        imagen = base64.b64decode(imagen_b64, validate=True)
    except (binascii.Error, ValueError):
        return jsonify({"error": "el campo 'imagen' no es base64 válido"}), 400
    if not imagen:
        return (
            jsonify({"error": "el campo 'imagen' está vacío o el data URI es inválido"}),
            400,
        )

    try:
        resultado = predictor.predecir(imagen)
    except predictor.ModeloNoDisponible as excepcion:
        return jsonify({"error": str(excepcion)}), 503
    except ValueError as excepcion:
        # base64 válido pero no era una imagen decodificable
        return jsonify({"error": str(excepcion)}), 400

    dir_registros = current_app.config["DIR_REGISTROS"]
    latencia.registrar(
        resultado,
        latencia_servidor_ms=(time.perf_counter() - inicio) * 1000,
        dir_registros=dir_registros,
        latencia_cliente_ms=_latencia_cliente(datos),
    )
    servicio_metricas.registrar("reconocimiento", dir_registros)
    return jsonify(resultado)


def _latencia_cliente(datos: dict) -> float | None:
    """Latencia captura→respuesta del ciclo anterior medida por el navegador."""
    valor = datos.get("latencia_previa_ms")
    if (
        isinstance(valor, (int, float))
        and not isinstance(valor, bool)
        and 0 <= valor <= LATENCIA_CLIENTE_MAX_MS
    ):
        return float(valor)
    return None
