"""Pruebas de exploración por categorías (RF03)."""


def test_listar_categorias(cliente):
    categorias = cliente.get("/api/categorias").get_json()
    assert len(categorias) == 1
    abecedario = categorias[0]
    assert abecedario["nombre"] == "Abecedario"
    assert abecedario["total_palabras"] == 27


def test_palabras_de_categoria(cliente):
    id_categoria = cliente.get("/api/categorias").get_json()[0]["id"]
    respuesta = cliente.get(f"/api/categorias/{id_categoria}/palabras").get_json()
    assert respuesta["categoria"]["nombre"] == "Abecedario"
    assert len(respuesta["palabras"]) == 27
    primera = respuesta["palabras"][0]
    assert primera["url_gif"].startswith("/media/gifs/abecedario/")


def test_categoria_inexistente(cliente):
    assert cliente.get("/api/categorias/999999/palabras").status_code == 404
