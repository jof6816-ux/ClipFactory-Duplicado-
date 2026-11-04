# ClipFactory — copia de trabajo

Copia de trabajo basada en el ZIP fuente de ClipFactory aportado en esta conversación, con el motor FFmpeg separado en `workers/`.

Incluye los archivos originales del ZIP y `workers/worker.py`, `workers/Dockerfile`, `workers/requirements.txt` y `workers/README.md`.

IMPORTANTE: este ZIP no crea por sí solo un repositorio GitHub ni despliega servicios. Para desplegar el worker se necesita publicar estos archivos en un repositorio GitHub y configurar la variable privada `SUPABASE_SERVICE_KEY` en Railway. Nunca guardes esa clave en el repositorio.

El worker usa detección de cambios de escena; no realiza análisis semántico con IA, no genera voz por sí solo y no publica en redes sociales.
