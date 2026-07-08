import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Cargando, MensajeError } from "../componentes/EstadoCarga.jsx";
import { listarCategorias } from "../servicios/api.js";

// Exploración por categorías temáticas (RF03).
export default function Categorias() {
  const [categorias, setCategorias] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    listarCategorias()
      .then(setCategorias)
      .catch(() => setError("No se pudieron cargar las categorías."));
  }, []);

  if (error) {
    return <MensajeError mensaje={error} />;
  }
  if (!categorias) {
    return <Cargando mensaje="Cargando las categorías…" />;
  }

  return (
    <div>
      <Link to="/" className="text-blue-800 underline">
        ← Volver
      </Link>
      <h1 className="mt-4 text-3xl font-bold">Categorías</h1>
      <p className="mt-2 max-w-2xl text-gray-700">
        Explora el vocabulario por temas, sin necesidad de conocer una
        palabra exacta.
      </p>

      <ul className="mt-8 grid gap-4 sm:grid-cols-2 md:grid-cols-3">
        {categorias.map((categoria) => (
          <li key={categoria.id}>
            <Link
              to={`/categorias/${categoria.id}`}
              className="block rounded-xl border-2 border-gray-300 bg-white p-6 hover:border-blue-700 hover:shadow"
            >
              <span className="block text-xl font-bold text-gray-900">
                {categoria.nombre}
              </span>
              {categoria.descripcion && (
                <span className="mt-1 block text-gray-700">
                  {categoria.descripcion}
                </span>
              )}
              <span className="mt-2 block text-sm text-gray-600">
                {categoria.total_palabras}{" "}
                {categoria.total_palabras === 1 ? "palabra" : "palabras"}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
