import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import useReconocimiento from "../hooks/useReconocimiento.js";

// Pantalla 4 del wireframe: video en vivo + letra reconocida con su
// confianza + palabra en construcción (RF05, RF06, RF07).
const MENSAJES = {
  inactivo: "Pulsa «Iniciar» y permite el uso de tu cámara.",
  esperando: "Muestra una seña del abecedario frente a la cámara.",
  sin_mano: "No vemos tu mano. Acércala a la cámara.",
  no_reconocida: "Seña no reconocida. Revisa la guía si necesitas ayuda.",
  sin_modelo:
    "El reconocimiento aún no está disponible en el servidor. El resto del diccionario funciona con normalidad.",
  sin_permiso:
    "No diste permiso para usar la cámara. Actívalo en tu navegador y vuelve a intentar.",
  sin_camara: "No encontramos una cámara en tu dispositivo.",
  no_soportado: "Tu navegador no permite usar la cámara.",
  error_camara:
    "No se pudo encender la cámara. Cierra otras aplicaciones que la estén usando e inténtalo de nuevo.",
  error_red: "Se perdió la conexión con el servidor. Reintentando…",
};

export default function Reconocer() {
  const {
    referenciaVideo,
    activo,
    iniciando,
    estado,
    letra,
    confianza,
    palabra,
    setPalabra,
    iniciar,
    detener,
  } = useReconocimiento();

  // Anuncio para lectores de pantalla: SOLO cuando cambia la letra o
  // el estado — nunca por la fluctuación del porcentaje cada segundo
  // (evita la sobre-verbosidad que desaconseja WCAG 4.1.3).
  const [anuncio, setAnuncio] = useState("");
  const referenciaAnunciado = useRef({ estado: null, letra: null });
  useEffect(() => {
    const previo = referenciaAnunciado.current;
    if (previo.estado === estado && previo.letra === letra) {
      return;
    }
    referenciaAnunciado.current = { estado, letra };
    setAnuncio(
      estado === "ok" && letra
        ? `Letra ${letra} reconocida`
        : (MENSAJES[estado] ?? ""),
    );
  }, [estado, letra]);

  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <Link to="/" className="text-blue-800 underline">
          ← Volver
        </Link>
        <Link
          to="/guia"
          className="rounded-full border-2 border-blue-800 px-4 py-1 font-semibold text-blue-900 hover:bg-blue-50"
        >
          Guía de uso <span aria-hidden="true">?</span>
        </Link>
      </div>

      <h1 className="mt-4 text-3xl font-bold">Reconocer seña</h1>
      <p className="mt-2 max-w-2xl text-gray-700">
        Haz una seña del abecedario frente a tu cámara y te diremos qué
        letra es. Las letras J, Z y Ñ llevan movimiento y no se reconocen.
      </p>

      <div className="mt-8 grid gap-8 md:grid-cols-2">
        <section aria-label="Tu cámara">
          <div className="relative overflow-hidden rounded-xl border-2 border-gray-300 bg-gray-900">
            <video
              ref={referenciaVideo}
              muted
              playsInline
              aria-label="Video en vivo de tu cámara"
              className="aspect-[4/3] w-full -scale-x-100 object-cover"
            />
            {!activo && (
              <p className="absolute inset-0 flex items-center justify-center px-6 text-center text-white">
                La cámara está apagada.
              </p>
            )}
          </div>
          <p className="mt-2 text-sm text-gray-700">
            🔒 Tu imagen se procesa y se descarta al instante. No guardamos
            ningún video ni foto.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            {activo ? (
              <button
                type="button"
                onClick={detener}
                className="rounded-lg bg-gray-800 px-6 py-3 font-semibold text-white hover:bg-gray-900"
              >
                Detener
              </button>
            ) : (
              <button
                type="button"
                onClick={iniciar}
                disabled={iniciando}
                className="rounded-lg bg-blue-800 px-6 py-3 font-semibold text-white hover:bg-blue-900 disabled:cursor-wait disabled:bg-gray-500"
              >
                {iniciando ? "Encendiendo…" : "Iniciar"}
              </button>
            )}
          </div>
        </section>

        <section aria-label="Resultado del reconocimiento">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-600">
            Letra reconocida
          </h2>
          <div className="mt-2">
            {letra && estado === "ok" ? (
              <p>
                <span className="inline-block rounded-xl border-4 border-green-700 bg-green-50 px-8 py-4 text-6xl font-bold text-green-900">
                  {letra}
                </span>
                <span className="ml-4 text-2xl font-semibold text-gray-800">
                  {Math.round(confianza * 100)} %
                </span>
              </p>
            ) : (
              <p className="rounded-xl border border-gray-300 bg-gray-50 px-4 py-6 text-gray-800">
                {MENSAJES[estado] ?? MENSAJES.inactivo}
                {estado === "no_reconocida" && confianza != null && (
                  <span className="mt-1 block text-sm text-gray-600">
                    {/* floor: nunca puede mostrar «80 %» si no llegó al umbral */}
                    (confianza {Math.floor(confianza * 100)} %, se necesita
                    al menos 80 %)
                  </span>
                )}
              </p>
            )}
          </div>
          {/* Región viva aparte, solo con los cambios relevantes */}
          <p role="status" aria-live="polite" className="sr-only">
            {anuncio}
          </p>

          <h2 className="mt-8 text-sm font-semibold uppercase tracking-wide text-gray-600">
            <label htmlFor="palabra-compuesta">Palabra que deletreas</label>
          </h2>
          <input
            id="palabra-compuesta"
            type="text"
            value={palabra}
            onChange={(evento) => setPalabra(evento.target.value.toUpperCase())}
            placeholder="Las letras aparecen aquí…"
            className="mt-2 w-full rounded-lg border-2 border-gray-400 px-4 py-3 font-mono text-2xl tracking-widest placeholder:text-gray-600"
          />
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => setPalabra((anterior) => anterior + " ")}
              className="rounded-lg border-2 border-gray-400 px-5 py-2 font-semibold text-gray-800 hover:border-blue-700"
            >
              Espacio
            </button>
            <button
              type="button"
              onClick={() => setPalabra((anterior) => anterior.slice(0, -1))}
              className="rounded-lg border-2 border-gray-400 px-5 py-2 font-semibold text-gray-800 hover:border-blue-700"
            >
              Borrar letra
            </button>
            <button
              type="button"
              onClick={() => setPalabra("")}
              className="rounded-lg border-2 border-gray-400 px-5 py-2 font-semibold text-gray-800 hover:border-blue-700"
            >
              Borrar todo
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}
