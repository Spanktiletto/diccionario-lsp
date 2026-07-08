"""Pruebas de POST /api/reconocer (RF05/RF06) y su instrumentación."""

import base64
import csv

from app.ia import predictor

JPEG_FALSO_B64 = base64.b64encode(b"\xff\xd8\xff\xe0contenido-jpeg").decode()


def _leer_latencias(app):
    ruta = app.config["DIR_REGISTROS"] / "latencias.csv"
    with ruta.open(encoding="utf-8") as archivo:
        return list(csv.DictReader(archivo))


def test_sin_cuerpo(cliente):
    respuesta = cliente.post("/api/reconocer", json={})
    assert respuesta.status_code == 400
    assert "imagen" in respuesta.get_json()["error"]


def test_json_no_objeto(cliente):
    # Un JSON válido que no es objeto es error del cliente (400), no 500.
    respuesta = cliente.post(
        "/api/reconocer", data='"hola"', content_type="application/json"
    )
    assert respuesta.status_code == 400


def test_imagen_no_base64(cliente):
    respuesta = cliente.post("/api/reconocer", json={"imagen": "¡no-base64!"})
    assert respuesta.status_code == 400


def test_data_uri_sin_coma(cliente):
    # partition(',') dejaría imagen vacía: debe rechazarse, no predecirse.
    respuesta = cliente.post(
        "/api/reconocer", json={"imagen": "data:image/jpeg;base64"}
    )
    assert respuesta.status_code == 400


def test_modelo_no_disponible(cliente):
    respuesta = cliente.post("/api/reconocer", json={"imagen": JPEG_FALSO_B64})
    assert respuesta.status_code == 503
    assert "modelo" in respuesta.get_json()["error"].lower()


def test_prediccion_ok_latencia_y_contador(cliente, app, monkeypatch):
    monkeypatch.setattr(
        predictor,
        "predecir",
        lambda imagen: {"estado": "ok", "letra": "A", "confianza": 0.93},
    )
    respuesta = cliente.post("/api/reconocer", json={"imagen": JPEG_FALSO_B64})
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"estado": "ok", "letra": "A", "confianza": 0.93}

    # Instrumentación obligatoria: la predicción quedó en latencias.csv.
    filas = _leer_latencias(app)
    assert len(filas) == 1
    assert filas[0]["estado"] == "ok"
    assert float(filas[0]["latencia_servidor_ms"]) >= 0
    assert filas[0]["latencia_cliente_ms"] == ""  # el cliente no la reportó
    # Privacidad: la letra reconocida NO se registra en el CSV.
    assert "letra" not in filas[0]

    # RF10: el contador 'reconocimiento' lo incrementa el servidor.
    resumen = cliente.get("/api/metricas").get_json()
    assert resumen["reconocimiento"] == 1


def test_latencia_de_cliente_reportada(cliente, app, monkeypatch):
    monkeypatch.setattr(
        predictor, "predecir", lambda imagen: {"estado": "sin_mano"}
    )
    cliente.post(
        "/api/reconocer",
        json={"imagen": JPEG_FALSO_B64, "latencia_previa_ms": 250},
    )
    filas = _leer_latencias(app)
    assert filas[0]["latencia_cliente_ms"] == "250.0"


def test_latencia_de_cliente_invalida_se_ignora(cliente, app, monkeypatch):
    monkeypatch.setattr(
        predictor, "predecir", lambda imagen: {"estado": "sin_mano"}
    )
    cliente.post(
        "/api/reconocer",
        json={"imagen": JPEG_FALSO_B64, "latencia_previa_ms": "abc"},
    )
    cliente.post(
        "/api/reconocer",
        json={"imagen": JPEG_FALSO_B64, "latencia_previa_ms": -5},
    )
    filas = _leer_latencias(app)
    assert [f["latencia_cliente_ms"] for f in filas] == ["", ""]


def test_acepta_data_uri(cliente, monkeypatch):
    monkeypatch.setattr(
        predictor, "predecir", lambda imagen: {"estado": "sin_mano"}
    )
    respuesta = cliente.post(
        "/api/reconocer",
        json={"imagen": f"data:image/jpeg;base64,{JPEG_FALSO_B64}"},
    )
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"estado": "sin_mano"}


def test_confianza_baja_no_reconocida(cliente, monkeypatch):
    monkeypatch.setattr(
        predictor,
        "predecir",
        lambda imagen: {"estado": "no_reconocida", "confianza": 0.42},
    )
    respuesta = cliente.post("/api/reconocer", json={"imagen": JPEG_FALSO_B64})
    assert respuesta.get_json()["estado"] == "no_reconocida"


def test_carga_demasiado_grande(cliente):
    enorme = "A" * (6 * 1024 * 1024)  # supera MAX_CONTENT_LENGTH (5 MB)
    respuesta = cliente.post("/api/reconocer", json={"imagen": enorme})
    assert respuesta.status_code == 413
    assert respuesta.get_json() == {"error": "carga demasiado grande"}
