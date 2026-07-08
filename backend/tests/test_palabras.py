"""Pruebas de búsqueda (RF01) y detalle (RF02)."""


def test_busqueda_por_prefijo(cliente):
    respuesta = cliente.get("/api/palabras?q=a")
    assert respuesta.status_code == 200
    resultados = respuesta.get_json()
    assert [r["texto"] for r in resultados] == ["A"]
    assert resultados[0]["categoria"] == "Abecedario"


def test_busqueda_insensible_a_mayusculas(cliente):
    minuscula = cliente.get("/api/palabras?q=a").get_json()
    mayuscula = cliente.get("/api/palabras?q=A").get_json()
    assert minuscula == mayuscula


def test_busqueda_sin_consulta_devuelve_vacio(cliente):
    assert cliente.get("/api/palabras").get_json() == []
    assert cliente.get("/api/palabras?q=").get_json() == []


def test_busqueda_sin_coincidencias(cliente):
    assert cliente.get("/api/palabras?q=zzz").get_json() == []


def test_busqueda_escapa_comodines_de_like(cliente):
    # '%' y '_' no deben actuar como comodines SQL.
    assert cliente.get("/api/palabras?q=%25").get_json() == []
    assert cliente.get("/api/palabras?q=_").get_json() == []


def test_busqueda_respeta_limite(cliente):
    todos = cliente.get("/api/palabras?q=&limite=50").get_json()
    assert todos == []  # sin consulta no busca
    limitado = cliente.get("/api/palabras?q=A&limite=1").get_json()
    assert len(limitado) <= 1
    invalido = cliente.get("/api/palabras?q=a&limite=abc")
    assert invalido.status_code == 200  # límite inválido cae al valor por defecto


def test_detalle_de_letra(cliente):
    id_a = cliente.get("/api/palabras?q=a").get_json()[0]["id"]
    detalle = cliente.get(f"/api/palabras/{id_a}").get_json()
    assert detalle["texto"] == "A"
    assert detalle["es_letra"] is True
    assert detalle["es_estatica"] is True
    assert detalle["categoria"]["nombre"] == "Abecedario"
    assert detalle["sena"]["url_gif"] == "/media/gifs/abecedario/a.gif"
    assert detalle["sena"]["clase_modelo"] == 0
    assert detalle["sena"]["descripcion_ejecucion"] is None  # sin contenido inventado
    assert 1 <= len(detalle["relacionadas"]) <= 6


def test_detalle_inexistente(cliente):
    respuesta = cliente.get("/api/palabras/999999")
    assert respuesta.status_code == 404
    assert "error" in respuesta.get_json()
