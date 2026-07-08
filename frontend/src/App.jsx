import { NavLink, Route, Routes } from "react-router-dom";

import Abecedario from "./paginas/Abecedario.jsx";
import AcercaDe from "./paginas/AcercaDe.jsx";
import Categorias from "./paginas/Categorias.jsx";
import DetallePalabra from "./paginas/DetallePalabra.jsx";
import Guia from "./paginas/Guia.jsx";
import Inicio from "./paginas/Inicio.jsx";
import PalabrasDeCategoria from "./paginas/PalabrasDeCategoria.jsx";
import Reconocer from "./paginas/Reconocer.jsx";

const ENLACES = [
  { ruta: "/abecedario", texto: "Abecedario" },
  { ruta: "/categorias", texto: "Categorías" },
  { ruta: "/reconocer", texto: "Reconocer seña" },
  { ruta: "/acerca-de", texto: "Acerca de" },
];

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-white text-gray-900">
      {/* Enlace de salto para navegación por teclado (WCAG 2.4.1) */}
      <a
        href="#contenido"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-blue-800 focus:text-white focus:px-4 focus:py-2 focus:rounded"
      >
        Saltar al contenido
      </a>

      <header className="border-b border-gray-200 bg-white">
        <nav
          aria-label="Navegación principal"
          className="mx-auto max-w-5xl px-4 py-3 flex flex-wrap items-center gap-x-6 gap-y-2"
        >
          <NavLink
            to="/"
            className="text-xl font-bold text-blue-900 hover:text-blue-700"
          >
            <span aria-hidden="true">🤟 </span>Diccionario LSP
          </NavLink>
          <ul className="flex flex-wrap gap-x-5 gap-y-1 ml-auto">
            {ENLACES.map((enlace) => (
              <li key={enlace.ruta}>
                <NavLink
                  to={enlace.ruta}
                  className={({ isActive }) =>
                    isActive
                      ? "font-semibold text-blue-800 underline underline-offset-4"
                      : "text-gray-700 hover:text-blue-800 hover:underline underline-offset-4"
                  }
                >
                  {enlace.texto}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <main id="contenido" className="flex-1 mx-auto w-full max-w-5xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Inicio />} />
          <Route path="/palabras/:id" element={<DetallePalabra />} />
          <Route path="/categorias" element={<Categorias />} />
          <Route path="/categorias/:id" element={<PalabrasDeCategoria />} />
          <Route path="/abecedario" element={<Abecedario />} />
          <Route path="/reconocer" element={<Reconocer />} />
          <Route path="/guia" element={<Guia />} />
          <Route path="/acerca-de" element={<AcercaDe />} />
          <Route
            path="*"
            element={
              <section aria-labelledby="titulo-404">
                <h1 id="titulo-404" className="text-2xl font-bold">
                  Página no encontrada
                </h1>
                <p className="mt-2">
                  <NavLink to="/" className="text-blue-800 underline">
                    Volver al inicio
                  </NavLink>
                </p>
              </section>
            }
          />
        </Routes>
      </main>

      <footer className="border-t border-gray-200 bg-gray-50">
        <p className="mx-auto max-w-5xl px-4 py-4 text-sm text-gray-700">
          Diccionario web de la Lengua de Señas Peruana · proyecto de tesis
          UCSM, Arequipa. Sitio público y gratuito, sin registro de usuarios.
        </p>
      </footer>
    </div>
  );
}
