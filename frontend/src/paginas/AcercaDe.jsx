import { Link } from "react-router-dom";

// Sección informativa sobre la LSP y el proyecto (RF09).
export default function AcercaDe() {
  return (
    <article className="mx-auto max-w-3xl">
      <Link to="/" className="text-blue-800 underline">
        ← Volver
      </Link>
      <h1 className="mt-4 text-3xl font-bold">Acerca de este diccionario</h1>

      <section aria-labelledby="titulo-lsp" className="mt-8">
        <h2 id="titulo-lsp" className="text-2xl font-bold">
          La Lengua de Señas Peruana
        </h2>
        <p className="mt-3 text-gray-900">
          La Lengua de Señas Peruana (LSP) es la lengua natural de la
          comunidad sorda del Perú. Es una lengua completa, con su propia
          gramática y vocabulario, reconocida oficialmente por el Estado
          peruano mediante la Ley N.º 29535.
        </p>
        <p className="mt-3 text-gray-900">
          El alfabeto dactilológico permite deletrear con las manos palabras
          que no tienen una seña propia, como nombres de personas o lugares.
        </p>
      </section>

      <section aria-labelledby="titulo-proyecto" className="mt-8">
        <h2 id="titulo-proyecto" className="text-2xl font-bold">
          El proyecto
        </h2>
        <p className="mt-3 text-gray-900">
          Este diccionario web nace de una tesis de la Universidad Católica
          de Santa María (Arequipa) sobre el reconocimiento automático de
          señas con aprendizaje profundo. Permite buscar palabras y ver su
          seña en video, explorar el abecedario dactilológico y practicar
          las 24 señas estáticas del alfabeto con la cámara.
        </p>
        <p className="mt-3 text-gray-900">
          Todo el contenido es de libre acceso: no hay registro, cuentas ni
          usuarios.
        </p>
      </section>

      <section aria-labelledby="titulo-privacidad" className="mt-8">
        <h2 id="titulo-privacidad" className="text-2xl font-bold">
          Tu privacidad
        </h2>
        <p className="mt-3 text-gray-900">
          Cuando usas el reconocimiento por cámara, cada imagen se procesa y
          se descarta al instante: no se guarda ni se comparte. Solo
          registramos contadores anónimos de uso (cuántas búsquedas y
          reconocimientos se hacen), sin ningún dato personal.
        </p>
      </section>
    </article>
  );
}
