# Diccionario Web de la Lengua de Señas Peruana (LSP)

Aplicación web **pública** para consultar palabras de la Lengua de Señas Peruana y reconocer, mediante la cámara, las señas estáticas del alfabeto dactilológico usando Deep Learning.

Acompaña la tesis *"Implementación de un diccionario web de la Lengua de Señas Peruana aplicando Deep Learning para el reconocimiento automático de señas, Arequipa – 2026"* (UCSM). La especificación completa del sistema está en [docs/ESPECIFICACION_TECNICA.md](docs/ESPECIFICACION_TECNICA.md), que es la **fuente de verdad** de toda decisión técnica.

## Funcionalidades

- 🔍 Búsqueda de palabras en español con autocompletado por prefijo
- 🎞️ Visualización de cada seña como GIF animado en bucle, con su categoría y descripción de ejecución
- 🗂️ Exploración del vocabulario por categorías temáticas
- 🔤 Abecedario dactilológico completo (27 letras; J, Z y Ñ, por ser dinámicas, solo se consultan como GIF)
- 📷 Reconocimiento en tiempo real de las 24 señas estáticas del alfabeto con la cámara del navegador
- ✍️ Composición de palabras deletreadas letra a letra
- 📖 Guía de uso del módulo de reconocimiento
- 📊 Métricas de uso anónimas y agregadas (sin datos personales)
- 🔄 Importación de contenido por CLI (API de señas, JSON o CSV) sin tocar el código

## Principios inviolables

- **Sin usuarios:** no hay login, registro, roles, sesiones ni panel administrativo. Todo es de libre acceso y la base de datos no contiene tablas de usuarios.
- **Privacidad:** los fotogramas de la cámara se procesan y se **descartan**; jamás se almacenan imágenes de las personas. Del dataset de entrenamiento solo se guardan vectores de landmarks, nunca fotos.
- **Accesibilidad:** interfaz visual, de lenguaje claro y conforme a WCAG 2.1 nivel AA.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React + Vite + Tailwind CSS (SPA responsive) |
| Backend | Python 3.11+, Flask, API REST JSON |
| Base de datos | PostgreSQL (3 tablas: `categoria`, `palabra`, `sena`) |
| IA | OpenCV · MediaPipe Hands (21 landmarks) · TensorFlow/Keras (red densa 63→128→64→24) |
| Pruebas | pytest (backend, cobertura ≥ 70 %) · Vitest + React Testing Library (frontend) |

## Estructura del proyecto

```
backend/app/         # Flask: rutas API, lógica de negocio, integración del modelo
backend/importador/  # CLI: sincronizar desde API de señas, importar JSON/CSV
backend/tests/       # pytest
frontend/            # React + Vite + Tailwind (SPA)
ml/dataset/          # vectores de landmarks etiquetados (nunca imágenes)
ml/scripts/          # capturar_muestras.py, entrenar.py, evaluar.py
ml/modelos/          # modelo entrenado (.keras, no versionado) + clases.json
db/                  # schema.sql y seeds del alfabeto
docs/                # ESPECIFICACION_TECNICA.md
media/gifs/          # GIFs de señas servidos como estáticos
```

## Puesta en marcha (desarrollo)

### Requisitos

- Python 3.11+
- Node.js 20+
- Docker (solo para la base de datos local) — o PostgreSQL 16 nativo

### 1. Base de datos

```bash
docker compose up -d          # levanta PostgreSQL local
```

Aplicar el esquema y los seeds del abecedario con el `psql` del propio
contenedor (no requiere cliente en el host). Los archivos son UTF-8 y
contienen la letra Ñ: usa una vía que preserve la codificación.

En PowerShell (⚠️ no uses `Get-Content |`: corrompe la Ñ):

```powershell
docker compose cp db/schema.sql db:/tmp/schema.sql
docker compose cp db/seeds/abecedario.sql db:/tmp/abecedario.sql
docker compose exec db psql -U lsp -d diccionario_lsp -f /tmp/schema.sql
docker compose exec db psql -U lsp -d diccionario_lsp -f /tmp/abecedario.sql
```

En Git Bash / Linux / macOS:

```bash
docker compose exec -T db psql -U lsp -d diccionario_lsp < db/schema.sql
docker compose exec -T db psql -U lsp -d diccionario_lsp < db/seeds/abecedario.sql
```

O, si tienes el cliente `psql` instalado:

```bash
psql postgresql://lsp:lsp_dev@localhost:5432/diccionario_lsp -f db/schema.sql
psql postgresql://lsp:lsp_dev@localhost:5432/diccionario_lsp -f db/seeds/abecedario.sql
```

Verificación rápida — deben salir las 27 letras y las 3 dinámicas (J, Ñ, Z) intactas:

```bash
docker compose exec -T db psql -U lsp -d diccionario_lsp -c "SELECT COUNT(*) AS letras FROM palabra WHERE es_letra;"
docker compose exec -T db psql -U lsp -d diccionario_lsp -c "SELECT texto FROM palabra WHERE NOT es_estatica ORDER BY texto;"
```

Los GIFs placeholder del abecedario ya están versionados en
`media/gifs/abecedario/`. Para regenerarlos (requiere Pillow):

```bash
pip install pillow
python db/seeds/generar_gifs_placeholder.py
```

### 2. Backend

En PowerShell (Windows):

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env    # y ajustar si hace falta
flask --app app run --debug
```

En Git Bash / Linux / macOS:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
flask --app app run --debug
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Pruebas

Cada bloque parte de la raíz del repositorio:

```bash
cd backend
pytest -q          # backend (cobertura ≥ 70 %)
```

```bash
cd frontend
npm test           # frontend
```

### 5. IA (entrenamiento y evaluación)

```bash
python ml/scripts/capturar_muestras.py   # captura vectores de landmarks (nunca imágenes)
python ml/scripts/entrenar.py            # entrena la red densa 63→128→64→24
python ml/scripts/evaluar.py             # accuracy, F1, precision/recall, matriz de confusión
```

## Contenido

En desarrollo solo se cargan los **seeds del alfabeto** con GIFs *placeholder* claramente marcados (ver el paso [1. Base de datos](#1-base-de-datos)). El vocabulario real se incorpora con el módulo de importación:

```bash
cd backend
python -m importador sincronizar          # desde la API de señas configurada en .env
python -m importador importar datos.json  # lote JSON
python -m importador importar datos.csv   # lote CSV
```

## Estado

🚧 En desarrollo por etapas (plan de sprints en la especificación técnica).
