// Estados de carga y de error, anunciados a los lectores de pantalla.

export function Cargando({ mensaje = "Cargando…" }) {
  return (
    <p role="status" className="py-8 text-center text-gray-700">
      {mensaje}
    </p>
  );
}

export function MensajeError({ mensaje }) {
  return (
    <p
      role="alert"
      className="my-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-red-900"
    >
      {mensaje}
    </p>
  );
}
