"""GET /api/salud — comprobación de estado para el despliegue."""

from flask import Blueprint, jsonify

from .. import db

bp = Blueprint("salud", __name__, url_prefix="/api/salud")


@bp.get("")
def salud():
    try:
        db.consultar_uno("SELECT 1 AS ok")
        bd_disponible = True
    except Exception:  # noqa: BLE001 — cualquier fallo de BD degrada la salud
        bd_disponible = False
    codigo = 200 if bd_disponible else 503
    return jsonify({"estado": "ok" if bd_disponible else "degradado", "bd": bd_disponible}), codigo
