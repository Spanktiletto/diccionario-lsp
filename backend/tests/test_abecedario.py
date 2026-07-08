"""Pruebas del abecedario dactilológico (RF04)."""

LETRAS_DINAMICAS = {"J", "Z", "Ñ"}


def test_abecedario_completo_y_ordenado(cliente):
    letras = cliente.get("/api/abecedario").get_json()
    assert len(letras) == 27
    textos = [l["letra"] for l in letras]
    assert textos == list("ABCDEFGHIJKLMN") + ["Ñ"] + list("OPQRSTUVWXYZ")


def test_letras_dinamicas_solo_consulta(cliente):
    letras = cliente.get("/api/abecedario").get_json()
    dinamicas = {l["letra"] for l in letras if not l["es_estatica"]}
    assert dinamicas == LETRAS_DINAMICAS
    for letra in letras:
        if letra["letra"] in LETRAS_DINAMICAS:
            assert letra["clase_modelo"] is None
        else:
            assert isinstance(letra["clase_modelo"], int)


def test_clases_modelo_completas(cliente):
    letras = cliente.get("/api/abecedario").get_json()
    clases = sorted(
        l["clase_modelo"] for l in letras if l["clase_modelo"] is not None
    )
    assert clases == list(range(24))


def test_todas_con_gif(cliente):
    letras = cliente.get("/api/abecedario").get_json()
    for letra in letras:
        assert letra["url_gif"].startswith("/media/gifs/abecedario/")


def test_gif_placeholder_se_sirve(cliente):
    respuesta = cliente.get("/media/gifs/abecedario/a.gif")
    assert respuesta.status_code == 200
    assert respuesta.mimetype == "image/gif"
    respuesta.close()


def test_gif_traversal_bloqueado(cliente):
    respuesta = cliente.get("/media/gifs/../../db/schema.sql")
    assert respuesta.status_code == 404
