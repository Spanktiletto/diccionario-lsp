import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import Categorias from "../src/paginas/Categorias.jsx";
import PalabrasDeCategoria from "../src/paginas/PalabrasDeCategoria.jsx";

vi.mock("../src/servicios/api.js", () => ({
  listarCategorias: vi.fn(),
  palabrasDeCategoria: vi.fn(),
}));

import {
  listarCategorias,
  palabrasDeCategoria,
} from "../src/servicios/api.js";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("exploración por categorías (RF03)", () => {
  it("lista las categorías con su número de palabras (singular/plural)", async () => {
    listarCategorias.mockResolvedValue([
      { id: 1, nombre: "Abecedario", descripcion: null, total_palabras: 27 },
      { id: 2, nombre: "Saludos", descripcion: "Saludos básicos", total_palabras: 1 },
    ]);
    render(
      <MemoryRouter>
        <Categorias />
      </MemoryRouter>,
    );

    expect(
      await screen.findByRole("link", { name: /abecedario.*27 palabras/is }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /saludos.*1 palabra(?!s)/is }),
    ).toBeInTheDocument();
  });

  it("muestra un error si las categorías no cargan", async () => {
    listarCategorias.mockRejectedValue(new Error("caída"));
    render(
      <MemoryRouter>
        <Categorias />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /no se pudieron cargar/i,
    );
  });
});

function montarPalabras(id = 5) {
  return render(
    <MemoryRouter initialEntries={[`/categorias/${id}`]}>
      <Routes>
        <Route path="/categorias/:id" element={<PalabrasDeCategoria />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("palabras de una categoría (RF03)", () => {
  it("muestra las palabras enlazadas a su detalle", async () => {
    palabrasDeCategoria.mockResolvedValue({
      categoria: { id: 5, nombre: "Saludos", descripcion: null },
      palabras: [
        {
          id: 40,
          texto: "hola",
          es_letra: false,
          es_estatica: false,
          url_gif: "/media/gifs/importadas/saludos-hola.gif",
        },
      ],
    });
    montarPalabras();

    expect(
      await screen.findByRole("heading", { level: 1, name: "Saludos" }),
    ).toBeInTheDocument();
    const enlace = screen.getByRole("link", { name: /hola/i });
    expect(enlace).toHaveAttribute("href", "/palabras/40");
  });

  it("avisa cuando la categoría está vacía", async () => {
    palabrasDeCategoria.mockResolvedValue({
      categoria: { id: 5, nombre: "Nueva", descripcion: null },
      palabras: [],
    });
    montarPalabras();
    expect(
      await screen.findByText(/aún no tiene palabras/i),
    ).toBeInTheDocument();
  });

  it("maneja la categoría inexistente con mensaje y salida", async () => {
    const error404 = new Error("recurso no encontrado");
    error404.codigo = 404;
    palabrasDeCategoria.mockRejectedValue(error404);
    montarPalabras(999);

    expect(await screen.findByRole("alert")).toHaveTextContent(/no existe/i);
    expect(
      screen.getByRole("link", { name: /ver todas las categorías/i }),
    ).toBeInTheDocument();
  });
});
