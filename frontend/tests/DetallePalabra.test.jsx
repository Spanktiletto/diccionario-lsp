import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import DetallePalabra from "../src/paginas/DetallePalabra.jsx";

vi.mock("../src/servicios/api.js", () => ({
  obtenerPalabra: vi.fn(),
}));

import { obtenerPalabra } from "../src/servicios/api.js";

const PALABRA_A = {
  id: 1,
  texto: "A",
  descripcion: "Letra A del alfabeto dactilológico",
  es_letra: true,
  es_estatica: true,
  categoria: { id: 1, nombre: "Abecedario" },
  sena: {
    url_gif: "/media/gifs/abecedario/a.gif",
    descripcion_ejecucion: null,
    clase_modelo: 0,
  },
  relacionadas: [{ id: 2, texto: "B" }],
};

function montar(id = 1) {
  return render(
    <MemoryRouter initialEntries={[`/palabras/${id}`]}>
      <Routes>
        <Route path="/palabras/:id" element={<DetallePalabra />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("vista detallada de una palabra (RF02)", () => {
  it("muestra el GIF con texto alternativo, la categoría y relacionadas", async () => {
    obtenerPalabra.mockResolvedValue(PALABRA_A);
    montar();

    expect(
      await screen.findByRole("heading", { level: 1, name: "A" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("img", { name: /seña de a en lengua de señas peruana/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Abecedario" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "B" })).toBeInTheDocument();
  });

  it("indica cuando la descripción de ejecución no existe, sin inventarla", async () => {
    obtenerPalabra.mockResolvedValue(PALABRA_A);
    montar();
    expect(
      await screen.findByText(/aún no está disponible/i),
    ).toBeInTheDocument();
  });

  it("avisa que las letras dinámicas no se reconocen por cámara", async () => {
    obtenerPalabra.mockResolvedValue({
      ...PALABRA_A,
      texto: "J",
      es_estatica: false,
      sena: { ...PALABRA_A.sena, clase_modelo: null },
    });
    montar();
    expect(
      await screen.findByText(/la cámara no la reconoce/i),
    ).toBeInTheDocument();
  });

  it("maneja una palabra sin GIF (sena null, contrato real del backend)", async () => {
    obtenerPalabra.mockResolvedValue({ ...PALABRA_A, sena: null });
    montar();
    expect(
      await screen.findByText(/aún no tiene GIF disponible/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(
      screen.getByText(/la descripción de ejecución aún no está disponible/i),
    ).toBeInTheDocument();
  });

  it("muestra un mensaje claro si la palabra no existe", async () => {
    const error404 = new Error("recurso no encontrado");
    error404.codigo = 404;
    obtenerPalabra.mockRejectedValue(error404);
    montar(999);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /no existe en el diccionario/i,
    );
  });
});
