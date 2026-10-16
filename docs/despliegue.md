# Despliegue en el VPS con Docker

Dos contenedores: `web` (Flask con Gunicorn) y `nginx` (proxy inverso y HTTPS). Los datos (base de datos, PDF, imágenes marcadas) viven en el volumen `datos`, así que reconstruir la imagen no los borra.

## 1. Preparar el VPS (una sola vez)

Conéctate por SSH y ejecuta:

```bash
# Docker con el plugin de compose
curl -fsSL https://get.docker.com | sh

# Código
git clone <URL-del-repositorio> imagebio
cd imagebio

# Clave secreta del sitio (no se sube a Git)
echo "SECRET_KEY=$(openssl rand -hex 32)" > .env
```

## 2. Levantar el sitio

```bash
docker compose up -d --build
docker compose ps          # los dos servicios deben estar "running"
docker compose logs -f web # para ver errores
```

El sitio responde en `http://IP-del-VPS`.

## 3. HTTPS con Certbot

Requiere que el dominio ya apunte a la IP del VPS.

```bash
docker run --rm \
  -v imagebio_certbot-web:/var/www/certbot \
  -v imagebio_certbot-certs:/etc/letsencrypt \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d TU-DOMINIO -m TU-CORREO --agree-tos --no-eff-email
```

(Los volúmenes se llaman `<carpeta>_certbot-web`; si la carpeta no se llama `imagebio`, ajusta el prefijo con `docker volume ls`.)

Después, en `deploy/nginx.conf`, cambia el bloque del puerto 80 para que redirija a HTTPS y agrega un bloque `listen 443 ssl` con:

```
ssl_certificate     /etc/letsencrypt/live/TU-DOMINIO/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/TU-DOMINIO/privkey.pem;
```

y el mismo `location /` de proxy. Luego `docker compose restart nginx`.

Renovación (el certificado dura 90 días): programa en `crontab -e`

```
0 3 1 * * cd ~/imagebio && docker run --rm -v imagebio_certbot-web:/var/www/certbot -v imagebio_certbot-certs:/etc/letsencrypt certbot/certbot renew -q && docker compose restart nginx
```

## 4. Actualizar el sitio

```bash
cd ~/imagebio
git pull
docker compose up -d --build
```

## 5. Respaldo de los datos

```bash
docker run --rm -v imagebio_datos:/datos -v $(pwd):/respaldo alpine \
  tar czf /respaldo/datos-$(date +%F).tar.gz -C /datos .
```

## Ajustes que dependen de medir en el servidor

- **Límite de subida:** 300 MB en Nginx y en `MAX_CONTENT_LENGTH` (10 imágenes BMP sin compresión). Si se decide otro tope, cambiar los dos.
- **Timeout:** 300 s en Gunicorn y en Nginx. Probar con 10 BMP reales; ajustar `--workers` según la RAM.
- **Modelo (PyTorch):** al agregarlo, subir `torch` y `torchvision` (versión CPU) a `requirements.txt`, copiar los pesos de `model/` en el `Dockerfile` y limitar los hilos con `torch.set_num_threads`. Revisar RAM y espacio en disco, porque la imagen crece varios GB.
