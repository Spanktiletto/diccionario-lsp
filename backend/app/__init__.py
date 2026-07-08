"""Fábrica de la aplicación Flask del Diccionario LSP.

Aplicación pública: sin usuarios, sin autenticación, sin sesiones.
"""

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from . import db
from .config import Config
from .rutas import registrar_blueprints


def crear_app(config_extra: dict | None = None) -> Flask:
    """Crea y configura la aplicación (config_extra permite overrides en tests)."""
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_extra:
        app.config.update(config_extra)

    # API pública de solo lectura/contadores: CORS abierto, sin credenciales.
    CORS(app, resources={r"/api/*": {"origins": "*"}, r"/media/*": {"origins": "*"}})

    db.reiniciar_pool(app.config["DATABASE_URL"])
    registrar_blueprints(app)

    @app.get("/media/gifs/<path:ruta>")
    def servir_gif(ruta: str):
        # send_from_directory previene el path traversal.
        return send_from_directory(app.config["MEDIA_GIFS_DIR"], ruta, max_age=86400)

    _registrar_errores(app)
    return app


def _registrar_errores(app: Flask) -> None:
    """Errores siempre en JSON, coherentes con la API."""

    def json_error(codigo: int, mensaje: str):
        return jsonify({"error": mensaje}), codigo

    app.register_error_handler(400, lambda e: json_error(400, "petición inválida"))
    app.register_error_handler(404, lambda e: json_error(404, "recurso no encontrado"))
    app.register_error_handler(405, lambda e: json_error(405, "método no permitido"))
    app.register_error_handler(413, lambda e: json_error(413, "carga demasiado grande"))
    app.register_error_handler(500, lambda e: json_error(500, "error interno del servidor"))


# Alias para la CLI de Flask (`flask --app app run`), que solo
# autodetecta los nombres create_app/make_app.
create_app = crear_app
