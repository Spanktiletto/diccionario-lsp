"""Rutas de la API REST (JSON)."""

from flask import Flask

from . import abecedario, categorias, metricas, palabras, reconocer, salud


def registrar_blueprints(app: Flask) -> None:
    app.register_blueprint(salud.bp)
    app.register_blueprint(palabras.bp)
    app.register_blueprint(categorias.bp)
    app.register_blueprint(abecedario.bp)
    app.register_blueprint(reconocer.bp)
    app.register_blueprint(metricas.bp)
