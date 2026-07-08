"""Modelo de datos del importador y su validación."""

from dataclasses import dataclass

# Índices válidos de clase del modelo (ml/modelos/clases.json: 24 clases).
CLASE_MODELO_MIN = 0
CLASE_MODELO_MAX = 23

# Longitudes máximas alineadas con db/schema.sql (para que --solo-validar
# sea un predictor fiable de la importación real).
LONGITUD_PALABRA = 120
LONGITUD_CATEGORIA = 80
LONGITUD_DESCRIPCION = 255
LONGITUD_DESCRIPCION_EJECUCION = 500
LONGITUD_RUTA_GIF = 255


@dataclass
class RegistroSena:
    """Un registro de contenido: palabra + categoría + seña.

    es_letra / es_estatica / clase_modelo en None significan «no
    especificado»: al insertar se aplican los valores por defecto del
    esquema (false / true / NULL) y al ACTUALIZAR una palabra existente
    se conserva su valor actual (no se pisa con el default).
    """

    palabra: str
    categoria: str
    descripcion: str | None = None
    descripcion_ejecucion: str | None = None
    ruta_gif: str | None = None
    gif_url: str | None = None
    es_letra: bool | None = None
    es_estatica: bool | None = None
    clase_modelo: int | None = None

    def validar(self) -> list[str]:
        """Devuelve la lista de errores de validación (vacía si es válido)."""
        errores = []
        if not (self.palabra or "").strip():
            errores.append("palabra vacía")
        elif len(self.palabra) > LONGITUD_PALABRA:
            errores.append(f"palabra supera {LONGITUD_PALABRA} caracteres")
        if not (self.categoria or "").strip():
            errores.append("categoría vacía")
        elif len(self.categoria) > LONGITUD_CATEGORIA:
            errores.append(f"categoría supera {LONGITUD_CATEGORIA} caracteres")
        if self.descripcion and len(self.descripcion) > LONGITUD_DESCRIPCION:
            errores.append(f"descripción supera {LONGITUD_DESCRIPCION} caracteres")
        if self.descripcion_ejecucion and len(
            self.descripcion_ejecucion
        ) > LONGITUD_DESCRIPCION_EJECUCION:
            errores.append(
                f"descripción de ejecución supera {LONGITUD_DESCRIPCION_EJECUCION} caracteres"
            )
        if self.ruta_gif and len(self.ruta_gif) > LONGITUD_RUTA_GIF:
            errores.append(f"ruta_gif supera {LONGITUD_RUTA_GIF} caracteres")
        if not self.ruta_gif and not self.gif_url:
            errores.append("se requiere ruta_gif o gif_url")
        if self.ruta_gif and self.gif_url:
            errores.append("ruta_gif y gif_url son excluyentes")
        if self.es_letra:
            texto = (self.palabra or "").strip()
            if len(texto) != 1 or texto != texto.upper():
                errores.append(
                    "es_letra exige una sola letra en mayúscula (el abecedario "
                    "se ordena por el texto exacto)"
                )
        if self.clase_modelo is not None:
            if not (CLASE_MODELO_MIN <= self.clase_modelo <= CLASE_MODELO_MAX):
                errores.append(
                    f"clase_modelo fuera de rango {CLASE_MODELO_MIN}-{CLASE_MODELO_MAX}"
                )
            if self.es_letra is not True or self.es_estatica is False:
                errores.append(
                    "clase_modelo solo aplica a letras estáticas "
                    "(es_letra=true y es_estatica=true)"
                )
        return errores


def _a_booleano_opcional(valor) -> bool | None:
    """None o '' = no especificado (no tocar al actualizar)."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() in {"true", "verdadero", "sí", "si", "1"}


def _a_clase_modelo(valor) -> int | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool):
        raise ValueError("clase_modelo debe ser un entero, no un booleano")
    if isinstance(valor, float):
        if not valor.is_integer():
            raise ValueError(f"clase_modelo no es un entero: {valor}")
        return int(valor)
    return int(valor)  # int, o cadena numérica (CSV)


def desde_dict(datos: dict) -> RegistroSena:
    """Construye un registro desde un dict (JSON o fila CSV).

    Lanza ValueError/TypeError si los tipos no son convertibles;
    la validación de negocio se hace aparte con validar().
    """
    return RegistroSena(
        palabra=str(datos.get("palabra", "")).strip(),
        categoria=str(datos.get("categoria", "")).strip(),
        descripcion=(datos.get("descripcion") or None),
        descripcion_ejecucion=(datos.get("descripcion_ejecucion") or None),
        ruta_gif=(datos.get("ruta_gif") or None),
        gif_url=(datos.get("gif_url") or None),
        es_letra=_a_booleano_opcional(datos.get("es_letra")),
        es_estatica=_a_booleano_opcional(datos.get("es_estatica")),
        clase_modelo=_a_clase_modelo(datos.get("clase_modelo")),
    )


def registros_desde_lista(datos) -> tuple[list[RegistroSena], list[str]]:
    """Convierte una lista de dicts en registros; acumula errores de parseo.

    Acepta un objeto {"senas": [...]} (o {"señas": [...]}) o una lista.
    Un objeto SIN esa clave es un error: reportarlo evita que una
    sincronización que no importó nada pase por un éxito silencioso.
    """
    if isinstance(datos, dict):
        if "senas" in datos:
            datos = datos["senas"]
        elif "señas" in datos:
            datos = datos["señas"]
        else:
            raise ValueError(
                "el objeto JSON no tiene la clave 'senas' (claves presentes: "
                + ", ".join(sorted(map(str, datos.keys())))
                + ")"
            )
    if not isinstance(datos, list):
        raise ValueError("se esperaba una lista o un objeto con la clave 'senas'")

    registros: list[RegistroSena] = []
    errores: list[str] = []
    for indice, elemento in enumerate(datos, start=1):
        if not isinstance(elemento, dict):
            errores.append(f"registro {indice}: no es un objeto")
            continue
        try:
            registros.append(desde_dict(elemento))
        except (ValueError, TypeError) as excepcion:
            errores.append(f"registro {indice}: {excepcion}")
    return registros, errores
