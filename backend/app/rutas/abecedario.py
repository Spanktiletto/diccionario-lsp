"""GET /api/abecedario — alfabeto dactilológico completo (RF04)."""

from flask import Blueprint, jsonify

from ..servicios import abecedario as servicio

bp = Blueprint("abecedario", __name__, url_prefix="/api/abecedario")


@bp.get("")
def listar():
    return jsonify(servicio.listar())
