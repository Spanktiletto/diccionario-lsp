import { useCallback, useEffect, useRef, useState } from "react";

import { reconocerFotograma } from "../servicios/api.js";
import { debeAgregarLetra } from "../servicios/composicion.js";

// Un fotograma por segundo: dentro del presupuesto de RNF02
// (respuesta ≤ 1 s por predicción) sin saturar el servidor.
const INTERVALO_CAPTURA_MS = 1000;
const ANCHO_CAPTURA = 480;
const CALIDAD_JPEG = 0.7;

/**
 * Reconocimiento de señas por cámara (RF05/RF06) y composición de
 * palabras deletreadas (RF07).
 *
 * Privacidad (RNF04): el fotograma se captura en un canvas en memoria,
 * se envía y se descarta; nunca se guarda ni se muestra a terceros.
 * La cámara se apaga SIEMPRE al detener o salir de la página, incluso
 * si el permiso se concede después de navegar (cancelación por
 * generación: cada detener() invalida las operaciones en vuelo).
 *
 * Instrumentación (Capítulo V): mide la latencia captura→respuesta
 * (incluye el dibujado y la codificación JPEG) con performance.now()
 * y la reporta al servidor una sola vez, en el ciclo siguiente
 * (campo latencia_previa_ms).
 */
export default function useReconocimiento() {
  const referenciaVideo = useRef(null);
  const referenciaFlujo = useRef(null);
  const referenciaIntervalo = useRef(null);
  const referenciaIniciando = useRef(false);
  const referenciaEnProceso = useRef(false);
  const referenciaGeneracion = useRef(0);
  const referenciaLatenciaPrevia = useRef(null);
  const referenciaUltimaAgregada = useRef({ letra: null, marca: 0 });

  const [activo, setActivo] = useState(false);
  const [iniciando, setIniciando] = useState(false);
  const [estado, setEstado] = useState("inactivo");
  const [letra, setLetra] = useState(null);
  const [confianza, setConfianza] = useState(null);
  const [palabra, setPalabra] = useState("");

  const detener = useCallback(() => {
    // Invalida cualquier getUserMedia o petición aún en vuelo.
    referenciaGeneracion.current += 1;
    if (referenciaIntervalo.current) {
      clearInterval(referenciaIntervalo.current);
      referenciaIntervalo.current = null;
    }
    if (referenciaFlujo.current) {
      referenciaFlujo.current.getTracks().forEach((pista) => pista.stop());
      referenciaFlujo.current = null;
    }
    if (referenciaVideo.current) {
      referenciaVideo.current.srcObject = null;
    }
    referenciaEnProceso.current = false;
    referenciaUltimaAgregada.current = { letra: null, marca: 0 };
    setActivo(false);
    setIniciando(false);
    setEstado("inactivo");
    setLetra(null);
    setConfianza(null);
  }, []);

  const capturarYReconocer = useCallback(async () => {
    const video = referenciaVideo.current;
    if (!video || !video.videoWidth || referenciaEnProceso.current) {
      return; // aún sin fotogramas, o el ciclo anterior sigue en vuelo
    }
    referenciaEnProceso.current = true;
    const generacion = referenciaGeneracion.current;

    // La medición captura→respuesta empieza ANTES de dibujar y
    // codificar el JPEG (definición de latencia_cliente_ms, Cap. V).
    const inicio = performance.now();
    const canvas = document.createElement("canvas");
    const escala = ANCHO_CAPTURA / video.videoWidth;
    canvas.width = ANCHO_CAPTURA;
    canvas.height = Math.round(video.videoHeight * escala);
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const fotograma = canvas.toDataURL("image/jpeg", CALIDAD_JPEG);

    // Cada medición se reporta a lo sumo una vez, aunque falle la red.
    const latenciaReportada = referenciaLatenciaPrevia.current;
    referenciaLatenciaPrevia.current = null;

    try {
      const resultado = await reconocerFotograma(fotograma, latenciaReportada);
      if (generacion !== referenciaGeneracion.current) {
        return; // el usuario detuvo mientras esperábamos: descartar
      }
      referenciaLatenciaPrevia.current = performance.now() - inicio;

      setEstado(resultado.estado);
      if (resultado.estado === "ok") {
        setLetra(resultado.letra);
        setConfianza(resultado.confianza);
        const ahora = performance.now();
        const ultima = referenciaUltimaAgregada.current;
        if (debeAgregarLetra(ultima, resultado.letra, ahora)) {
          referenciaUltimaAgregada.current = {
            letra: resultado.letra,
            marca: ahora,
          };
          setPalabra((anterior) => anterior + resultado.letra);
        } else if (ultima.letra === resultado.letra) {
          // Ventana deslizante: un gesto sostenido no repite la letra;
          // repetirla exige dejar de mostrarla ~2 s (pausa deliberada).
          ultima.marca = ahora;
        }
      } else {
        setLetra(null);
        setConfianza(
          resultado.estado === "no_reconocida"
            ? (resultado.confianza ?? null)
            : null,
        );
      }
    } catch (error) {
      if (generacion !== referenciaGeneracion.current) {
        return;
      }
      if (error.codigo === 503) {
        detener();
        setEstado("sin_modelo");
      } else {
        setEstado("error_red"); // el intervalo sigue: se recupera solo
      }
    } finally {
      referenciaEnProceso.current = false;
    }
  }, [detener]);

  const iniciar = useCallback(async () => {
    if (activo || referenciaIniciando.current || referenciaFlujo.current) {
      return; // ya en marcha o arrancando: ignorar clics repetidos
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setEstado("no_soportado");
      return;
    }
    referenciaIniciando.current = true;
    setIniciando(true);
    const generacion = referenciaGeneracion.current;
    let flujo = null;
    try {
      flujo = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });
      if (
        generacion !== referenciaGeneracion.current ||
        !referenciaVideo.current
      ) {
        // Se detuvo o desmontó mientras el navegador pedía permiso:
        // apagar la cámara recién concedida y no tocar nada más.
        flujo.getTracks().forEach((pista) => pista.stop());
        return;
      }
      referenciaFlujo.current = flujo;
      referenciaVideo.current.srcObject = flujo;
      await referenciaVideo.current.play();
      if (generacion !== referenciaGeneracion.current) {
        return; // detener() ya apagó las pistas
      }
      referenciaLatenciaPrevia.current = null;
      setEstado("esperando");
      setActivo(true);
      referenciaIntervalo.current = setInterval(
        capturarYReconocer,
        INTERVALO_CAPTURA_MS,
      );
    } catch (error) {
      if (flujo) {
        flujo.getTracks().forEach((pista) => pista.stop());
      }
      referenciaFlujo.current = null;
      if (error.name === "NotAllowedError") {
        setEstado("sin_permiso");
      } else if (
        error.name === "NotFoundError" ||
        error.name === "OverconstrainedError"
      ) {
        setEstado("sin_camara");
      } else {
        setEstado("error_camara");
      }
    } finally {
      referenciaIniciando.current = false;
      setIniciando(false);
    }
  }, [activo, capturarYReconocer]);

  // Al salir de la página, la cámara se apaga siempre.
  useEffect(() => detener, [detener]);

  return {
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
  };
}
