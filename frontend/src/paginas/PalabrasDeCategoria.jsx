import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Cargando, MensajeError } from "../componentes/EstadoCarga.jsx";
import TarjetaSena from "../componentes/TarjetaSena.jsx";
import { palabrasDeCategoria } from "../servicios/api.js";

// Palabras de una categoría (RF03), cada una enlazada a su detalle.
export default function PalabrasDeCategoria() {
  const { id } = useParams();
  const [datos, setDatos] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let vigente = true;
    setDatos(null);
    setError(null);
    palabrasDeCategoria(id)
      .then((respuesta) => vigente && setDatos(respuesta))
      .catch((fallo) =>
        vigente &&
        setError(
          fallo.codigo === 404
            ? "Esta categoría no existe."
            : "No se pudo cargar la categoría.",
        ),
      );
    return () => {
      vigente = false;
    };
  }, [id]);

  if (error) {
    return (
      <div>
        <MensajeError mensaje={error} />
        <Link to="/categorias" className="text-blue-800 underline">
          ← Ver todas las categorías
        </Link>
      </div>
    );
  }
  if (!datos) {
    return <Cargando mensaje="Cargando las palabras…" />;
  }

  return (
    <div>
      <Link to="/categorias" className="text-blue-800 underline">
        ← Categorías
      </Link>
      <h1 className="mt-4 text-3xl font-bold">{datos.categoria.nombre}</h1>
      {datos.categoria.descripcion && (
        <p className="mt-2 max-w-2xl text-gray-700">
          {datos.categoria.descripcion}
        </p>
      )}

      {datos.palabras.length === 0 ? (
        <p className="mt-8 text-gray-700">
          Esta categoría aún no tiene palabras.
        </p>
      ) : (
        <ul className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
          {datos.palabras.map((palabra) => (
            <li key={palabra.id}>
              <TarjetaSena palabra={palabra} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
