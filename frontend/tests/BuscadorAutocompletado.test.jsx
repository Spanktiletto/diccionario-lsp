import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import BuscadorAutocompletado from "../src/componentes/BuscadorAutocompletado.jsx";

vi.mock("../src/servicios/api.js", () => ({
  buscarPalabras: vi.fn(),
  registrarBusqueda: vi.fn().mockResolvedValue(null),
}));

import { buscarPalabras, registrarBusqueda } from "../src/servicios/api.js";

function montar() {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<BuscadorAutocompletado />} />
        <Route path="/palabras/:id" element={<p>detalle de palabra</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("buscador con autocompletado (RF01)", () => {
  it("es un combobox accesible con etiqueta en español", () => {
    montar();
    const entrada = screen.getByRole("combobox", {
      name: /buscar una palabra/i,
    });
    expect(entrada).toHaveAttribute("aria-autocomplete", "list");
    expect(entrada).toHaveAttribute("aria-expanded", "false");
  });

  it("muestra resultados tras teclear (con debounce)", async () => {
    buscarPalabras.mockResolvedValue([
      { id: 1, texto: "A", categoria: "Abecedario" },
    ]);
    const usuario = userEvent.setup();
    montar();

    await usuario.type(screen.getByRole("combobox"), "a");
    const opcion = await screen.findByRole("option", { name: /A/ });
    expect(opcion).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toHaveAttribute(
      "aria-expanded",
      "true",
    );
  });

  it("una ráfaga de teclas produce UNA sola llamada a la API (debounce)", async () => {
    vi.useFakeTimers();
    buscarPalabras.mockResolvedValue([]);
    montar();
    const entrada = screen.getByRole("combobox");

    // Ráfaga de escritura: cada cambio reinicia el debounce de 250 ms.
    for (const parcial of ["h", "ho", "hol", "hola"]) {
      fireEvent.change(entrada, { target: { value: parcial } });
    }
    expect(buscarPalabras).not.toHaveBeenCalled(); // nada por tecla

    await act(async () => {
      await vi.advanceTimersByTimeAsync(250);
    });
    expect(buscarPalabras).toHaveBeenCalledTimes(1);
    expect(buscarPalabras.mock.calls[0][0]).toBe("hola");
  });

  it("selecciona con el ratón pese al blur del combobox", async () => {
    buscarPalabras.mockResolvedValue([
      { id: 9, texto: "C", categoria: "Abecedario" },
    ]);
    const usuario = userEvent.setup();
    montar();

    await usuario.type(screen.getByRole("combobox"), "c");
    const opcion = await screen.findByRole("option", { name: /C/ });
    await usuario.click(opcion);

    await screen.findByText("detalle de palabra");
    expect(registrarBusqueda).toHaveBeenCalledTimes(1);
  });

  it("navega al detalle con flechas y Enter, y registra la métrica", async () => {
    buscarPalabras.mockResolvedValue([
      { id: 7, texto: "B", categoria: "Abecedario" },
    ]);
    const usuario = userEvent.setup();
    montar();

    await usuario.type(screen.getByRole("combobox"), "b");
    await screen.findByRole("option", { name: /B/ });
    await usuario.keyboard("{ArrowDown}{Enter}");

    await screen.findByText("detalle de palabra");
    expect(registrarBusqueda).toHaveBeenCalledTimes(1);
  });

  it("cierra la lista con Escape", async () => {
    buscarPalabras.mockResolvedValue([
      { id: 1, texto: "A", categoria: "Abecedario" },
    ]);
    const usuario = userEvent.setup();
    montar();

    await usuario.type(screen.getByRole("combobox"), "a");
    await screen.findByRole("option", { name: /A/ });
    await usuario.keyboard("{Escape}");
    expect(screen.queryByRole("option")).not.toBeInTheDocument();
  });

  it("avisa cuando no hay coincidencias", async () => {
    buscarPalabras.mockResolvedValue([]);
    const usuario = userEvent.setup();
    montar();

    await usuario.type(screen.getByRole("combobox"), "zzz");
    expect(
      await screen.findByText(/no hay palabras que empiecen/i),
    ).toBeInTheDocument();
  });

  it("muestra un error si la búsqueda falla", async () => {
    buscarPalabras.mockRejectedValue(new Error("caída"));
    const usuario = userEvent.setup();
    montar();

    await usuario.type(screen.getByRole("combobox"), "a");
    expect(
      await screen.findByText(/revisa tu conexión e inténtalo de nuevo/i),
    ).toBeInTheDocument();
  });
});
