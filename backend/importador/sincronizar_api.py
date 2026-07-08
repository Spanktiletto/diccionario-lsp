"""Sincronización del vocabulario desde la API de señas (RF11).

La API debe responder JSON con el mismo formato de registros que los
lotes (lista u objeto {"senas": [...]}); ver importador/__init__.py.
La URL y el token se configuran en .env (API_SENAS_URL, API_SENAS_TOKEN)
o por parámetro, sin tocar el código.
"""

import requests

from .modelos import RegistroSena, registros_desde_lista


def obtener_registros_api(
    url: str, token: str | None = None
) -> tuple[list[RegistroSena], list[str]]:
    """Descarga y parsea los registros publicados por la API de señas."""
    cabeceras = {"Accept": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    respuesta = requests.get(url, headers=cabeceras, timeout=60)
    respuesta.raise_for_status()
    return registros_desde_lista(respuesta.json())
