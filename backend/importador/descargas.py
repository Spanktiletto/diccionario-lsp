"""Descarga de GIFs referenciados por URL, con validación del formato.

Robustez: descarga en streaming con tope de tamaño y validación
temprana de la cabecera GIF, para que una API comprometida o mal
configurada no pueda agotar la memoria de la máquina que importa.
"""

import re
import unicodedata
from pathlib import Path

import requests

CABECERAS_GIF = (b"GIF87a", b"GIF89a")
SUBDIRECTORIO = "importadas"
LIMITE_BYTES = 10 * 1024 * 1024  # 10 MB por GIF
_TROZO = 64 * 1024


def _slug(texto: str) -> str:
    """Nombre de archivo seguro: minúsculas, ASCII, guiones."""
    normalizado = unicodedata.normalize("NFKD", texto)
    ascii_plano = normalizado.encode("ascii", "ignore").decode("ascii")
    limpio = re.sub(r"[^a-z0-9]+", "-", ascii_plano.lower()).strip("-")
    return limpio or "sin-nombre"


def descargar_gif(url: str, dir_media: Path, nombre_archivo: str) -> str:
    """Descarga un GIF y devuelve su ruta relativa a media/gifs/.

    Valida la cabecera (GIF87a/GIF89a) en cuanto llegan los primeros
    bytes y aborta si el contenido supera LIMITE_BYTES. Lanza
    requests.RequestException o ValueError.
    """
    contenido = bytearray()
    with requests.get(url, timeout=30, stream=True) as respuesta:
        respuesta.raise_for_status()
        for trozo in respuesta.iter_content(chunk_size=_TROZO):
            contenido.extend(trozo)
            if len(contenido) >= 6 and bytes(contenido[:6]) not in CABECERAS_GIF:
                raise ValueError(f"el contenido de {url} no es un GIF válido")
            if len(contenido) > LIMITE_BYTES:
                raise ValueError(
                    f"{url} supera el límite de {LIMITE_BYTES // (1024 * 1024)} MB"
                )
    if len(contenido) < 6:
        raise ValueError(f"el contenido de {url} no es un GIF válido")

    destino = Path(dir_media) / SUBDIRECTORIO
    destino.mkdir(parents=True, exist_ok=True)
    (destino / nombre_archivo).write_bytes(bytes(contenido))
    return f"{SUBDIRECTORIO}/{nombre_archivo}"


def resolver_gifs(registros, dir_media: Path) -> list[str]:
    """Descarga el GIF de cada registro con gif_url y fija su ruta_gif.

    Los nombres se desambiguan dentro de la ejecución: 'mamá' y 'mama'
    en la misma categoría generan archivos distintos en vez de
    sobrescribirse en silencio.

    Devuelve los errores de descarga; los registros fallidos conservan
    gif_url y sin ruta_gif, y la persistencia los rechaza como
    inválidos (no se insertan señas sin GIF).
    """
    errores = []
    usados: set[str] = set()
    for registro in registros:
        if not registro.gif_url or registro.ruta_gif:
            continue
        base = _slug(f"{registro.categoria}-{registro.palabra}")
        nombre = f"{base}.gif"
        contador = 2
        while nombre in usados:
            nombre = f"{base}-{contador}.gif"
            contador += 1
        try:
            registro.ruta_gif = descargar_gif(registro.gif_url, dir_media, nombre)
            registro.gif_url = None
            usados.add(nombre)
        except (requests.RequestException, ValueError, OSError) as excepcion:
            errores.append(f"{registro.palabra}: {excepcion}")
    return errores
