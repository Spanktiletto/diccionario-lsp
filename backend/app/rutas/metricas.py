"""POST/GET /api/metricas — métricas anónimas agregadas (RF10).

El cliente solo puede reportar 'busqueda' (una búsqueda efectiva, no
cada tecla del autocompletado). El evento 'reconocimiento' lo cuenta
el propio servidor en POST /api/reconocer; aquí se rechaza para evitar
el doble conteo.
"""

from flask import Blueprint, current_app, jsonify, request

from ..servicios import metricas as servicio

bp = Blueprint("metricas", __name__, url_prefix="/api/metricas")

# Eventos que puede reportar el cliente (el resto los cuenta el servidor).
EVENTOS_CLIENTE = frozenset({"busqueda"})


@bp.post("")
def registrar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        datos = {}
    evento = datos.get("evento")
    if evento not in EVENTOS_CLIENTE:
        validos = ", ".join(sorted(EVENTOS_CLIENTE))
        return jsonify({"error": f"evento inválido; use uno de: {validos}"}), 400
    total = servicio.registrar(evento, current_app.config["DIR_REGISTROS"])
    return jsonify({"evento": evento, "total": total}), 201


@bp.get("")
def resumen():
    return jsonify(servicio.resumen(current_app.config["DIR_REGISTROS"]))
