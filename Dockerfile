FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/imagebio

COPY requirements.txt requirements-modelo.txt ./
RUN pip install -r requirements.txt  && pip install --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple -r requirements-modelo.txt

COPY app ./app
COPY run.py .

# La base de datos, los PDF y las imágenes marcadas viven en instance/ (volumen)
VOLUME /srv/imagebio/instance

EXPOSE 8000

# Un solo proceso con varios hilos: así los modelos (cientos de MB) se cargan una vez y no por proceso.
# Los análisis esperan turno dentro del módulo (solo uno usa la CPU a la vez); los hilos permiten que el resto
# del sitio siga respondiendo mientras tanto.
# Timeout alto: analizar 10 imágenes grandes con los modelos puede tardar varios minutos.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "4", "--timeout", "1800", "app:crear_app()"]
