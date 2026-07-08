import { useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { buscarPalabras, registrarBusqueda } from "../servicios/api.js";

const RETARDO_MS = 250;

/**
 * Búsqueda instantánea con autocompletado por prefijo (RF01).
 * Implementa el patrón WAI-ARIA combobox: navegable por teclado
 * (flechas, Enter, Escape) y anunciado por lectores de pantalla.
 */
export default function BuscadorAutocompletado() {
  const [consulta, setConsulta] = useState("");
  const [resultados, setResultados] = useState([]);
  const [abierto, setAbierto] = useState(false);
  const [indiceActivo, setIndiceActivo] = useState(-1);
  const [fallo, setFallo] = useState(false);
  const referenciaLista = useRef(null);
  const idBase = useId();
  const navegar = useNavigate();

  // La opción activa se mantiene visible al navegar con flechas.
  useEffect(() => {
    if (indiceActivo < 0) {
      return;
    }
    // Llamada opcional: jsdom (tests) no implementa scrollIntoView.
    referenciaLista.current?.children[indiceActivo]?.scrollIntoView?.({
      block: "nearest",
    });
  }, [indiceActivo]);

  useEffect(() => {
    const texto = consulta.trim();
    if (!texto) {
      setResultados([]);
      setAbierto(false);
      setFallo(false);
      return undefined;
    }
    const controlador = new AbortController();
    const temporizador = setTimeout(async () => {
      try {
        const encontrados = await buscarPalabras(texto, controlador.signal);
        setResultados(encontrados);
        setAbierto(true);
        setIndiceActivo(-1);
        setFallo(false);
      } catch (error) {
        if (error.name !== "AbortError") {
          setFallo(true);
          setAbierto(false);
        }
      }
    }, RETARDO_MS);
    return () => {
      clearTimeout(temporizador);
      controlador.abort();
    };
  }, [consulta]);

  function elegir(palabra) {
    setAbierto(false);
    setConsulta("");
    registrarBusqueda(); // RF10: una búsqueda efectiva, no cada tecla
    navegar(`/palabras/${palabra.id}`);
  }

  function alTeclear(evento) {
    if (evento.key === "ArrowDown" && resultados.length > 0) {
      evento.preventDefault();
      setAbierto(true);
      setIndiceActivo((indice) => (indice + 1) % resultados.length);
    } else if (evento.key === "ArrowUp" && resultados.length > 0) {
      evento.preventDefault();
      setAbierto(true);
      setIndiceActivo(
        (indice) => (indice - 1 + resultados.length) % resultados.length,
      );
    } else if (evento.key === "Enter") {
      if (abierto && indiceActivo >= 0 && resultados[indiceActivo]) {
        evento.preventDefault();
        elegir(resultados[indiceActivo]);
      } else if (abierto && resultados.length === 1) {
        evento.preventDefault();
        elegir(resultados[0]);
      }
    } else if (evento.key === "Escape") {
      setAbierto(false);
      setIndiceActivo(-1);
    }
  }

  const hayLista = abierto && resultados.length > 0;

  return (
    <div className="relative mx-auto w-full max-w-xl">
      <label htmlFor={`${idBase}-entrada`} className="sr-only">
        Buscar una palabra en español
      </label>
      <input
        id={`${idBase}-entrada`}
        type="text"
        role="combobox"
        aria-expanded={hayLista}
        aria-controls={`${idBase}-lista`}
        aria-autocomplete="list"
        aria-activedescendant={
          indiceActivo >= 0 ? `${idBase}-opcion-${indiceActivo}` : undefined
        }
        autoComplete="off"
        placeholder="🔍 Escribe una palabra…"
        value={consulta}
        onChange={(evento) => setConsulta(evento.target.value)}
        onKeyDown={alTeclear}
        onBlur={() => setTimeout(() => setAbierto(false), 150)}
        className="w-full rounded-lg border-2 border-gray-400 px-4 py-3 text-lg placeholder:text-gray-600 focus:border-blue-700"
      />

      {hayLista && (
        <ul
          id={`${idBase}-lista`}
          role="listbox"
          aria-label="Resultados de búsqueda"
          ref={referenciaLista}
          className="absolute z-10 mt-1 max-h-80 w-full overflow-y-auto rounded-lg border border-gray-300 bg-white shadow-lg"
        >
          {resultados.map((palabra, indice) => (
            <li
              key={palabra.id}
              id={`${idBase}-opcion-${indice}`}
              role="option"
              aria-selected={indice === indiceActivo}
              className={`cursor-pointer px-4 py-2 ${
                indice === indiceActivo
                  ? "bg-blue-800 text-white"
                  : "hover:bg-blue-50"
              }`}
              onMouseDown={(evento) => {
                evento.preventDefault(); // que no dispare el blur antes del clic
                elegir(palabra);
              }}
              onMouseEnter={() => setIndiceActivo(indice)}
            >
              <span className="font-semibold">{palabra.texto}</span>
              <span
                className={`ml-2 text-sm ${
                  indice === indiceActivo ? "text-blue-100" : "text-gray-600"
                }`}
              >
                {palabra.categoria}
              </span>
            </li>
          ))}
        </ul>
      )}

      {/* Estado anunciado a lectores de pantalla (WCAG 4.1.3) */}
      <p role="status" className="sr-only">
        {fallo
          ? "No se pudo buscar; revisa tu conexión."
          : consulta.trim() && abierto
            ? `${resultados.length} resultados para ${consulta}`
            : ""}
      </p>
      {fallo && (
        <p className="mt-2 text-red-800">
          No se pudo buscar. Revisa tu conexión e inténtalo de nuevo.
        </p>
      )}
      {abierto && consulta.trim() && resultados.length === 0 && (
        <p className="mt-2 text-gray-700">
          No hay palabras que empiecen con «{consulta.trim()}».
        </p>
      )}
    </div>
  );
}
