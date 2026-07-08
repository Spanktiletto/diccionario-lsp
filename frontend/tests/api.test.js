import { afterEach, describe, expect, it, vi } from "vitest";

import {
  buscarPalabras,
  reconocerFotograma,
  registrarBusqueda,
} from "../src/servicios/api.js";

function respuestaFalsa(datos, ok = true, status = 200) {
  return {
    ok,
    status,
    json: () => Promise.resolve(datos),
  };
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("cliente de la API", () => {
  it("busca palabras codificando la consulta", async () => {
    const fetchFalso = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(respuestaFalsa([{ id: 1, texto: "A" }]));
    const resultados = await buscarPalabras("ñ y espacios");
    expect(resultados).toEqual([{ id: 1, texto: "A" }]);
    // URLSearchParams codifica la ñ y los espacios (espacio → '+').
    expect(fetchFalso.mock.calls[0][0]).toBe(
      "/api/palabras?q=%C3%B1+y+espacios",
    );
  });

  it("propaga el mensaje de error del backend con su código", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      respuestaFalsa({ error: "recurso no encontrado" }, false, 404),
    );
    await expect(buscarPalabras("x")).rejects.toMatchObject({
      message: "recurso no encontrado",
      codigo: 404,
    });
  });

  it("envía el fotograma y la latencia del ciclo anterior", async () => {
    const fetchFalso = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(respuestaFalsa({ estado: "sin_mano" }));
    await reconocerFotograma("data:image/jpeg;base64,AAA", 321.456);
    const cuerpo = JSON.parse(fetchFalso.mock.calls[0][1].body);
    expect(cuerpo.imagen).toBe("data:image/jpeg;base64,AAA");
    expect(cuerpo.latencia_previa_ms).toBeCloseTo(321.46);
  });

  it("omite la latencia cuando aún no hay ciclo anterior", async () => {
    const fetchFalso = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(respuestaFalsa({ estado: "sin_mano" }));
    await reconocerFotograma("AAA", null);
    const cuerpo = JSON.parse(fetchFalso.mock.calls[0][1].body);
    expect(cuerpo).not.toHaveProperty("latencia_previa_ms");
  });

  it("las métricas nunca lanzan aunque el servidor falle", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("sin red"));
    await expect(registrarBusqueda()).resolves.toBeNull();
  });

  it("registrarBusqueda envía el único evento que acepta el servidor", async () => {
    const fetchFalso = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(respuestaFalsa({ evento: "busqueda", total: 1 }));
    await registrarBusqueda();
    const [url, opciones] = fetchFalso.mock.calls[0];
    expect(url).toBe("/api/metricas");
    expect(opciones.method).toBe("POST");
    // El backend rechaza con 400 cualquier otro evento (EVENTOS_CLIENTE).
    expect(JSON.parse(opciones.body)).toEqual({ evento: "busqueda" });
  });
});
