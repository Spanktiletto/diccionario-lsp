# Diccionario Web de la Lengua de Señas Peruana (LSP)

Aplicación web pública que acompaña la tesis "Implementación de un diccionario web de la Lengua de Señas Peruana aplicando Deep Learning para el reconocimiento automático de señas, Arequipa – 2026" (UCSM). La app DEBE mantenerse coherente con la tesis: toda decisión técnica ya está especificada en `docs/ESPECIFICACION_TECNICA.md` (fuente de verdad). Si una mejora técnica contradice la especificación, proponla y espera aprobación antes de implementarla.

## Restricciones inviolables

- **App pública sin usuarios:** NO implementar login, registro, autenticación, roles, sesiones de usuario, panel administrativo ni tablas de usuarios. Nunca. Si una librería o patrón lo sugiere, rechazarlo.
- **Privacidad:** los fotogramas de la cámara se procesan y se descartan; jamás se almacenan imágenes del usuario. Del dataset solo se guardan vectores de landmarks, nunca fotos.
- **Alcance del modelo:** 24 señas ESTÁTICAS del alfabeto dactilológico. J, Z y Ñ (dinámicas) solo aparecen como GIFs consultables (`es_estatica = false`).
- **Datos reales únicamente:** no generar señas, GIFs ni registros ficticios. El contenido llega por el módulo de importación (API de señas que proporcionará el usuario, o archivos JSON/CSV). Para desarrollo, usar solo los seeds del alfabeto con GIFs placeholder claramente marcados.
- **Terminología:** "Lengua de Señas Peruana" (no "Lenguaje"); "persona sorda" (nunca "sordomudo").

## Stack (fijado por la tesis — no cambiar)

- Frontend: **React + Vite + Tailwind CSS** (SPA que consume la API REST; responsive; WCAG 2.1 AA)
- Backend: Python 3.11+, **Flask**, API REST JSON
- Base de datos: **PostgreSQL** (esquema exacto en la especificación: 3 tablas — categoria, palabra, sena; sin tablas de usuarios)
- IA: **OpenCV** (preproceso), **MediaPipe Hands** (21 landmarks), **TensorFlow/Keras** (red densa 63→128→64→24, softmax, dropout 0.3/0.2, Adam lr=0.001, umbral de confianza 0.8)
- Control de versiones: Git (commits convencionales en español)
- Tests: pytest (backend, cobertura ≥ 70 %), Vitest/React Testing Library (frontend)

## Estructura del proyecto

```
backend/app/         # Flask: rutas API, lógica, integración del modelo
backend/importador/  # CLI: sincronizar desde API de señas, importar JSON/CSV
backend/tests/       # pytest
frontend/            # React + Vite + Tailwind (SPA)
ml/dataset/          # vectores de landmarks etiquetados (nunca imágenes)
ml/scripts/          # capturar_muestras.py, entrenar.py, evaluar.py
ml/modelos/          # modelo .keras (no versionado) + clases.json (versionado)
db/                  # schema.sql, seeds del alfabeto
docs/                # ESPECIFICACION_TECNICA.md
media/gifs/          # GIFs de señas servidos como estáticos
```

## Funcionalidades (RF01–RF11 de la tesis)

1. Página principal con búsqueda instantánea (autocompletado por prefijo; índice LOWER + varchar_pattern_ops)
2. Vista detallada de palabra: GIF en bucle + categoría + descripción de ejecución
3. Exploración por categorías
4. Abecedario dactilológico completo (27 letras como GIFs; 24 reconocibles — J, Z y Ñ son dinámicas)
5. Reconocimiento por cámara: POST /api/reconocer → landmarks → predicción → {letra, confianza}
6. Composición de palabras deletreadas (acumular letras en campo editable)
7. Guía de uso del reconocimiento
8. Métricas anónimas agregadas (contadores; sin datos personales)
9. Importación de contenido: CLI de sincronización desde API de señas + importadores JSON/CSV, sin tocar código

## Instrumentación obligatoria (para el Capítulo V de la tesis)

- Registro de latencia por predicción (captura→respuesta) exportable a CSV
- `ml/scripts/evaluar.py`: accuracy, F1 macro, precision/recall por clase, matriz de confusión (PNG) sobre el conjunto de prueba
- Umbrales objetivo: accuracy ≥ 90 %, F1 ≥ 0.90, latencia mediana ≤ 1 s

## Comandos

- Backend: `cd backend && flask --app app run --debug`
- Frontend: `cd frontend && npm run dev`
- Tests backend: `cd backend && pytest -q`
- BD local: `psql -f db/schema.sql`
- Entrenar / evaluar: `python ml/scripts/entrenar.py` / `python ml/scripts/evaluar.py`

## Estilo

- Código, comentarios y nombres en español
- Componentes React accesibles: roles ARIA, foco visible, contraste AA, textos llanos (usuarios sordos: lenguaje simple)
- No añadir dependencias pesadas sin justificación
