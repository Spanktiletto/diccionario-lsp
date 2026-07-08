"""GET /api/categorias — exploración por categorías temáticas (RF03)."""

from flask import Blueprint, abort, jsonify

from ..servicios import categorias as servicio

bp = Blueprint("categorias", __name__, url_prefix="/api/categorias")


@bp.get("")
def listar():
    return jsonify(servicio.listar())


@bp.get("/<int:id_categoria>/palabras")
def palabras(id_categoria: int):
    categoria = servicio.obtener(id_categoria)
    if categoria is None:
        abort(404)
    return jsonify(
        {"categoria": categoria, "palabras": servicio.palabras_de(id_categoria)}
    )
