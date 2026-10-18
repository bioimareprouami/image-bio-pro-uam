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

## 2. Copiar los modelos y levantar el sitio

Los dos modelos entrenados (`fluorescencia.pt` y `campo_claro.pt`, unos 176 MB cada uno) **no están en Git**. Se copian a la carpeta `model/` del servidor antes de levantar el sitio, por ejemplo desde tu computadora:

```bash
scp model/fluorescencia.pt model/campo_claro.pt USUARIO@IP-del-VPS:~/imagebio/model/
```

`docker-compose.yml` monta esa carpeta dentro del contenedor, así que cambiar un modelo por uno nuevo no obliga a reconstruir la imagen: se copia el archivo y `docker compose restart web`. Si faltan los archivos, el sitio funciona con la detección provisional y lo avisa en los resultados.

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
- **Timeout:** 1800 s en Gunicorn y en Nginx, porque analizar 10 imágenes con los modelos puede tardar varios minutos. **Hay que medir los tiempos en el VPS real**: en una computadora de escritorio un análisis tarda de 10 a 50 segundos por imagen de 1792 px, y un VPS con una sola CPU puede tardar varias veces más. Si con 10 imágenes se pasa del tiempo razonable, hay que limitar imágenes por subida o pasar el análisis a segundo plano.
- **Proceso:** un solo proceso de Gunicorn con 4 hilos, para cargar los modelos una vez. Los análisis esperan turno (uno a la vez), así que varios usuarios analizando a la vez se encolan.
- **PyTorch:** `requirements-modelo.txt` instala `torch` y `torchvision` para CPU desde el índice de CPU de PyTorch (la imagen crece alrededor de 1 GB). Los hilos que usa se limitan con la variable `TORCH_HILOS` (por omisión, hasta 4 según las CPU).
- **Memoria:** los modelos se cargan la primera vez que se usan y se quedan en memoria (unos 400 MB entre los dos, más el análisis). Revisar la RAM del VPS con `docker stats`.
