"""GET /api/palabras — búsqueda con autocompletado (RF01) y detalle (RF02)."""

from flask import Blueprint, abort, jsonify, request

from ..servicios import palabras as servicio

bp = Blueprint("palabras", __name__, url_prefix="/api/palabras")


@bp.get("")
def buscar():
    consulta = (request.args.get("q") or "").strip()
    if not consulta:
        return jsonify([])
    try:
        limite = int(request.args.get("limite", "10"))
    except ValueError:
        limite = 10
    limite = max(1, min(limite, 50))
    return jsonify(servicio.buscar_por_prefijo(consulta, limite))


@bp.get("/<int:id_palabra>")
def detalle(id_palabra: int):
    palabra = servicio.obtener_detalle(id_palabra)
    if palabra is None:
        abort(404)
    return jsonify(palabra)
