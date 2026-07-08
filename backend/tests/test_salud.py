"""Pruebas de GET /api/salud."""


def test_salud_ok(cliente):
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"estado": "ok", "bd": True}


def test_ruta_inexistente_devuelve_json(cliente):
    respuesta = cliente.get("/api/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.get_json() == {"error": "recurso no encontrado"}
