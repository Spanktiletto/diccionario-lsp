// Lógica pura de la composición de palabras deletreadas (RF07):
// decide cuándo una letra reconocida se agrega a la palabra en
// construcción, evitando que un mismo gesto sostenido la repita.

export const INTERVALO_REPETICION_MS = 2000;

/**
 * @param {{letra: string|null, marca: number}} ultima  última letra agregada
 *   y el instante en que se agregó o se VIO por última vez (el hook
 *   refresca la marca en cada ciclo que reconoce la misma letra, de
 *   modo que un gesto sostenido nunca la repite: repetirla exige dejar
 *   de mostrarla durante la pausa deliberada).
 * @param {string|null} letra  letra reconocida en este ciclo
 * @param {number} ahora  instante actual (performance.now())
 * @returns {boolean} si la letra debe agregarse a la palabra
 */
export function debeAgregarLetra(ultima, letra, ahora) {
  if (!letra) {
    return false;
  }
  if (!ultima.letra || ultima.letra !== letra) {
    return true;
  }
  return ahora - ultima.marca >= INTERVALO_REPETICION_MS;
}
