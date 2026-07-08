"""Pruebas de sincronización desde la API de señas (RF11), sin red real."""

import psycopg

from importador import descargas, sincronizar_api
from importador.descargas import resolver_gifs
from importador.persistencia import guardar_registros

GIF_MINIMO = b"GIF89a" + b"\x00" * 20


class _RespuestaFalsa:
    def __init__(self, json_datos=None, contenido=b""):
        self._json = json_datos
        self.content = contenido

    def raise_for_status(self):
        pass

    def json(self):
        return self._json

    def iter_content(self, chunk_size):
        for inicio in range(0, len(self.content), chunk_size):
            yield self.content[inicio : inicio + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *argumentos):
        return False


def test_sincronizacion_completa(monkeypatch, tmp_path, url_bd):
    """Flujo completo: API → registros → descarga de GIF → upsert en BD."""
    carga = {
        "senas": [
            {
                "palabra": "gracias",
                "categoria": "Saludos",
                "gif_url": "https://api.ejemplo.pe/gifs/gracias.gif",
            }
        ]
    }

    def get_falso(url, **kwargs):
        if url.endswith(".gif"):
            return _RespuestaFalsa(contenido=GIF_MINIMO)
        return _RespuestaFalsa(json_datos=carga)

    monkeypatch.setattr(sincronizar_api.requests, "get", get_falso)
    monkeypatch.setattr(descargas.requests, "get", get_falso)

    registros, errores = sincronizar_api.obtener_registros_api(
        "https://api.ejemplo.pe/senas", token="secreto"
    )
    assert errores == []
    assert len(registros) == 1

    errores_gif = resolver_gifs(registros, tmp_path)
    assert errores_gif == []
    assert registros[0].ruta_gif == "importadas/saludos-gracias.gif"
    assert (tmp_path / "importadas" / "saludos-gracias.gif").read_bytes() == GIF_MINIMO

    resumen = guardar_registros(registros, url_bd)
    assert resumen.insertadas == 1
    with psycopg.connect(url_bd) as conexion:
        ruta = conexion.execute(
            "SELECT s.ruta_gif FROM sena s JOIN palabra p USING (id_palabra) "
            "WHERE p.texto = 'gracias'"
        ).fetchone()[0]
    assert ruta == "importadas/saludos-gracias.gif"


def test_descarga_rechaza_contenido_no_gif(monkeypatch, tmp_path, url_bd):
    monkeypatch.setattr(
        descargas.requests,
        "get",
        lambda url, **kwargs: _RespuestaFalsa(contenido=b"<html>no soy un gif</html>"),
    )
    from importador.modelos import desde_dict

    registro = desde_dict(
        {"palabra": "x", "categoria": "C", "gif_url": "https://malo.pe/x.gif"}
    )
    errores = resolver_gifs([registro], tmp_path)
    assert len(errores) == 1
    assert registro.ruta_gif is None
    # Y la persistencia lo rechaza en vez de reventar el lote.
    resumen = guardar_registros([registro], url_bd)
    assert resumen.invalidas == 1
    assert "GIF no descargado" in resumen.errores[0]


def test_slugs_en_colision_no_se_sobrescriben(monkeypatch, tmp_path):
    """'mamá' y 'mama' en la misma categoría reciben archivos distintos."""
    from importador.modelos import desde_dict

    contenidos = {
        "https://api.pe/mama-con-tilde.gif": b"GIF89a" + b"\x01" * 10,
        "https://api.pe/mama-sin-tilde.gif": b"GIF89a" + b"\x02" * 10,
    }
    monkeypatch.setattr(
        descargas.requests,
        "get",
        lambda url, **kwargs: _RespuestaFalsa(contenido=contenidos[url]),
    )
    con_tilde = desde_dict(
        {"palabra": "mamá", "categoria": "Familia", "gif_url": "https://api.pe/mama-con-tilde.gif"}
    )
    sin_tilde = desde_dict(
        {"palabra": "mama", "categoria": "Familia", "gif_url": "https://api.pe/mama-sin-tilde.gif"}
    )
    errores = resolver_gifs([con_tilde, sin_tilde], tmp_path)
    assert errores == []
    assert con_tilde.ruta_gif != sin_tilde.ruta_gif
    assert (tmp_path / con_tilde.ruta_gif).read_bytes() != (
        tmp_path / sin_tilde.ruta_gif
    ).read_bytes()


def test_descarga_respeta_limite_de_tamano(monkeypatch, tmp_path):
    from importador.modelos import desde_dict

    class _RespuestaGrande:
        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            yield b"GIF89a"
            for _ in range(200):
                yield b"\x00" * (64 * 1024)  # ~12.5 MB en total

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        descargas.requests, "get", lambda url, **kwargs: _RespuestaGrande()
    )
    registro = desde_dict(
        {"palabra": "enorme", "categoria": "C", "gif_url": "https://api.pe/e.gif"}
    )
    errores = resolver_gifs([registro], tmp_path)
    assert len(errores) == 1 and "límite" in errores[0]
    assert registro.ruta_gif is None


def test_slug_sanitiza_nombres():
    assert descargas._slug("Ñandú / Ñoño") == "nandu-nono"
    assert descargas._slug("../../peligro") == "peligro"
    assert descargas._slug("") == "sin-nombre"
