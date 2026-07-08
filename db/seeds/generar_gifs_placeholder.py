"""Genera los GIFs placeholder del abecedario — SOLO DESARROLLO.

Crea en media/gifs/abecedario/ un GIF por cada una de las 27 letras,
claramente marcado como PLACEHOLDER (dos fotogramas con la marca
parpadeante "PLACEHOLDER · no es la seña real"). Los GIFs reales de
las señas llegarán por el módulo de importación (RF11); estos solo
permiten desarrollar y probar la aplicación sin inventar contenido.

Las letras estáticas y dinámicas se leen de ml/modelos/clases.json
(fuente única de verdad); el script falla si LETRAS no coincide.

Uso (desde la raíz del repositorio):
    python db/seeds/generar_gifs_placeholder.py

Requiere Pillow >= 10.1:  pip install pillow
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]

# Letra -> nombre de archivo (coincide con db/seeds/abecedario.sql)
LETRAS = {
    "A": "a.gif", "B": "b.gif", "C": "c.gif", "D": "d.gif", "E": "e.gif",
    "F": "f.gif", "G": "g.gif", "H": "h.gif", "I": "i.gif", "J": "j.gif",
    "K": "k.gif", "L": "l.gif", "M": "m.gif", "N": "n.gif", "Ñ": "enie.gif",
    "O": "o.gif", "P": "p.gif", "Q": "q.gif", "R": "r.gif", "S": "s.gif",
    "T": "t.gif", "U": "u.gif", "V": "v.gif", "W": "w.gif", "X": "x.gif",
    "Y": "y.gif", "Z": "z.gif",
}

TAMANO = 320  # px, cuadrado
COLOR_FONDO = (229, 231, 235)      # gris claro
COLOR_LETRA = (31, 41, 55)         # gris muy oscuro (contraste AA)
COLOR_MARCA = (185, 28, 28)        # rojo oscuro
DURACION_MS = 700                  # por fotograma


def _cargar_letras_dinamicas() -> set[str]:
    """Lee las letras dinámicas del mapa canónico ml/modelos/clases.json
    y valida que LETRAS cubra exactamente clases + letras_dinamicas."""
    ruta = RAIZ / "ml" / "modelos" / "clases.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    estaticas = set(datos["clases"])
    dinamicas = set(datos["letras_dinamicas"])
    esperadas = estaticas | dinamicas
    if esperadas != set(LETRAS):
        faltan = sorted(esperadas - set(LETRAS))
        sobran = sorted(set(LETRAS) - esperadas)
        raise SystemExit(
            f"LETRAS no coincide con {ruta}: faltan {faltan}, sobran {sobran}"
        )
    return dinamicas


def _fuente(tamano: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Devuelve una fuente TrueType disponible o la fuente por defecto
    escalada (Pillow >= 10.1) para que el marcado siga siendo legible."""
    candidatas = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for ruta in candidatas:
        try:
            return ImageFont.truetype(ruta, tamano)
        except OSError:
            continue
    return ImageFont.load_default(size=tamano)


def _texto_centrado(dibujo: ImageDraw.ImageDraw, xy, texto, fuente, color) -> None:
    dibujo.text(xy, texto, font=fuente, fill=color, anchor="mm")


def _fotograma(letra: str, con_marca: bool, es_dinamica: bool) -> Image.Image:
    imagen = Image.new("RGB", (TAMANO, TAMANO), COLOR_FONDO)
    dibujo = ImageDraw.Draw(imagen)
    centro = TAMANO // 2

    _texto_centrado(dibujo, (centro, centro - 10), letra, _fuente(170), COLOR_LETRA)

    if con_marca:
        _texto_centrado(dibujo, (centro, 28), "PLACEHOLDER", _fuente(30), COLOR_MARCA)
        _texto_centrado(
            dibujo, (centro, TAMANO - 46), "no es la seña real", _fuente(24), COLOR_MARCA
        )
    if es_dinamica:
        _texto_centrado(
            dibujo, (centro, TAMANO - 18), "seña con movimiento", _fuente(18), COLOR_LETRA
        )
    return imagen


def generar_todos() -> Path:
    dinamicas = _cargar_letras_dinamicas()
    destino = RAIZ / "media" / "gifs" / "abecedario"
    destino.mkdir(parents=True, exist_ok=True)

    for letra, nombre in LETRAS.items():
        es_dinamica = letra in dinamicas
        fotogramas = [
            _fotograma(letra, True, es_dinamica),
            _fotograma(letra, False, es_dinamica),
        ]
        fotogramas[0].save(
            destino / nombre,
            save_all=True,
            append_images=fotogramas[1:],
            duration=DURACION_MS,
            loop=0,  # bucle infinito (RF02)
        )
    return destino


if __name__ == "__main__":
    carpeta = generar_todos()
    print(f"{len(LETRAS)} GIFs placeholder generados en {carpeta}")
