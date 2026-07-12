"""Pruebas del módulo de IA: normalización compartida y predictor.

La normalización es matemática pura (§4.5.1) y se prueba exacta. El
predictor se prueba con un modelo Keras diminto creado al vuelo y con
la extracción de landmarks sustituida por vectores de prueba (nunca se
fabrican señas reales: son fixtures de test).
"""

import json

import numpy as np
import pytest

from app.ia import landmarks, predictor


# ── Normalización (compartida entre captura, entrenamiento e inferencia) ──


def test_normalizacion_traslada_la_muneca_al_origen():
    puntos = np.random.default_rng(7).uniform(0, 1, (21, 3)).astype("float32")
    vector = landmarks.normalizar_landmarks(puntos)
    assert vector.shape == (63,)
    assert np.allclose(vector[:3], 0.0)  # landmark 0 = muñeca = origen


def test_normalizacion_es_invariante_a_traslacion_y_escala():
    generador = np.random.default_rng(11)
    puntos = generador.uniform(0, 1, (21, 3)).astype("float32")
    desplazados = puntos + np.array([0.3, -0.2, 0.1], dtype="float32")
    escalados = puntos * 2.5

    base = landmarks.normalizar_landmarks(puntos)
    assert np.allclose(base, landmarks.normalizar_landmarks(desplazados), atol=1e-5)
    assert np.allclose(base, landmarks.normalizar_landmarks(escalados), atol=1e-5)


def test_normalizacion_escala_por_distancia_maxima():
    puntos = np.zeros((21, 3), dtype="float32")
    puntos[5] = [3.0, 4.0, 0.0]  # distancia 5 desde la muñeca
    vector = landmarks.normalizar_landmarks(puntos).reshape(21, 3)
    distancias = np.linalg.norm(vector, axis=1)
    assert distancias.max() == pytest.approx(1.0)
    assert vector[5] == pytest.approx([0.6, 0.8, 0.0])


def test_normalizacion_tolera_landmarks_degenerados():
    # Todos los puntos iguales (distancia máxima 0): no divide entre cero.
    vector = landmarks.normalizar_landmarks(np.ones((21, 3), dtype="float32"))
    assert np.allclose(vector, 0.0)


# ── Predictor: contrato de predecir() con recursos de prueba ──


def _hay_tensorflow():
    try:
        import tensorflow  # noqa: F401

        return True
    except ImportError:
        return False


requiere_tf = pytest.mark.skipif(
    not _hay_tensorflow(), reason="requiere tensorflow instalado"
)


@pytest.fixture()
def recursos_de_prueba(tmp_path, monkeypatch):
    """Modelo diminuto real + clases reales + detector sustituido."""
    from tensorflow import keras

    clases = json.loads(
        (predictor.Config.RUTA_CLASES).read_text(encoding="utf-8")
    )["clases"]

    modelo = keras.Sequential(
        [
            keras.layers.Input(shape=(63,)),
            keras.layers.Dense(len(clases), activation="softmax"),
        ]
    )
    ruta_modelo = tmp_path / "modelo.keras"
    modelo.save(ruta_modelo)

    monkeypatch.setattr(predictor.Config, "RUTA_MODELO", ruta_modelo)
    predictor.reiniciar()
    # El detector real necesita cámara/mediapipe: se sustituye por un
    # doble que controlamos por test (los vectores son fixtures, no
    # señas reales).
    monkeypatch.setattr(
        landmarks, "crear_detector", lambda: object(), raising=True
    )
    yield clases
    predictor.reiniciar()


def _jpeg_negro() -> bytes:
    """Un JPEG real y diminuto (imagen negra), garantizado decodificable."""
    import cv2

    _, codificado = cv2.imencode(".jpg", np.zeros((8, 8, 3), dtype=np.uint8))
    return codificado.tobytes()


@requiere_tf
def test_predecir_sin_mano(monkeypatch, recursos_de_prueba):
    monkeypatch.setattr(
        landmarks, "extraer_landmarks", lambda imagen, detector: None
    )
    assert predictor.predecir(_jpeg_negro()) == {"estado": "sin_mano"}


@requiere_tf
def test_predecir_devuelve_letra_o_no_reconocida(
    monkeypatch, recursos_de_prueba
):
    puntos = np.random.default_rng(3).uniform(0, 1, (21, 3)).astype("float32")
    monkeypatch.setattr(
        landmarks, "extraer_landmarks", lambda imagen, detector: puntos
    )
    resultado = predictor.predecir(_jpeg_negro())
    # Con un modelo sin entrenar la confianza ronda 1/24: el contrato
    # exige el flujo alterno 5a de CU05.
    assert resultado["estado"] in {"ok", "no_reconocida"}
    if resultado["estado"] == "ok":
        assert resultado["letra"] in recursos_de_prueba
        assert resultado["confianza"] >= 0.8
    else:
        assert 0.0 <= resultado["confianza"] < 0.8


@requiere_tf
def test_predecir_respeta_el_umbral_de_confianza(
    monkeypatch, recursos_de_prueba
):
    puntos = np.random.default_rng(5).uniform(0, 1, (21, 3)).astype("float32")
    monkeypatch.setattr(
        landmarks, "extraer_landmarks", lambda imagen, detector: puntos
    )
    monkeypatch.setattr(predictor.Config, "UMBRAL_CONFIANZA", 0.0)
    con_umbral_cero = predictor.predecir(_jpeg_negro())
    assert con_umbral_cero["estado"] == "ok"

    monkeypatch.setattr(predictor.Config, "UMBRAL_CONFIANZA", 1.01)
    imposible = predictor.predecir(_jpeg_negro())
    assert imposible["estado"] == "no_reconocida"


@requiere_tf
def test_predecir_rechaza_bytes_que_no_son_imagen(recursos_de_prueba):
    with pytest.raises(ValueError):
        predictor.predecir(b"esto no es un jpeg")


@requiere_tf
def test_bytes_invalidos_devuelven_400_en_la_ruta(
    cliente, monkeypatch, recursos_de_prueba
):
    import base64

    respuesta = cliente.post(
        "/api/reconocer",
        json={"imagen": base64.b64encode(b"no soy jpeg").decode()},
    )
    assert respuesta.status_code == 400
    assert "imagen" in respuesta.get_json()["error"]


def test_sin_modelo_hay_503(cliente, monkeypatch, tmp_path):
    """Sin modelo entrenado el endpoint degrada con 503 (contrato v1)."""
    import base64

    monkeypatch.setattr(
        predictor.Config, "RUTA_MODELO", tmp_path / "no-existe.keras"
    )
    predictor.reiniciar()
    respuesta = cliente.post(
        "/api/reconocer",
        json={"imagen": base64.b64encode(b"da igual").decode()},
    )
    predictor.reiniciar()
    assert respuesta.status_code == 503
    assert "modelo" in respuesta.get_json()["error"].lower()
