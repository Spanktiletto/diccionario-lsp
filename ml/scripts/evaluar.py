"""Evaluación del modelo sobre el conjunto de prueba (Capítulo V).

Calcula accuracy, F1 macro y precision/recall por clase, y genera la
matriz de confusión en PNG. Usa EXACTAMENTE los índices de prueba que
registró el entrenamiento (ml/modelos/particiones.json), de modo que
los resultados del Capítulo V sean reproducibles.

Umbrales objetivo de la tesis: accuracy >= 0.90 y F1 macro >= 0.90.

Uso (desde la raíz del repositorio):

    python ml/scripts/evaluar.py [--dataset ml/dataset/landmarks.csv]
        [--modelo ml/modelos/modelo.keras]
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

OBJETIVO_ACCURACY = 0.90
OBJETIVO_F1 = 0.90


def _matriz_png(matriz, clases, ruta: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")  # sin interfaz gráfica
    import matplotlib.pyplot as plt

    figura, ejes = plt.subplots(figsize=(11, 9))
    imagen = ejes.imshow(matriz, cmap="Blues")
    figura.colorbar(imagen, ax=ejes, label="muestras")
    ejes.set_xticks(range(len(clases)), clases)
    ejes.set_yticks(range(len(clases)), clases)
    ejes.set_xlabel("Letra predicha")
    ejes.set_ylabel("Letra real")
    ejes.set_title("Matriz de confusión — conjunto de prueba")
    umbral_color = matriz.max() / 2 if matriz.max() else 0
    for fila in range(len(clases)):
        for columna in range(len(clases)):
            valor = int(matriz[fila, columna])
            if valor:
                ejes.text(
                    columna,
                    fila,
                    valor,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white" if matriz[fila, columna] > umbral_color else "black",
                )
    figura.tight_layout()
    figura.savefig(ruta, dpi=150)
    plt.close(figura)


def principal() -> int:
    analizador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analizador.add_argument("--dataset", default=None)
    analizador.add_argument("--modelo", default=str(DIR_MODELOS / "modelo.keras"))
    argumentos = analizador.parse_args()

    import numpy as np
    from sklearn.metrics import (
        accuracy_score,
        confusion_matrix,
        f1_score,
        precision_recall_fscore_support,
    )
    from tensorflow import keras

    ruta_modelo = Path(argumentos.modelo)
    if not ruta_modelo.exists():
        raise SystemExit(
            f"No existe el modelo {ruta_modelo}: entrena primero con "
            "ml/scripts/entrenar.py"
        )
    # Los metadatos y los informes viven junto al modelo.
    dir_metadatos = ruta_modelo.parent
    ruta_particiones = dir_metadatos / "particiones.json"
    if not ruta_particiones.exists():
        raise SystemExit(
            f"No existe {ruta_particiones} (lo genera entrenar.py); "
            "sin él no se puede reconstruir el conjunto de prueba exacto"
        )

    clases, _ = cargar_clases()
    landmarks = cargar_modulo_landmarks()
    x_crudo, letras, _ = cargar_dataset(argumentos.dataset)

    particiones = json.loads(ruta_particiones.read_text(encoding="utf-8"))
    if particiones["total_muestras"] != len(letras):
        raise SystemExit(
            f"El dataset tiene {len(letras)} muestras pero las particiones "
            f"se registraron con {particiones['total_muestras']}: reentrena "
            "para regenerar particiones coherentes"
        )
    indices_prueba = particiones["prueba"]

    x = np.stack(
        [landmarks.normalizar_landmarks(x_crudo[i]) for i in indices_prueba]
    )
    y_real = np.array([clases.index(letras[i]) for i in indices_prueba])

    modelo = keras.models.load_model(ruta_modelo)
    probabilidades = modelo.predict(x, verbose=0)
    y_predicha = probabilidades.argmax(axis=1)

    exactitud = accuracy_score(y_real, y_predicha)
    f1_macro = f1_score(y_real, y_predicha, average="macro")
    precision, cobertura, f1_clase, soporte = precision_recall_fscore_support(
        y_real, y_predicha, labels=range(len(clases)), zero_division=0
    )
    matriz = confusion_matrix(y_real, y_predicha, labels=range(len(clases)))

    print(f"Conjunto de prueba: {len(y_real)} muestras")
    print(f"Accuracy: {exactitud:.4f}  (objetivo >= {OBJETIVO_ACCURACY})")
    print(f"F1 macro: {f1_macro:.4f}  (objetivo >= {OBJETIVO_F1})")
    print("\nLetra  Precision  Recall  F1      Muestras")
    for indice, letra in enumerate(clases):
        print(
            f"{letra:5}  {precision[indice]:9.4f}  {cobertura[indice]:6.4f}"
            f"  {f1_clase[indice]:6.4f}  {int(soporte[indice]):8d}"
        )

    ruta_png = dir_metadatos / "matriz_confusion.png"
    _matriz_png(matriz, clases, ruta_png)

    resultado = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "modelo": str(ruta_modelo),
        "muestras_prueba": int(len(y_real)),
        "accuracy": round(float(exactitud), 4),
        "f1_macro": round(float(f1_macro), 4),
        "objetivos": {
            "accuracy": OBJETIVO_ACCURACY,
            "f1_macro": OBJETIVO_F1,
            "cumplidos": bool(
                exactitud >= OBJETIVO_ACCURACY and f1_macro >= OBJETIVO_F1
            ),
        },
        "por_clase": {
            letra: {
                "precision": round(float(precision[i]), 4),
                "recall": round(float(cobertura[i]), 4),
                "f1": round(float(f1_clase[i]), 4),
                "muestras": int(soporte[i]),
            }
            for i, letra in enumerate(clases)
        },
        "matriz_confusion": matriz.tolist(),
    }
    ruta_json = dir_metadatos / "evaluacion.json"
    ruta_json.write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nMatriz de confusión: {ruta_png}")
    print(f"Informe completo:    {ruta_json}")
    if resultado["objetivos"]["cumplidos"]:
        print("Objetivos de la tesis CUMPLIDOS (accuracy y F1 >= 0.90).")
        return 0
    print("Objetivos de la tesis AÚN NO alcanzados: revisa dataset y entrenamiento.")
    return 1


if __name__ == "__main__":
    sys.exit(principal())
