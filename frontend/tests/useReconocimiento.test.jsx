import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import useReconocimiento from "../src/hooks/useReconocimiento.js";

vi.mock("../src/servicios/api.js", () => ({
  reconocerFotograma: vi.fn(),
}));

import { reconocerFotograma } from "../src/servicios/api.js";

function crearFlujoFalso() {
  const pista = { stop: vi.fn() };
  return { flujo: { getTracks: () => [pista] }, pista };
}

function crearVideoFalso() {
  const video = document.createElement("video");
  Object.defineProperty(video, "videoWidth", { value: 480 });
  Object.defineProperty(video, "videoHeight", { value: 360 });
  video.play = vi.fn().mockResolvedValue(undefined);
  return video;
}

function instalarCamara(getUserMedia) {
  Object.defineProperty(navigator, "mediaDevices", {
    value: { getUserMedia },
    configurable: true,
  });
}

async function avanzarCiclo() {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(1000);
  });
}

beforeEach(() => {
  // performance.now también se congela: la ventana de repetición (2 s)
  // debe medirse en tiempo simulado.
  vi.useFakeTimers({
    toFake: [
      "setTimeout",
      "setInterval",
      "clearTimeout",
      "clearInterval",
      "performance",
    ],
  });
  HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
    drawImage: vi.fn(),
  }));
  HTMLCanvasElement.prototype.toDataURL = vi.fn(
    () => "data:image/jpeg;base64,AAA",
  );
});

afterEach(() => {
  vi.useRealTimers();
  vi.clearAllMocks();
  delete navigator.mediaDevices;
});

async function montarYArrancar() {
  const { flujo, pista } = crearFlujoFalso();
  instalarCamara(vi.fn().mockResolvedValue(flujo));
  const montado = renderHook(() => useReconocimiento());
  montado.result.current.referenciaVideo.current = crearVideoFalso();
  await act(async () => {
    await montado.result.current.iniciar();
  });
  return { ...montado, pista };
}

describe("useReconocimiento (RF05–RF07)", () => {
  it("clics repetidos en Iniciar no abren la cámara dos veces", async () => {
    const { flujo } = crearFlujoFalso();
    let resolver;
    const pendiente = new Promise((res) => {
      resolver = res;
    });
    const getUserMedia = vi.fn(() => pendiente);
    instalarCamara(getUserMedia);

    const { result } = renderHook(() => useReconocimiento());
    result.current.referenciaVideo.current = crearVideoFalso();
    await act(async () => {
      result.current.iniciar(); // el permiso sigue pendiente…
      result.current.iniciar(); // …y el segundo clic debe ignorarse
      resolver(flujo);
      await pendiente;
    });
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    expect(result.current.activo).toBe(true);
  });

  it("agrega la letra reconocida una sola vez aunque el gesto se sostenga", async () => {
    const { result } = await montarYArrancar();
    const respuestaA = { estado: "ok", letra: "A", confianza: 0.95 };
    reconocerFotograma
      .mockResolvedValueOnce(respuestaA)
      .mockResolvedValueOnce(respuestaA)
      .mockResolvedValueOnce(respuestaA);

    await avanzarCiclo();
    await avanzarCiclo();
    await avanzarCiclo();

    expect(result.current.palabra).toBe("A"); // ventana deslizante
    expect(result.current.letra).toBe("A");
    expect(result.current.estado).toBe("ok");
  });

  it("permite repetir letra tras una pausa sin mostrarla (p. ej. deletrear OO)", async () => {
    const { result } = await montarYArrancar();
    const respuestaO = { estado: "ok", letra: "O", confianza: 0.9 };
    reconocerFotograma
      .mockResolvedValueOnce(respuestaO) // t=1s → agrega O
      .mockResolvedValueOnce({ estado: "sin_mano" }) // t=2s
      .mockResolvedValueOnce({ estado: "sin_mano" }) // t=3s
      .mockResolvedValueOnce(respuestaO); // t=4s → 3 s sin verla: agrega O

    for (let ciclo = 0; ciclo < 4; ciclo += 1) {
      await avanzarCiclo();
    }
    expect(result.current.palabra).toBe("OO");
  });

  it("cubre los flujos alternos de CU05: sin mano y confianza baja", async () => {
    const { result } = await montarYArrancar();
    reconocerFotograma.mockResolvedValueOnce({ estado: "sin_mano" });
    await avanzarCiclo();
    expect(result.current.estado).toBe("sin_mano");
    expect(result.current.letra).toBeNull();

    reconocerFotograma.mockResolvedValueOnce({
      estado: "no_reconocida",
      confianza: 0.55,
    });
    await avanzarCiclo();
    expect(result.current.estado).toBe("no_reconocida");
    expect(result.current.confianza).toBe(0.55);
  });

  it("con el modelo ausente (503) se detiene y apaga la cámara", async () => {
    const { result, pista } = await montarYArrancar();
    const error = new Error("modelo no disponible");
    error.codigo = 503;
    reconocerFotograma.mockRejectedValueOnce(error);

    await avanzarCiclo();
    expect(result.current.estado).toBe("sin_modelo");
    expect(result.current.activo).toBe(false);
    expect(pista.stop).toHaveBeenCalled();
  });

  it("descarta la respuesta en vuelo si el usuario detiene antes", async () => {
    const { result, pista } = await montarYArrancar();
    let resolver;
    reconocerFotograma.mockImplementationOnce(
      () =>
        new Promise((res) => {
          resolver = res;
        }),
    );
    await avanzarCiclo(); // dispara la petición, que queda en vuelo

    act(() => {
      result.current.detener();
    });
    await act(async () => {
      resolver({ estado: "ok", letra: "B", confianza: 0.99 });
    });

    expect(result.current.palabra).toBe(""); // la B tardía se descartó
    expect(result.current.estado).toBe("inactivo");
    expect(pista.stop).toHaveBeenCalled();
  });

  it("apaga la cámara si el permiso llega después de salir de la página", async () => {
    const { flujo, pista } = crearFlujoFalso();
    let resolver;
    instalarCamara(
      vi.fn(
        () =>
          new Promise((res) => {
            resolver = res;
          }),
      ),
    );
    const { result, unmount } = renderHook(() => useReconocimiento());
    result.current.referenciaVideo.current = crearVideoFalso();

    act(() => {
      result.current.iniciar(); // el prompt de permiso sigue abierto…
    });
    unmount(); // …y la persona navega a otra página

    await act(async () => {
      resolver(flujo); // el permiso se concede tarde
    });
    expect(pista.stop).toHaveBeenCalled(); // la cámara no queda encendida
  });

  it("informa cuando se niega el permiso de cámara", async () => {
    const rechazo = new Error("denegado");
    rechazo.name = "NotAllowedError";
    instalarCamara(vi.fn().mockRejectedValue(rechazo));
    const { result } = renderHook(() => useReconocimiento());
    result.current.referenciaVideo.current = crearVideoFalso();

    await act(async () => {
      await result.current.iniciar();
    });
    expect(result.current.estado).toBe("sin_permiso");
    expect(result.current.activo).toBe(false);
  });

  it("un error de red no detiene el ciclo y se recupera solo", async () => {
    const { result } = await montarYArrancar();
    reconocerFotograma.mockRejectedValueOnce(new Error("sin red"));
    await avanzarCiclo();
    expect(result.current.estado).toBe("error_red");
    expect(result.current.activo).toBe(true);

    reconocerFotograma.mockResolvedValueOnce({ estado: "sin_mano" });
    await avanzarCiclo();
    expect(result.current.estado).toBe("sin_mano");
  });
});
