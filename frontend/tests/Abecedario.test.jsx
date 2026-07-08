import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import Abecedario from "../src/paginas/Abecedario.jsx";

const LETRAS = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ".split("");
const DINAMICAS = new Set(["J", "Z", "Ñ"]);

vi.mock("../src/servicios/api.js", () => ({
  obtenerAbecedario: vi.fn(() =>
    Promise.resolve(
      LETRAS.map((letra, indice) => ({
        id: indice + 1,
        letra,
        es_estatica: !DINAMICAS.has(letra),
        url_gif: `/media/gifs/abecedario/${letra.toLowerCase()}.gif`,
        clase_modelo: DINAMICAS.has(letra) ? null : indice,
      })),
    ),
  ),
}));

function montar() {
  return render(
    <MemoryRouter>
      <Abecedario />
    </MemoryRouter>,
  );
}

describe("abecedario dactilológico (RF04)", () => {
  it("muestra las 27 letras", async () => {
    montar();
    expect(await screen.findAllByRole("link", { name: /letra/i })).toHaveLength(
      27,
    );
  });

  it("anuncia las letras dinámicas como solo consulta", async () => {
    montar();
    const letraJota = await screen.findByRole("link", {
      name: /letra j, seña con movimiento, solo consulta/i,
    });
    expect(letraJota).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /letra ñ, seña con movimiento/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /letra z, seña con movimiento/i }),
    ).toBeInTheDocument();
  });

  it("muestra la leyenda de señas con movimiento", async () => {
    montar();
    expect(
      await screen.findByText(/señas con movimiento \(j, z y ñ\)/i),
    ).toBeInTheDocument();
  });
});
