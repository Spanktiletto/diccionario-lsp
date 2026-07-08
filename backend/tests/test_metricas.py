"""Pruebas de métricas anónimas agregadas (RF10)."""

import json


def test_registrar_busqueda(cliente):
    primera = cliente.post("/api/metricas", json={"evento": "busqueda"})
    assert primera.status_code == 201
    assert primera.get_json() == {"evento": "busqueda", "total": 1}

    segunda = cliente.post("/api/metricas", json={"evento": "busqueda"})
    assert segunda.get_json()["total"] == 2


def test_evento_invalido(cliente):
    assert cliente.post("/api/metricas", json={"evento": "clic"}).status_code == 400
    assert cliente.post("/api/metricas", json={}).status_code == 400


def test_reconocimiento_no_lo_reporta_el_cliente(cliente):
    """El servidor cuenta 'reconocimiento' en /api/reconocer; reportarlo
    por aquí duplicaría el conteo, así que se rechaza."""
    respuesta = cliente.post("/api/metricas", json={"evento": "reconocimiento"})
    assert respuesta.status_code == 400


def test_json_no_objeto(cliente):
    respuesta = cliente.post(
        "/api/metricas", data="[1, 2]", content_type="application/json"
    )
    assert respuesta.status_code == 400


def test_resumen(cliente):
    cliente.post("/api/metricas", json={"evento": "busqueda"})
    resumen = cliente.get("/api/metricas").get_json()
    assert resumen == {"busqueda": 1, "reconocimiento": 0}


def test_sin_datos_personales_en_archivo(cliente, app):
    """RNF/RF10: el archivo de métricas solo contiene contadores."""
    cliente.post("/api/metricas", json={"evento": "busqueda"})
    contenido = json.loads(
        (app.config["DIR_REGISTROS"] / "metricas.json").read_text(encoding="utf-8")
    )
    assert set(contenido) <= {"busqueda", "reconocimiento"}
    assert all(isinstance(v, int) for v in contenido.values())
