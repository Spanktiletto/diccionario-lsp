// Cliente de la API REST del backend (rutas relativas; en desarrollo
// las reenvía el proxy de Vite).

async function pedirJson(ruta, opciones = {}) {
  const respuesta = await fetch(ruta, opciones);
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const error = new Error(datos?.error ?? `error ${respuesta.status}`);
    error.codigo = respuesta.status;
    throw error;
  }
  return datos;
}

export function buscarPalabras(consulta, senal) {
  const parametros = new URLSearchParams({ q: consulta });
  return pedirJson(`/api/palabras?${parametros}`, { signal: senal });
}

export function obtenerPalabra(id) {
  return pedirJson(`/api/palabras/${id}`);
}

export function listarCategorias() {
  return pedirJson("/api/categorias");
}

export function palabrasDeCategoria(id) {
  return pedirJson(`/api/categorias/${id}/palabras`);
}

export function obtenerAbecedario() {
  return pedirJson("/api/abecedario");
}

/**
 * Envía un fotograma JPEG (base64 o data URI) al reconocedor.
 * `latenciaPreviaMs` es la latencia captura→respuesta del ciclo
 * anterior, medida con performance.now(): alimenta la columna
 * latencia_cliente_ms del CSV de instrumentación (Capítulo V).
 */
export function reconocerFotograma(imagenBase64, latenciaPreviaMs = null) {
  const cuerpo = { imagen: imagenBase64 };
  if (typeof latenciaPreviaMs === "number" && latenciaPreviaMs >= 0) {
    cuerpo.latencia_previa_ms = Math.round(latenciaPreviaMs * 100) / 100;
  }
  return pedirJson("/api/reconocer", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cuerpo),
  });
}

/** Métrica anónima agregada (RF10). Nunca debe romper la experiencia. */
export function registrarBusqueda() {
  return pedirJson("/api/metricas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ evento: "busqueda" }),
  }).catch(() => null);
}
