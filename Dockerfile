FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/imagebio

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY run.py .

# La base de datos, los PDF y las imágenes marcadas viven en instance/ (volumen)
VOLUME /srv/imagebio/instance

EXPOSE 8000

# Timeout alto: el análisis de varias imágenes grandes tarda
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "300", "app:crear_app()"]
