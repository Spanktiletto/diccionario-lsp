import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Reconocer from "../src/paginas/Reconocer.jsx";

vi.mock("../src/servicios/api.js", () => ({
  reconocerFotograma: vi.fn(),
}));

function montar() {
  return render(
    <MemoryRouter>
      <Reconocer />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  delete navigator.mediaDevices;
});

describe("reconocimiento por cámara (RF05–RF07)", () => {
  it("muestra las instrucciones iniciales, la nota de privacidad y la guía", () => {
    montar();
    // El mensaje aparece en el panel visual y en la región sr-only.
    expect(screen.getAllByText(/pulsa «iniciar»/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/se procesa y se descarta al instante/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /guía de uso/i }),
    ).toBeInTheDocument();
  });

  it("informa cuando el navegador no soporta cámara", async () => {
    // Precondición explícita: sin API de medios (no dependemos de jsdom).
    Object.defineProperty(navigator, "mediaDevices", {
      value: undefined,
      configurable: true,
    });
    const usuario = userEvent.setup();
    montar();
    await usuario.click(screen.getByRole("button", { name: "Iniciar" }));
    expect(
      (await screen.findAllByText(/tu navegador no permite usar la cámara/i))
        .length,
    ).toBeGreaterThan(0);
  });

  it("informa cuando la persona niega el permiso de cámara", async () => {
    const rechazo = new Error("denegado");
    rechazo.name = "NotAllowedError";
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: vi.fn().mockRejectedValue(rechazo) },
      configurable: true,
    });
    const usuario = userEvent.setup();
    montar();
    await usuario.click(screen.getByRole("button", { name: "Iniciar" }));
    expect(
      (await screen.findAllByText(/no diste permiso para usar la cámara/i))
        .length,
    ).toBeGreaterThan(0);
  });

  it("la palabra compuesta es editable y sus botones funcionan (RF07)", async () => {
    const usuario = userEvent.setup();
    montar();
    const campo = screen.getByLabelText(/palabra que deletreas/i);

    await usuario.type(campo, "ana");
    expect(campo).toHaveValue("ANA"); // siempre en mayúsculas, como el abecedario

    await usuario.click(screen.getByRole("button", { name: "Espacio" }));
    expect(campo).toHaveValue("ANA ");

    await usuario.click(screen.getByRole("button", { name: "Borrar letra" }));
    expect(campo).toHaveValue("ANA");

    await usuario.click(screen.getByRole("button", { name: "Borrar todo" }));
    expect(campo).toHaveValue("");
  });

  it("el resultado se anuncia en una región aria-live", () => {
    const { container } = montar();
    expect(container.querySelector('[aria-live="polite"]')).not.toBeNull();
  });

  it("menciona que J, Z y Ñ no se reconocen", () => {
    montar();
    expect(screen.getByText(/j, z y ñ/i)).toBeInTheDocument();
  });
});
