"""Configuración del backend, leída del entorno (.env en la raíz del repo)."""

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIR_BACKEND = RAIZ_PROYECTO / "backend"

load_dotenv(RAIZ_PROYECTO / ".env")


def _ruta(variable: str, por_defecto: Path) -> Path:
    """Resuelve una ruta del entorno; las relativas lo son a backend/."""
    valor = os.getenv(variable, "")
    if not valor:
        return por_defecto
    ruta = Path(valor)
    return ruta if ruta.is_absolute() else (DIR_BACKEND / ruta).resolve()


def _url_bd_pruebas(url: str) -> str:
    """Deriva la URL de la BD de pruebas añadiendo el sufijo _test."""
    base, _, nombre = url.rpartition("/")
    return f"{base}/{nombre.split('?')[0]}_test"


class Config:
    """Valores de configuración; Flask los carga con from_object."""

    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://lsp:lsp_dev@localhost:5433/diccionario_lsp"
    )
    DATABASE_URL_TEST = os.getenv("DATABASE_URL_TEST", _url_bd_pruebas(DATABASE_URL))

    # Módulo de IA (tesis: umbral de confianza 0.8)
    UMBRAL_CONFIANZA = float(os.getenv("UMBRAL_CONFIANZA", "0.8"))
    RUTA_MODELO = _ruta("RUTA_MODELO", RAIZ_PROYECTO / "ml" / "modelos" / "modelo.keras")
    RUTA_CLASES = _ruta("RUTA_CLASES", RAIZ_PROYECTO / "ml" / "modelos" / "clases.json")

    # Medios estáticos (la BD guarda rutas relativas a este directorio)
    MEDIA_GIFS_DIR = _ruta("MEDIA_GIFS_DIR", RAIZ_PROYECTO / "media" / "gifs")

    # Salidas de instrumentación (latencias CSV, métricas agregadas)
    DIR_REGISTROS = DIR_BACKEND / "registros"

    # Importador (RF11)
    API_SENAS_URL = os.getenv("API_SENAS_URL", "")
    API_SENAS_TOKEN = os.getenv("API_SENAS_TOKEN", "")

    # Límite defensivo para los fotogramas JPEG en base64 (RNF02/RNF04)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
