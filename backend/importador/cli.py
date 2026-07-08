"""CLI del importador de contenido (RF11).

Uso (desde backend/, con el venv activado):

    python -m importador importar lote.json [--solo-validar]
    python -m importador importar lote.csv  [--solo-validar]
    python -m importador sincronizar [--url URL] [--token TOKEN] [--solo-validar]
"""

import argparse
from pathlib import Path

import requests

from app.config import Config

from .descargas import resolver_gifs
from .importar_csv import cargar_registros_csv
from .importar_json import cargar_registros_json
from .persistencia import guardar_registros
from .sincronizar_api import obtener_registros_api


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="importador",
        description="Importa o sincroniza el vocabulario del Diccionario LSP "
        "sin modificar el código fuente.",
    )
    subordenes = parser.add_subparsers(dest="orden", required=True)

    importar = subordenes.add_parser("importar", help="importa un lote JSON o CSV")
    importar.add_argument("archivo", help="ruta del lote (.json o .csv)")
    importar.add_argument(
        "--solo-validar",
        action="store_true",
        help="valida el lote sin descargar GIFs ni escribir en la BD",
    )

    sincronizar = subordenes.add_parser(
        "sincronizar", help="sincroniza desde la API de señas configurada"
    )
    sincronizar.add_argument("--url", default=None, help="URL de la API de señas")
    sincronizar.add_argument("--token", default=None, help="token de acceso (Bearer)")
    sincronizar.add_argument("--solo-validar", action="store_true")
    return parser


def _cargar(argumentos) -> tuple[list, list[str]]:
    if argumentos.orden == "sincronizar":
        url = argumentos.url or Config.API_SENAS_URL
        if not url:
            raise SystemExit(
                "No hay URL de la API de señas: usa --url o define API_SENAS_URL en .env"
            )
        token = argumentos.token or Config.API_SENAS_TOKEN or None
        return obtener_registros_api(url, token)

    ruta = Path(argumentos.archivo)
    if not ruta.is_file():
        raise SystemExit(f"No existe el archivo: {ruta}")
    extension = ruta.suffix.lower()
    if extension == ".json":
        return cargar_registros_json(ruta)
    if extension == ".csv":
        return cargar_registros_csv(ruta)
    raise SystemExit(f"Formato no soportado: {extension} (use .json o .csv)")


def principal(argv=None) -> int:
    argumentos = _construir_parser().parse_args(argv)

    try:
        registros, errores_carga = _cargar(argumentos)
    except ValueError as excepcion:  # JSON/CSV malformado o clave ausente
        print(f"Error al leer los registros: {excepcion}")
        return 1
    except requests.RequestException as excepcion:
        print(f"Error al consultar la API de señas: {excepcion}")
        return 1
    except OSError as excepcion:
        print(f"Error al abrir el archivo: {excepcion}")
        return 1

    print(f"Registros leídos: {len(registros)}")
    for error in errores_carga:
        print(f"  - descartado {error}")
    if not registros:
        print(
            "Advertencia: no se leyó ningún registro; revisa el formato "
            "del archivo o la respuesta de la API."
        )
        return 1

    if argumentos.solo_validar:
        invalidos = 0
        for registro in registros:
            errores = registro.validar()
            if errores:
                invalidos += 1
                print(f"  - inválido {registro.palabra!r}: {', '.join(errores)}")
        print(f"Validación: {len(registros) - invalidos} válidos, {invalidos} inválidos")
        return 0 if not (errores_carga or invalidos) else 1

    errores_gifs = resolver_gifs(registros, Config.MEDIA_GIFS_DIR)
    for error in errores_gifs:
        print(f"  - GIF no descargado: {error}")

    resumen = guardar_registros(registros, Config.DATABASE_URL)
    print(resumen)
    return 0 if not (errores_carga or errores_gifs or resumen.errores) else 1
