"""Escritura de registros validados en PostgreSQL.

Cada registro se procesa en su propia subtransacción: un registro que
falle (validación o error de BD) se cuenta como inválido y NO revierte
los demás. El upsert es idempotente y conserva los campos no
especificados del registro (ver RegistroSena).
"""

from dataclasses import dataclass, field

import psycopg

from .modelos import RegistroSena


@dataclass
class Resumen:
    """Resultado de una importación."""

    insertadas: int = 0
    actualizadas: int = 0
    invalidas: int = 0
    errores: list[str] = field(default_factory=list)

    def __str__(self) -> str:  # informe legible para la CLI
        lineas = [
            f"Palabras insertadas:   {self.insertadas}",
            f"Palabras actualizadas: {self.actualizadas}",
            f"Registros inválidos:   {self.invalidas}",
        ]
        lineas.extend(f"  - {error}" for error in self.errores)
        return "\n".join(lineas)


def guardar_registros(registros: list[RegistroSena], url_bd: str) -> Resumen:
    resumen = Resumen()
    with psycopg.connect(url_bd) as conexion:
        for registro in registros:
            errores = registro.validar()
            if not errores and not registro.ruta_gif:
                # resolver_gifs no pudo descargar su gif_url: sin GIF no
                # hay seña que insertar (sena.ruta_gif es NOT NULL).
                errores = ["GIF no descargado (gif_url sin resolver)"]
            if errores:
                resumen.invalidas += 1
                resumen.errores.append(
                    f"{registro.palabra or '(sin palabra)'}: {', '.join(errores)}"
                )
                continue
            try:
                with conexion.transaction():
                    accion = _guardar_uno(conexion, registro)
            except psycopg.Error as excepcion:
                resumen.invalidas += 1
                resumen.errores.append(
                    f"{registro.palabra}: error de base de datos: {excepcion}"
                )
                continue
            if accion == "insertada":
                resumen.insertadas += 1
            else:
                resumen.actualizadas += 1
    return resumen


def _guardar_uno(conexion: psycopg.Connection, registro: RegistroSena) -> str:
    """Upsert de un registro; devuelve 'insertada' o 'actualizada'."""
    fila = conexion.execute(
        """
        INSERT INTO categoria (nombre) VALUES (%s)
        ON CONFLICT (nombre) DO NOTHING
        RETURNING id_categoria
        """,
        (registro.categoria,),
    ).fetchone()
    if fila is None:
        fila = conexion.execute(
            "SELECT id_categoria FROM categoria WHERE nombre = %s",
            (registro.categoria,),
        ).fetchone()
    id_categoria = fila[0]

    existente = conexion.execute(
        "SELECT id_palabra FROM palabra WHERE texto = %s AND id_categoria = %s",
        (registro.palabra, id_categoria),
    ).fetchone()

    if existente:
        id_palabra = existente[0]
        # COALESCE: los campos no especificados (None) conservan su
        # valor actual — reimportar solo el GIF de la letra J no debe
        # volverla estática ni sacarla del abecedario.
        conexion.execute(
            """
            UPDATE palabra
            SET descripcion = COALESCE(%s, descripcion),
                es_letra = COALESCE(%s, es_letra),
                es_estatica = COALESCE(%s, es_estatica)
            WHERE id_palabra = %s
            """,
            (
                registro.descripcion,
                registro.es_letra,
                registro.es_estatica,
                id_palabra,
            ),
        )
        accion = "actualizada"
    else:
        id_palabra = conexion.execute(
            """
            INSERT INTO palabra (texto, descripcion, id_categoria, es_letra, es_estatica)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id_palabra
            """,
            (
                registro.palabra,
                registro.descripcion,
                id_categoria,
                registro.es_letra if registro.es_letra is not None else False,
                registro.es_estatica if registro.es_estatica is not None else True,
            ),
        ).fetchone()[0]
        accion = "insertada"

    conexion.execute(
        """
        INSERT INTO sena (id_palabra, ruta_gif, descripcion_ejecucion, clase_modelo)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id_palabra) DO UPDATE
        SET ruta_gif = EXCLUDED.ruta_gif,
            descripcion_ejecucion = COALESCE(
                EXCLUDED.descripcion_ejecucion, sena.descripcion_ejecucion
            ),
            clase_modelo = COALESCE(EXCLUDED.clase_modelo, sena.clase_modelo)
        """,
        (
            id_palabra,
            registro.ruta_gif,
            registro.descripcion_ejecucion,
            registro.clase_modelo,
        ),
    )
    return accion
