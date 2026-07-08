import { Link } from "react-router-dom";

import BuscadorAutocompletado from "../componentes/BuscadorAutocompletado.jsx";

// Pantalla 1 del wireframe: búsqueda + tres accesos principales a un clic.
export default function Inicio() {
  return (
    <div className="text-center">
      <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
        ¿Qué palabra quieres aprender?
      </h1>
      <p className="mx-auto mt-3 max-w-2xl text-lg text-gray-700">
        Busca una palabra en español y mira cómo se dice en la Lengua de
        Señas Peruana.
      </p>

      <div className="mt-8">
        <BuscadorAutocompletado />
      </div>

      <nav aria-label="Secciones principales" className="mt-12">
        <ul className="mx-auto grid max-w-3xl gap-4 sm:grid-cols-3">
          <li>
            <Link
              to="/abecedario"
              className="block rounded-xl border-2 border-blue-800 bg-white px-6 py-8 text-xl font-semibold text-blue-900 shadow-sm hover:bg-blue-50"
            >
              <span aria-hidden="true" className="block text-4xl">
                🔤
              </span>
              Abecedario
            </Link>
          </li>
          <li>
            <Link
              to="/categorias"
              className="block rounded-xl border-2 border-blue-800 bg-white px-6 py-8 text-xl font-semibold text-blue-900 shadow-sm hover:bg-blue-50"
            >
              <span aria-hidden="true" className="block text-4xl">
                🗂️
              </span>
              Categorías
            </Link>
          </li>
          <li>
            <Link
              to="/reconocer"
              className="block rounded-xl bg-blue-800 px-6 py-8 text-xl font-semibold text-white shadow-sm hover:bg-blue-900"
            >
              <span aria-hidden="true" className="block text-4xl">
                📷
              </span>
              Reconocer seña con tu cámara
            </Link>
          </li>
        </ul>
      </nav>
    </div>
  );
}
