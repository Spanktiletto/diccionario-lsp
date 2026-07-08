import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Cargando, MensajeError } from "../componentes/EstadoCarga.jsx";
import { obtenerPalabra } from "../servicios/api.js";

// Pantalla 2 del wireframe: GIF en bucle + categoría + descripción de
// ejecución + palabras relacionadas (RF02).
export default function DetallePalabra() {
  const { id } = useParams();
  const [palabra, setPalabra] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let vigente = true;
    setPalabra(null);
    setError(null);
    obtenerPalabra(id)
      .then((datos) => vigente && setPalabra(datos))
      .catch((fallo) =>
        vigente &&
        setError(
          fallo.codigo === 404
            ? "Esta palabra no existe en el diccionario."
            : "No se pudo cargar la palabra. Inténtalo de nuevo.",
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
        <Link to="/" className="text-blue-800 underline">
          ← Volver al inicio
        </Link>
      </div>
    );
  }
  if (!palabra) {
    return <Cargando mensaje="Cargando la seña…" />;
  }

  return (
    <article>
      <Link to="/" className="text-blue-800 underline">
        ← Volver
      </Link>

      <h1 className="mt-4 text-3xl font-bold">{palabra.texto}</h1>

      <div className="mt-6 grid gap-8 md:grid-cols-2">
        <div>
          {palabra.sena?.url_gif ? (
            <img
              src={palabra.sena.url_gif}
              alt={`Seña de ${palabra.texto} en Lengua de Señas Peruana, animación en bucle`}
              className="w-full max-w-md rounded-xl border border-gray-300 shadow-sm"
            />
          ) : (
            <p className="rounded-xl border border-gray-300 bg-gray-50 p-8 text-center text-gray-700">
              Esta palabra aún no tiene GIF disponible.
            </p>
          )}
        </div>

        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-600">
            Categoría
          </h2>
          <p className="mt-1">
            <Link
              to={`/categorias/${palabra.categoria.id}`}
              className="inline-block rounded-full bg-blue-100 px-4 py-1 font-semibold text-blue-900 hover:bg-blue-200"
            >
              {palabra.categoria.nombre}
            </Link>
          </p>

          {palabra.descripcion && (
            <>
              <h2 className="mt-6 text-sm font-semibold uppercase tracking-wide text-gray-600">
                Descripción
              </h2>
              <p className="mt-1 text-gray-900">{palabra.descripcion}</p>
            </>
          )}

          <h2 className="mt-6 text-sm font-semibold uppercase tracking-wide text-gray-600">
            Cómo se ejecuta
          </h2>
          <p className="mt-1 text-gray-900">
            {palabra.sena?.descripcion_ejecucion ??
              "La descripción de ejecución aún no está disponible."}
          </p>

          {palabra.es_letra && !palabra.es_estatica && (
            <p className="mt-6 rounded border border-amber-300 bg-amber-50 px-4 py-3 text-amber-900">
              Esta letra se hace con movimiento: puedes verla aquí, pero la
              cámara no la reconoce.
            </p>
          )}
        </div>
      </div>

      {palabra.relacionadas.length > 0 && (
        <section aria-labelledby="titulo-relacionadas" className="mt-10">
          <h2 id="titulo-relacionadas" className="text-xl font-bold">
            Palabras relacionadas
          </h2>
          <ul className="mt-3 flex flex-wrap gap-2">
            {palabra.relacionadas.map((relacionada) => (
              <li key={relacionada.id}>
                <Link
                  to={`/palabras/${relacionada.id}`}
                  className="inline-block rounded-full border border-gray-300 px-4 py-1 text-gray-800 hover:border-blue-700 hover:text-blue-800"
                >
                  {relacionada.texto}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
