"""Pruebas del importador CLI (RF11): JSON, CSV, validación y upsert."""

import json

import psycopg
import pytest

from importador.cli import principal
from importador.importar_csv import cargar_registros_csv
from importador.importar_json import cargar_registros_json
from importador.modelos import desde_dict, registros_desde_lista
from importador.persistencia import guardar_registros

LOTE = [
    {
        "palabra": "casa",
        "categoria": "Hogar",
        "descripcion": "Vivienda",
        "descripcion_ejecucion": "Manos formando un techo",
        "ruta_gif": "importadas/hogar-casa.gif",
    },
    {
        "palabra": "mesa",
        "categoria": "Hogar",
        "ruta_gif": "importadas/hogar-mesa.gif",
    },
]


def _uno(url_bd: str, sql: str, parametros=None):
    with psycopg.connect(url_bd) as conexion:
        return conexion.execute(sql, parametros).fetchone()


def test_importar_json(tmp_path, url_bd):
    archivo = tmp_path / "lote.json"
    archivo.write_text(json.dumps({"senas": LOTE}), encoding="utf-8")

    registros, errores = cargar_registros_json(archivo)
    assert errores == []
    resumen = guardar_registros(registros, url_bd)
    assert resumen.insertadas == 2
    assert resumen.invalidas == 0
    assert _uno(url_bd, "SELECT COUNT(*) FROM palabra WHERE NOT es_letra")[0] == 2

    # Reimportar es idempotente: actualiza, no duplica.
    resumen2 = guardar_registros(registros, url_bd)
    assert resumen2.actualizadas == 2
    assert _uno(url_bd, "SELECT COUNT(*) FROM palabra WHERE NOT es_letra")[0] == 2


def test_json_acepta_clave_con_enie(tmp_path):
    archivo = tmp_path / "lote.json"
    archivo.write_text(json.dumps({"señas": LOTE}), encoding="utf-8")
    registros, errores = cargar_registros_json(archivo)
    assert len(registros) == 2 and errores == []


def test_json_clave_desconocida_es_error(tmp_path):
    archivo = tmp_path / "lote.json"
    archivo.write_text(json.dumps({"items": LOTE}), encoding="utf-8")
    with pytest.raises(ValueError, match="senas"):
        cargar_registros_json(archivo)


def test_importar_csv_con_punto_y_coma(tmp_path, url_bd):
    archivo = tmp_path / "lote.csv"
    archivo.write_text(
        "palabra;categoria;ruta_gif;es_estatica\n"
        "hola;Saludos;importadas/saludos-hola.gif;false\n",
        encoding="utf-8",
    )
    registros, errores = cargar_registros_csv(archivo)
    assert errores == []
    assert registros[0].es_estatica is False

    resumen = guardar_registros(registros, url_bd)
    assert resumen.insertadas == 1


def test_csv_campo_largo_entre_comillas(tmp_path):
    """La detección por cabecera no se confunde con campos enormes."""
    descripcion = "palabra con; punto y coma " * 300  # > 4096 bytes
    archivo = tmp_path / "lote.csv"
    archivo.write_text(
        "palabra;categoria;descripcion_ejecucion;ruta_gif\n"
        f'uno;Cat;"{descripcion}";x.gif\n'
        "dos;Cat;normal;y.gif\n",
        encoding="utf-8",
    )
    registros, errores = cargar_registros_csv(archivo)
    assert errores == []
    assert [r.palabra for r in registros] == ["uno", "dos"]


def test_registro_invalido_no_se_inserta(url_bd):
    registros = [desde_dict({"palabra": "", "categoria": "Hogar", "ruta_gif": "x.gif"})]
    resumen = guardar_registros(registros, url_bd)
    assert resumen.invalidas == 1
    assert resumen.insertadas == 0
    assert "palabra vacía" in resumen.errores[0]


def test_longitudes_maximas_del_esquema(url_bd):
    """--solo-validar debe predecir lo que la BD rechazaría."""
    registros = [
        desde_dict(
            {"palabra": "x" * 121, "categoria": "C", "ruta_gif": "x.gif"}
        ),
        desde_dict(
            {"palabra": "ok", "categoria": "c" * 81, "ruta_gif": "x.gif"}
        ),
    ]
    resumen = guardar_registros(registros, url_bd)
    assert resumen.invalidas == 2
    assert "supera 120" in resumen.errores[0]
    assert "supera 80" in resumen.errores[1]


def test_registro_con_error_de_bd_no_tumba_el_lote(url_bd):
    """Un fallo de BD en un registro no revierte los demás (subtransacción)."""
    valido = desde_dict(
        {"palabra": "válida", "categoria": "Mixto", "ruta_gif": "v.gif"}
    )
    # Pasa validar() pero viola el esquema: es_letra exige 1 carácter solo
    # si es_letra=true... forzamos error de BD con una palabra que colisiona
    # en el índice único tras un cambio de mayúsculas no detectado. Más
    # directo: clase_modelo válido según el modelo pero es_letra sin
    # especificar rompe la validación, así que usamos un truco real:
    # texto con byte nulo, que PostgreSQL rechaza en tiempo de ejecución.
    con_error = desde_dict(
        {"palabra": "rota\x00", "categoria": "Mixto", "ruta_gif": "r.gif"}
    )
    resumen = guardar_registros([valido, con_error], url_bd)
    assert resumen.insertadas == 1
    assert resumen.invalidas == 1
    assert "error de base de datos" in resumen.errores[0]
    # El registro válido sobrevivió al fallo del otro.
    assert _uno(url_bd, "SELECT COUNT(*) FROM palabra WHERE texto = 'válida'")[0] == 1


def test_gif_no_descargado_no_revienta_el_lote(url_bd):
    """El estado que deja resolver_gifs tras una descarga fallida
    (gif_url presente, ruta_gif vacía) se rechaza como inválido."""
    valido = desde_dict({"palabra": "bien", "categoria": "Mixto", "ruta_gif": "b.gif"})
    fallido = desde_dict(
        {"palabra": "mal", "categoria": "Mixto", "gif_url": "https://caida.pe/x.gif"}
    )
    resumen = guardar_registros([valido, fallido], url_bd)
    assert resumen.insertadas == 1
    assert resumen.invalidas == 1
    assert "GIF no descargado" in resumen.errores[0]


def test_reimporte_parcial_conserva_flags_y_clase(url_bd):
    """Actualizar solo el GIF no debe pisar es_letra/es_estatica/clase_modelo."""
    completo = desde_dict(
        {
            "palabra": "J",
            "categoria": "AlfabetoPrueba",
            "ruta_gif": "prueba/j.gif",
            "es_letra": True,
            "es_estatica": False,
        }
    )
    con_clase = desde_dict(
        {
            "palabra": "B",
            "categoria": "AlfabetoPrueba",
            "ruta_gif": "prueba/b.gif",
            "es_letra": True,
            "es_estatica": True,
            "clase_modelo": 1,
        }
    )
    assert guardar_registros([completo, con_clase], url_bd).insertadas == 2

    # Reimporte parcial: solo palabra+categoria+GIF nuevo.
    parciales = [
        desde_dict(
            {"palabra": "J", "categoria": "AlfabetoPrueba", "ruta_gif": "prueba/j2.gif"}
        ),
        desde_dict(
            {"palabra": "B", "categoria": "AlfabetoPrueba", "ruta_gif": "prueba/b2.gif"}
        ),
    ]
    assert guardar_registros(parciales, url_bd).actualizadas == 2

    fila_j = _uno(
        url_bd,
        """
        SELECT p.es_letra, p.es_estatica, s.ruta_gif
        FROM palabra p JOIN sena s USING (id_palabra)
        JOIN categoria c USING (id_categoria)
        WHERE p.texto = 'J' AND c.nombre = 'AlfabetoPrueba'
        """,
    )
    assert fila_j == (True, False, "prueba/j2.gif")  # sigue letra dinámica

    fila_b = _uno(
        url_bd,
        """
        SELECT s.clase_modelo, s.ruta_gif
        FROM palabra p JOIN sena s USING (id_palabra)
        JOIN categoria c USING (id_categoria)
        WHERE p.texto = 'B' AND c.nombre = 'AlfabetoPrueba'
        """,
    )
    assert fila_b == (1, "prueba/b2.gif")  # conserva su clase del modelo


def test_letra_exige_mayuscula_unica():
    minuscula = desde_dict(
        {"palabra": "b", "categoria": "C", "ruta_gif": "b.gif", "es_letra": True}
    )
    assert any("mayúscula" in e for e in minuscula.validar())
    frase = desde_dict(
        {"palabra": "BE", "categoria": "C", "ruta_gif": "b.gif", "es_letra": True}
    )
    assert frase.validar() != []


def test_clase_modelo_solo_en_letras_estaticas():
    palabra_normal = desde_dict(
        {"palabra": "casa", "categoria": "C", "ruta_gif": "c.gif", "clase_modelo": 5}
    )
    assert any("letras estáticas" in e for e in palabra_normal.validar())
    dinamica = desde_dict(
        {
            "palabra": "J",
            "categoria": "C",
            "ruta_gif": "j.gif",
            "es_letra": True,
            "es_estatica": False,
            "clase_modelo": 9,
        }
    )
    assert any("letras estáticas" in e for e in dinamica.validar())


def test_clase_modelo_fuera_de_rango(url_bd):
    registros = [
        desde_dict(
            {
                "palabra": "X",
                "categoria": "C",
                "ruta_gif": "x.gif",
                "es_letra": True,
                "es_estatica": True,
                "clase_modelo": 24,
            }
        )
    ]
    resumen = guardar_registros(registros, url_bd)
    assert resumen.invalidas == 1


def test_clase_modelo_no_entero_se_rechaza():
    registros, errores = registros_desde_lista(
        [{"palabra": "A", "categoria": "C", "ruta_gif": "a.gif", "clase_modelo": 3.7}]
    )
    assert registros == []
    assert len(errores) == 1 and "3.7" in errores[0]

    registros, errores = registros_desde_lista(
        [{"palabra": "A", "categoria": "C", "ruta_gif": "a.gif", "clase_modelo": True}]
    )
    assert registros == [] and "booleano" in errores[0]


def test_cli_solo_validar(tmp_path, capsys):
    archivo = tmp_path / "lote.json"
    archivo.write_text(json.dumps(LOTE), encoding="utf-8")
    codigo = principal(["importar", str(archivo), "--solo-validar"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Registros leídos: 2" in salida
    assert "2 válidos" in salida


def test_cli_lote_vacio_no_es_exito(tmp_path, capsys):
    archivo = tmp_path / "lote.json"
    archivo.write_text("[]", encoding="utf-8")
    codigo = principal(["importar", str(archivo), "--solo-validar"])
    assert codigo == 1
    assert "Advertencia" in capsys.readouterr().out


def test_cli_clave_desconocida_mensaje_claro(tmp_path, capsys):
    archivo = tmp_path / "lote.json"
    archivo.write_text(json.dumps({"items": []}), encoding="utf-8")
    codigo = principal(["importar", str(archivo), "--solo-validar"])
    assert codigo == 1
    assert "Error al leer los registros" in capsys.readouterr().out


def test_cli_archivo_inexistente():
    with pytest.raises(SystemExit):
        principal(["importar", "no-existe.json"])


def test_cli_formato_no_soportado(tmp_path):
    archivo = tmp_path / "lote.txt"
    archivo.write_text("x", encoding="utf-8")
    with pytest.raises(SystemExit):
        principal(["importar", str(archivo)])
