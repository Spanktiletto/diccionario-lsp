import { Link } from "react-router-dom";

// Guía breve del módulo de reconocimiento (RF08): posición de la mano,
// distancia e iluminación, en lenguaje llano y visual.
const CONSEJOS = [
  {
    icono: "✋",
    titulo: "Una sola mano",
    texto:
      "Usa una mano, con la palma mirando a la cámara. Deja la otra fuera del encuadre.",
  },
  {
    icono: "📏",
    titulo: "Distancia media",
    texto:
      "Ponte a medio metro o un metro de la cámara. Tu mano debe verse completa y grande.",
  },
  {
    icono: "💡",
    titulo: "Buena luz",
    texto:
      "Busca luz de frente, no de espaldas. Un fondo liso y claro ayuda mucho.",
  },
  {
    icono: "✊",
    titulo: "Mantén la seña quieta",
    texto:
      "Sostén cada seña uno o dos segundos, sin moverla, hasta que aparezca la letra.",
  },
  {
    icono: "🔄",
    titulo: "J, Z y Ñ no se reconocen",
    texto:
      "Esas tres letras llevan movimiento. Puedes verlas en el abecedario, pero la cámara no las detecta.",
  },
  {
    icono: "🔒",
    titulo: "Tu privacidad primero",
    texto:
      "Tu imagen se usa solo para reconocer la seña y se descarta al instante. No se guarda nada.",
  },
];

export default function Guia() {
  return (
    <div>
      <Link to="/reconocer" className="text-blue-800 underline">
        ← Volver al reconocimiento
      </Link>
      <h1 className="mt-4 text-3xl font-bold">Guía de uso</h1>
      <p className="mt-2 max-w-2xl text-gray-700">
        Sigue estos consejos para que la cámara reconozca bien tus señas.
      </p>

      <ul className="mt-8 grid gap-4 sm:grid-cols-2">
        {CONSEJOS.map((consejo) => (
          <li
            key={consejo.titulo}
            className="rounded-xl border border-gray-300 bg-white p-5"
          >
            <h2 className="text-lg font-bold text-gray-900">
              <span aria-hidden="true" className="mr-2 text-2xl">
                {consejo.icono}
              </span>
              {consejo.titulo}
            </h2>
            <p className="mt-1 text-gray-800">{consejo.texto}</p>
          </li>
        ))}
      </ul>

      <p className="mt-8">
        <Link
          to="/reconocer"
          className="inline-block rounded-lg bg-blue-800 px-6 py-3 font-semibold text-white hover:bg-blue-900"
        >
          Probar el reconocimiento
        </Link>
      </p>
    </div>
  );
}
