-- ============================================================
-- Seeds del abecedario dactilológico (27 letras) — SOLO DESARROLLO
--
-- - Las rutas apuntan a GIFs PLACEHOLDER claramente marcados,
--   generados por db/seeds/generar_gifs_placeholder.py. El
--   contenido real (GIFs y descripciones de ejecución) llegará
--   por el módulo de importación (RF11); aquí NO se inventa nada:
--   descripcion_ejecucion queda NULL a propósito.
-- - es_estatica = FALSE para las letras dinámicas J, Z y Ñ
--   (27 − 3 = 24 clases estáticas reconocibles por el modelo).
-- - clase_modelo sigue el mapa canónico ml/modelos/clases.json:
--   el índice es la posición de la letra en el arreglo "clases".
-- - ruta_gif se guarda relativa a media/gifs/ (la BD almacena
--   rutas, no binarios — decisión de arquitectura §4.3).
-- - Idempotente: puede re-ejecutarse sin duplicar filas.
--
-- Aplicar (tras db/schema.sql), desde la raíz del repositorio.
-- ⚠️ Este archivo es UTF-8 y contiene la letra Ñ: usa una vía que
-- preserve la codificación.
--
--   · Git Bash / Linux / macOS (Docker):
--       docker compose exec -T db psql -U lsp -d diccionario_lsp < db/seeds/abecedario.sql
--   · PowerShell (Docker) — NO uses `Get-Content |` (corrompe la Ñ):
--       docker compose cp db/seeds/abecedario.sql db:/tmp/abecedario.sql
--       docker compose exec db psql -U lsp -d diccionario_lsp -f /tmp/abecedario.sql
--   · Cliente psql nativo:
--       psql postgresql://lsp:lsp_dev@localhost:5433/diccionario_lsp -f db/seeds/abecedario.sql
--
-- Verificación: SELECT texto FROM palabra WHERE NOT es_estatica;
-- debe devolver J, Ñ y Z intactas.
-- ============================================================

BEGIN;

-- El archivo es UTF-8; fija la codificación del cliente para que
-- psql nativo en Windows (consola CP850/WIN1252) no corrompa la Ñ.
SET client_encoding = 'UTF8';

INSERT INTO categoria (nombre, descripcion)
VALUES ('Abecedario', 'Alfabeto dactilológico de la Lengua de Señas Peruana')
ON CONFLICT (nombre) DO NOTHING;

-- Las 27 letras del alfabeto español.
INSERT INTO palabra (texto, descripcion, id_categoria, es_letra, es_estatica)
SELECT v.texto,
       v.descripcion,
       (SELECT id_categoria FROM categoria WHERE nombre = 'Abecedario'),
       TRUE,
       v.es_estatica
FROM (VALUES
    ('A', 'Letra A del alfabeto dactilológico', TRUE),
    ('B', 'Letra B del alfabeto dactilológico', TRUE),
    ('C', 'Letra C del alfabeto dactilológico', TRUE),
    ('D', 'Letra D del alfabeto dactilológico', TRUE),
    ('E', 'Letra E del alfabeto dactilológico', TRUE),
    ('F', 'Letra F del alfabeto dactilológico', TRUE),
    ('G', 'Letra G del alfabeto dactilológico', TRUE),
    ('H', 'Letra H del alfabeto dactilológico', TRUE),
    ('I', 'Letra I del alfabeto dactilológico', TRUE),
    ('J', 'Letra J del alfabeto dactilológico (seña con movimiento)', FALSE),
    ('K', 'Letra K del alfabeto dactilológico', TRUE),
    ('L', 'Letra L del alfabeto dactilológico', TRUE),
    ('M', 'Letra M del alfabeto dactilológico', TRUE),
    ('N', 'Letra N del alfabeto dactilológico', TRUE),
    ('Ñ', 'Letra Ñ del alfabeto dactilológico (seña con movimiento)', FALSE),
    ('O', 'Letra O del alfabeto dactilológico', TRUE),
    ('P', 'Letra P del alfabeto dactilológico', TRUE),
    ('Q', 'Letra Q del alfabeto dactilológico', TRUE),
    ('R', 'Letra R del alfabeto dactilológico', TRUE),
    ('S', 'Letra S del alfabeto dactilológico', TRUE),
    ('T', 'Letra T del alfabeto dactilológico', TRUE),
    ('U', 'Letra U del alfabeto dactilológico', TRUE),
    ('V', 'Letra V del alfabeto dactilológico', TRUE),
    ('W', 'Letra W del alfabeto dactilológico', TRUE),
    ('X', 'Letra X del alfabeto dactilológico', TRUE),
    ('Y', 'Letra Y del alfabeto dactilológico', TRUE),
    ('Z', 'Letra Z del alfabeto dactilológico (seña con movimiento)', FALSE)
) AS v(texto, descripcion, es_estatica)
ON CONFLICT (texto, id_categoria) DO NOTHING;

-- Señas: GIF placeholder por letra; clase_modelo solo para las 24
-- estáticas (índices 0–23 de ml/modelos/clases.json), NULL para
-- las dinámicas J, Z y Ñ.
INSERT INTO sena (id_palabra, ruta_gif, descripcion_ejecucion, clase_modelo)
SELECT p.id_palabra,
       v.ruta_gif,
       NULL,                       -- pendiente de contenido real (importador)
       v.clase_modelo::smallint
FROM (VALUES
    ('A', 'abecedario/a.gif',    0),
    ('B', 'abecedario/b.gif',    1),
    ('C', 'abecedario/c.gif',    2),
    ('D', 'abecedario/d.gif',    3),
    ('E', 'abecedario/e.gif',    4),
    ('F', 'abecedario/f.gif',    5),
    ('G', 'abecedario/g.gif',    6),
    ('H', 'abecedario/h.gif',    7),
    ('I', 'abecedario/i.gif',    8),
    ('J', 'abecedario/j.gif',    NULL),
    ('K', 'abecedario/k.gif',    9),
    ('L', 'abecedario/l.gif',    10),
    ('M', 'abecedario/m.gif',    11),
    ('N', 'abecedario/n.gif',    12),
    ('Ñ', 'abecedario/enie.gif', NULL),
    ('O', 'abecedario/o.gif',    13),
    ('P', 'abecedario/p.gif',    14),
    ('Q', 'abecedario/q.gif',    15),
    ('R', 'abecedario/r.gif',    16),
    ('S', 'abecedario/s.gif',    17),
    ('T', 'abecedario/t.gif',    18),
    ('U', 'abecedario/u.gif',    19),
    ('V', 'abecedario/v.gif',    20),
    ('W', 'abecedario/w.gif',    21),
    ('X', 'abecedario/x.gif',    22),
    ('Y', 'abecedario/y.gif',    23),
    ('Z', 'abecedario/z.gif',    NULL)
) AS v(texto, ruta_gif, clase_modelo)
JOIN palabra p
  ON p.texto = v.texto
 AND p.id_categoria = (SELECT id_categoria FROM categoria WHERE nombre = 'Abecedario')
ON CONFLICT (id_palabra) DO NOTHING;

COMMIT;
