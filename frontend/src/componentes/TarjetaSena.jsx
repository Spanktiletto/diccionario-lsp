import { Link } from "react-router-dom";

/**
 * Tarjeta de una palabra con su GIF, enlazada a la vista detallada.
 * El GIF es contenido (no decoración): lleva texto alternativo.
 */
export default function TarjetaSena({ palabra }) {
  return (
    <Link
      to={`/palabras/${palabra.id}`}
      className="block rounded-lg border border-gray-300 bg-white p-3 text-center shadow-sm hover:border-blue-700 hover:shadow"
    >
      {palabra.url_gif ? (
        <img
          src={palabra.url_gif}
          alt={`Seña de ${palabra.texto}`}
          className="mx-auto h-28 w-28 rounded object-cover"
          loading="lazy"
        />
      ) : (
        <span
          aria-hidden="true"
          className="mx-auto flex h-28 w-28 items-center justify-center rounded bg-gray-100 text-3xl font-bold text-gray-400"
        >
          {palabra.texto.charAt(0)}
        </span>
      )}
      <span className="mt-2 block font-semibold text-gray-900">
        {palabra.texto}
      </span>
    </Link>
  );
}
