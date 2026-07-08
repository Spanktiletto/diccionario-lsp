"""Importador de contenido (RF11) — herramienta interna de línea de comandos.

Permite ampliar el vocabulario sin modificar el código fuente:

    python -m importador importar lote.json [--solo-validar]
    python -m importador importar lote.csv  [--solo-validar]
    python -m importador sincronizar [--url URL] [--token TOKEN] [--solo-validar]

Formato de registro (JSON: lista u objeto {"senas": [...]} — también se
acepta la clave "señas"; CSV: una columna por campo):

    palabra                (obligatorio)  texto en español (≤ 120 caracteres)
    categoria              (obligatorio)  categoría temática (≤ 80 caracteres)
    descripcion            (opcional)     descripción de la palabra (≤ 255)
    descripcion_ejecucion  (opcional)     cómo se ejecuta la seña (≤ 500)
    ruta_gif               (*)            ruta relativa a media/gifs/ (≤ 255)
    gif_url                (*)            URL del GIF a descargar (tope 10 MB)
    es_letra               (opcional)     si es letra, una sola mayúscula
    es_estatica            (opcional)     false para señas con movimiento
    clase_modelo           (opcional)     índice 0-23; SOLO letras estáticas
                                          (es_letra=true y es_estatica=true)

    (*) se exige exactamente uno de ruta_gif o gif_url.

Semántica de actualización: al reimportar una palabra existente, los
campos AUSENTES del registro conservan el valor actual en la BD
(es_letra, es_estatica, clase_modelo, descripciones); solo se
sobrescribe lo que el registro especifica. Cada registro se procesa en
su propia subtransacción: un registro inválido o con error de BD no
afecta a los demás del lote.

Este módulo NUNCA genera contenido: solo carga lo que recibe.
"""
