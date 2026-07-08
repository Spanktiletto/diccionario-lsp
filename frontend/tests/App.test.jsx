import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import App from "../src/App.jsx";

vi.mock("../src/servicios/api.js", () => ({
  buscarPalabras: vi.fn().mockResolvedValue([]),
  registrarBusqueda: vi.fn().mockResolvedValue(null),
  obtenerAbecedario: vi.fn().mockResolvedValue([]),
  listarCategorias: vi.fn().mockResolvedValue([]),
  palabrasDeCategoria: vi.fn().mockResolvedValue({ categoria: {}, palabras: [] }),
  obtenerPalabra: vi.fn().mockResolvedValue(null),
  reconocerFotograma: vi.fn(),
}));

function montar(ruta = "/") {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <App />
    </MemoryRouter>,
  );
}

describe("estructura accesible de la aplicación", () => {
  it("tiene enlace de salto, navegación, contenido principal y pie", () => {
    montar();
    expect(
      screen.getByRole("link", { name: /saltar al contenido/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("navigation", { name: /navegación principal/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
  });

  it("la portada ofrece las tres acciones principales a un clic", () => {
    montar();
    const principal = within(screen.getByRole("main"));
    expect(
      principal.getByRole("link", { name: /abecedario/i }),
    ).toBeInTheDocument();
    expect(
      principal.getByRole("link", { name: /categorías/i }),
    ).toBeInTheDocument();
    expect(
      principal.getByRole("link", { name: /reconocer seña con tu cámara/i }),
    ).toBeInTheDocument();
  });

  it("las rutas desconocidas muestran una página 404 con salida", () => {
    montar("/no-existe");
    expect(
      screen.getByRole("heading", { name: /página no encontrada/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /volver al inicio/i }),
    ).toBeInTheDocument();
  });

  it("la guía de uso cubre mano, distancia e iluminación (RF08)", () => {
    montar("/guia");
    // Anclado a estructura (headings), no a la redacción exacta.
    const titulos = screen
      .getAllByRole("heading", { level: 2 })
      .map((titulo) => titulo.textContent)
      .join(" · ");
    expect(titulos).toMatch(/mano/i);
    expect(titulos).toMatch(/distancia/i);
    expect(titulos).toMatch(/luz/i);
  });

  it("acerca de usa la terminología correcta (RF09)", () => {
    montar("/acerca-de");
    expect(
      screen.getAllByText(/lengua de señas peruana/i).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/comunidad sorda/i)).toBeInTheDocument();
    // Nunca "lenguaje de señas" ni "sordomudo".
    expect(screen.queryByText(/lenguaje de señas/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sordomudo/i)).not.toBeInTheDocument();
  });
});
