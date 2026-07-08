import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Cargando, MensajeError } from "../componentes/EstadoCarga.jsx";
import { obtenerAbecedario } from "../servicios/api.js";

// Pantalla 3 del wireframe: las 27 letras del abecedario dactilológico;
// las dinámicas (J, Z, Ñ) se marcan con * y solo se consultan (RF04).
export default function Abecedario() {
  const [letras, setLetras] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    obtenerAbecedario()
      .then(setLetras)
      .catch(() => setError("No se pudo cargar el abecedario."));
  }, []);

  if (error) {
    return <MensajeError mensaje={error} />;
  }
  if (!letras) {
    return <Cargando mensaje="Cargando el abecedario…" />;
  }

  return (
    <div>
      <Link to="/" className="text-blue-800 underline">
        ← Volver
      </Link>
      <h1 className="mt-4 text-3xl font-bold">Abecedario dactilológico</h1>
      <p className="mt-2 max-w-2xl text-gray-700">
        Toca una letra para ver su seña en grande.
      </p>

      <ul className="mt-8 grid grid-cols-3 gap-3 sm:grid-cols-5 md:grid-cols-7">
        {letras.map((letra) => (
          <li key={letra.id}>
            <Link
              to={`/palabras/${letra.id}`}
              aria-label={
                letra.es_estatica
                  ? `Letra ${letra.letra}`
                  : `Letra ${letra.letra}, seña con movimiento, solo consulta`
              }
              className="block rounded-lg border-2 border-gray-300 bg-white p-2 text-center hover:border-blue-700 hover:shadow"
            >
              <img
                src={letra.url_gif}
                alt=""
                aria-hidden="true"
                loading="lazy"
                className="mx-auto h-20 w-20 rounded object-cover"
              />
              <span className="mt-1 block text-xl font-bold text-gray-900">
                {letra.letra}
                {!letra.es_estatica && (
                  <span aria-hidden="true" className="text-amber-700">
                    *
                  </span>
                )}
              </span>
            </Link>
          </li>
        ))}
      </ul>

      <p className="mt-6 text-gray-700">
        <span aria-hidden="true" className="font-bold text-amber-700">
          *
        </span>{" "}
        Señas con movimiento (J, Z y Ñ): puedes verlas, pero la cámara no las
        reconoce.
      </p>
    </div>
  );
}
