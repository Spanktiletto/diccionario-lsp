"""Entrenamiento del clasificador de señas estáticas (tesis §4.5.3).

Red densa 63→128→64→24: ReLU, dropout 0.3/0.2, softmax; Adam
(lr = 0.001), entropía cruzada categórica, lotes de 32, hasta 100
épocas con parada temprana según la pérdida de validación. Partición
estratificada 70/15/15 y aumento de datos en entrenamiento (ruido
gaussiano leve y rotaciones pequeñas sobre los landmarks, §4.5.2).

Uso (desde la raíz del repositorio):

    python ml/scripts/entrenar.py [--dataset ml/dataset/landmarks.csv]
        [--epocas 100] [--semilla 42] [--sin-aumento]
        [--salida ml/modelos/modelo.keras]

Guarda junto al modelo:
  - particiones.json   índices exactos train/val/test (los usa evaluar.py)
  - entrenamiento.json metadatos para el Capítulo V (reproducibilidad)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from comun import (
    DIR_MODELOS,
    cargar_clases,
    cargar_dataset,
    cargar_modulo_landmarks,
)

# Hiperparámetros fijados por la tesis (§4.5.3).
CAPA_1 = 128
CAPA_2 = 64
DROPOUT_1 = 0.3
DROPOUT_2 = 0.2
TASA_APRENDIZAJE = 0.001
TAMANO_LOTE = 32
EPOCAS_MAXIMAS = 100
PACIENCIA = 10

# Aumento de datos (§4.5.2): perturbaciones leves.
COPIAS_AUMENTO = 2
SIGMA_RUIDO = 0.01
ROTACION_MAX_GRADOS = 10.0


def _particionar(y, semilla):
    """Partición estratificada 70/15/15 por índices."""
    from sklearn.model_selection import train_test_split

    indices = list(range(len(y)))
    entrena, resto = train_test_split(
        indices, test_size=0.30, random_state=semilla, stratify=[y[i] for i in indices]
    )
    valida, prueba = train_test_split(
        resto, test_size=0.50, random_state=semilla, stratify=[y[i] for i in resto]
    )
    return entrena, valida, prueba


def _aumentar(x, y, semilla):
    """Ruido gaussiano leve y rotaciones pequeñas en el plano XY.

    La rotación se aplica alrededor del origen (la muñeca, tras la
    normalización) y preserva la escala; el ruido se añade después.
    """
    import numpy as np

    generador = np.random.default_rng(semilla)
    aumentadas_x, aumentadas_y = [x], [y]
    for _ in range(COPIAS_AUMENTO):
        angulos = generador.uniform(
            -np.radians(ROTACION_MAX_GRADOS),
            np.radians(ROTACION_MAX_GRADOS),
            size=len(x),
        )
        puntos = x.reshape(len(x), 21, 3).copy()
        cosenos, senos = np.cos(angulos), np.sin(angulos)
        equis = puntos[:, :, 0].copy()
        yes = puntos[:, :, 1].copy()
        puntos[:, :, 0] = cosenos[:, None] * equis - senos[:, None] * yes
        puntos[:, :, 1] = senos[:, None] * equis + cosenos[:, None] * yes
        copia = puntos.reshape(len(x), 63)
        copia = copia + generador.normal(0.0, SIGMA_RUIDO, copia.shape)
        aumentadas_x.append(copia.astype("float32"))
        aumentadas_y.append(y)
    return np.concatenate(aumentadas_x), np.concatenate(aumentadas_y)


def _construir_modelo(num_clases):
    from tensorflow import keras

    return keras.Sequential(
        [
            keras.layers.Input(shape=(63,)),
            keras.layers.Dense(CAPA_1, activation="relu"),
            keras.layers.Dropout(DROPOUT_1),
            keras.layers.Dense(CAPA_2, activation="relu"),
            keras.layers.Dropout(DROPOUT_2),
            keras.layers.Dense(num_clases, activation="softmax"),
        ]
    )


def principal() -> int:
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--dataset", default=None)
    analizador.add_argument("--epocas", type=int, default=EPOCAS_MAXIMAS)
    analizador.add_argument("--semilla", type=int, default=42)
    analizador.add_argument("--sin-aumento", action="store_true")
    analizador.add_argument("--salida", default=str(DIR_MODELOS / "modelo.keras"))
    argumentos = analizador.parse_args()

    import numpy as np

    clases, dinamicas = cargar_clases()
    landmarks = cargar_modulo_landmarks()
    x_crudo, letras, _ = cargar_dataset(argumentos.dataset)

    desconocidas = sorted(set(letras) - set(clases))
    if desconocidas:
        raise SystemExit(
            "El dataset contiene letras fuera de las 24 clases estáticas: "
            + ", ".join(desconocidas)
            + (". Recuerda que J, Z y Ñ son dinámicas." if set(desconocidas) & dinamicas else "")
        )
    ausentes = sorted(set(clases) - set(letras))
    if ausentes:
        raise SystemExit(
            "Faltan muestras de estas clases (la salida softmax de 24 "
            "neuronas exige las 24): " + ", ".join(ausentes)
        )

    # Preproceso idéntico a la inferencia: módulo compartido.
    x = np.stack([landmarks.normalizar_landmarks(fila) for fila in x_crudo])
    y = np.array([clases.index(letra) for letra in letras])

    conteos = {letra: letras.count(letra) for letra in clases}
    escasas = {letra: n for letra, n in conteos.items() if n < 300}
    if escasas:
        print("AVISO: clases con menos de 300 muestras (objetivo §4.5.2):")
        for letra, cuenta in sorted(escasas.items()):
            print(f"  {letra}: {cuenta}")

    indices_entrena, indices_valida, indices_prueba = _particionar(
        y, argumentos.semilla
    )
    x_entrena, y_entrena = x[indices_entrena], y[indices_entrena]
    x_valida, y_valida = x[indices_valida], y[indices_valida]

    if not argumentos.sin_aumento:
        x_entrena, y_entrena = _aumentar(x_entrena, y_entrena, argumentos.semilla)

    from tensorflow import keras

    keras.utils.set_random_seed(argumentos.semilla)
    modelo = _construir_modelo(len(clases))
    modelo.compile(
        optimizer=keras.optimizers.Adam(learning_rate=TASA_APRENDIZAJE),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    parada = keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=PACIENCIA, restore_best_weights=True
    )
    historia = modelo.fit(
        x_entrena,
        keras.utils.to_categorical(y_entrena, len(clases)),
        validation_data=(
            x_valida,
            keras.utils.to_categorical(y_valida, len(clases)),
        ),
        epochs=argumentos.epocas,
        batch_size=TAMANO_LOTE,
        callbacks=[parada],
        verbose=2,
    )

    ruta_salida = Path(argumentos.salida)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    modelo.save(ruta_salida)

    # Los metadatos viven junto al modelo (permite entrenar a un
    # directorio alternativo sin tocar ml/modelos/).
    dir_metadatos = ruta_salida.parent
    (dir_metadatos / "particiones.json").write_text(
        json.dumps(
            {
                "semilla": argumentos.semilla,
                "dataset": str(argumentos.dataset or "ml/dataset/landmarks.csv"),
                "total_muestras": int(len(y)),
                "entrenamiento": [int(i) for i in indices_entrena],
                "validacion": [int(i) for i in indices_valida],
                "prueba": [int(i) for i in indices_prueba],
            }
        ),
        encoding="utf-8",
    )

    epocas_ejecutadas = len(historia.history["loss"])
    mejor_val = float(min(historia.history["val_loss"]))
    val_accuracy = float(max(historia.history["val_accuracy"]))
    (dir_metadatos / "entrenamiento.json").write_text(
        json.dumps(
            {
                "fecha": datetime.now(timezone.utc).isoformat(),
                "arquitectura": "63-128-64-24 (ReLU, dropout 0.3/0.2, softmax)",
                "optimizador": f"Adam lr={TASA_APRENDIZAJE}",
                "perdida": "categorical_crossentropy",
                "tamano_lote": TAMANO_LOTE,
                "epocas_maximas": argumentos.epocas,
                "epocas_ejecutadas": epocas_ejecutadas,
                "paciencia": PACIENCIA,
                "aumento_de_datos": not argumentos.sin_aumento,
                "semilla": argumentos.semilla,
                "muestras_por_clase": conteos,
                "mejor_val_loss": round(mejor_val, 4),
                "mejor_val_accuracy": round(val_accuracy, 4),
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"\nModelo guardado en {ruta_salida}")
    print(f"Épocas ejecutadas: {epocas_ejecutadas} · mejor val_accuracy: {val_accuracy:.4f}")
    print("Evalúa sobre el conjunto de prueba con: python ml/scripts/evaluar.py")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
