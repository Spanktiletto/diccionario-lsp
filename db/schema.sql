-- ============================================================
-- Diccionario Web de la Lengua de Señas Peruana (LSP)
-- Esquema físico de la base de datos (PostgreSQL)
--
-- Fuente: docs/ESPECIFICACION_TECNICA.md §4.4.2 (transcripción
-- exacta). Tres tablas bastan para el alcance definido; nótese
-- la ausencia deliberada de cualquier tabla de usuarios o
-- sesiones: la aplicación es pública.
--
-- Aplicar:
--   psql postgresql://lsp:lsp_dev@localhost:5432/diccionario_lsp -f db/schema.sql
-- ============================================================

CREATE TABLE categoria (
    id_categoria  SERIAL PRIMARY KEY,
    nombre        VARCHAR(80)  NOT NULL UNIQUE,
    descripcion   VARCHAR(255)
);

CREATE TABLE palabra (
    id_palabra    SERIAL PRIMARY KEY,
    texto         VARCHAR(120) NOT NULL,
    descripcion   VARCHAR(255),
    id_categoria  INTEGER NOT NULL REFERENCES categoria(id_categoria),
    es_letra      BOOLEAN NOT NULL DEFAULT FALSE,
    es_estatica   BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (texto, id_categoria)
);

-- Soporta el autocompletado por prefijo (RF01) con buen rendimiento.
CREATE INDEX idx_palabra_texto ON palabra (LOWER(texto) varchar_pattern_ops);

CREATE TABLE sena (
    id_sena                SERIAL PRIMARY KEY,
    id_palabra             INTEGER NOT NULL UNIQUE REFERENCES palabra(id_palabra),
    ruta_gif               VARCHAR(255) NOT NULL,
    descripcion_ejecucion  VARCHAR(500),
    clase_modelo           SMALLINT
);
