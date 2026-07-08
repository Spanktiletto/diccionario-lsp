import { describe, expect, it } from "vitest";

import {
  INTERVALO_REPETICION_MS,
  debeAgregarLetra,
} from "../src/servicios/composicion.js";

describe("composición de palabras deletreadas (RF07)", () => {
  it("agrega la primera letra reconocida", () => {
    expect(debeAgregarLetra({ letra: null, marca: 0 }, "A", 1000)).toBe(true);
  });

  it("agrega una letra distinta de la anterior", () => {
    expect(debeAgregarLetra({ letra: "A", marca: 1000 }, "B", 1100)).toBe(true);
  });

  it("no repite la misma letra por un gesto sostenido", () => {
    expect(debeAgregarLetra({ letra: "A", marca: 1000 }, "A", 1500)).toBe(
      false,
    );
  });

  it("permite repetir la misma letra tras la pausa deliberada", () => {
    expect(
      debeAgregarLetra(
        { letra: "A", marca: 1000 },
        "A",
        1000 + INTERVALO_REPETICION_MS,
      ),
    ).toBe(true);
  });

  it("ignora los ciclos sin letra", () => {
    expect(debeAgregarLetra({ letra: "A", marca: 1000 }, null, 5000)).toBe(
      false,
    );
  });
});
