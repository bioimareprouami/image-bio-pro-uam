# BioImage-Repro UAM

Plataforma web con inteligencia artificial para el análisis de imágenes de microscopía de fluorescencia de espermatozoides. A partir de una fotografía, el sistema detecta cada espermatozoide, lo cuenta, mide su tamaño, calcula la estadística descriptiva de la muestra y entrega los resultados en pantalla, en CSV y en PDF.

Proyecto Institucional UAM Iztapalapa.

## Contenido

- [Funcionalidades](#funcionalidades)
- [Arquitectura](#arquitectura)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Configuración](#configuración)
- [Modelos](#modelos)
- [Pruebas](#pruebas)
- [Estado y limitaciones](#estado-y-limitaciones)
- [Documentación](#documentación)
- [Trabajo futuro](#trabajo-futuro)
- [Autoría](#autoría)

## Funcionalidades

### Análisis de imágenes

Las imágenes son de microscopía de fluorescencia sobre fondo negro. En cada una aparecen las cabezas de los espermatozoides (en rojo o anaranjado), sus colas (líneas largas verde-amarillas), manchas rojas difusas y, en ocasiones, cabezas encimadas.

- **Detección:** una red neuronal de segmentación por instancias obtiene el contorno de cada espermatozoide e ignora el fondo y las manchas.
- **Conteo:** número de espermatozoides detectados en cada imagen.
- **Medición:** área en píxeles y largo del espermatozoide visible (el lado mayor del rectángulo mínimo que lo encierra), con su equivalente en micrómetros.
- **Estadística descriptiva:** media, desviación estándar, mínimo y máximo, y un histograma de tamaños por imagen. Con varias imágenes se agrega el histograma del promedio.
- **Imagen marcada:** la fotografía con cada contorno numerado y una regla de escala. Se puede ampliar con un visor de zoom, y al pasar el cursor sobre un espermatozoide se muestran su número, su área y su largo.
- **Exportación:** CSV con una fila por espermatozoide y un PDF con los resultados de todas las imágenes del análisis.
- **Avisos:** el sistema indica cuando una imagen no pudo analizarse, cuando el resultado es poco confiable (por ejemplo, con menos de tres espermatozoides) y cuando se usó la detección provisional.
- **Color:** se calcula y se conserva en cada análisis, pero no se muestra en los resultados.

Se pueden cargar hasta 10 imágenes por análisis, en formato BMP, PNG o TIFF (JPG se acepta con aviso, porque la compresión modifica el resultado). Las imágenes cargadas se eliminan al terminar el análisis.

### Sitio web

- **Páginas:** Inicio, Nosotros, Aliados, Infografías, Videos, Inteligencia Artificial, Contacto y aviso de privacidad, con menú tipo hamburguesa.
- **Idiomas:** español e inglés, con traducción automática mediante el servicio de traducción de Google.
- **Cuentas:** registro e inicio de sesión con correo electrónico y contraseña. Las contraseñas se guardan cifradas y los formularios llevan protección CSRF. La recuperación de contraseña envía por correo (SMTP) un enlace de un solo uso que dura una hora.
- **Análisis privado:** cada persona ve únicamente sus propios análisis, en "Mis análisis". De cada uno se conservan el PDF y una copia reducida de la imagen marcada.
- **Imagen de prueba:** permite probar el análisis sin cargar una fotografía propia.
- **Infografías:** cuadros que se abren en una ventana ampliada con la imagen y su texto.
- **Videos:** los 15 videos del curso, agrupados en dos secciones (desarrollo de la red neuronal y desarrollo del sitio web), con reproductor de YouTube, lista del curso y marca de videos vistos, que se guarda en el navegador de cada persona.
- **Contacto:** formulario con nombre, correo y mensaje. Los mensajes se guardan en la base de datos.
- **Contador de visitantes:** se muestra en el pie de página y cuenta una vez por sesión del navegador, sin guardar datos personales.

## Arquitectura

```
Navegador  ->  Flask (páginas, cuentas, carga de imagen)  ->  Red de segmentación (PyTorch)
                          |                                          |
                          +->  Base de datos (SQLite)                +->  Medición por espermatozoide
                                                                     |
                                                                     +->  Gráficas, CSV y PDF
```

### Modelo

- Se usan **dos redes Mask R-CNN** de torchvision (licencia BSD), ajustadas con *transfer learning* a partir de pesos preentrenados: una para fotografías de fondo oscuro (fluorescencia) y otra para fotografías de fondo claro (campo claro). El sitio mide el brillo de cada fotografía y elige el modelo.
- La imagen se corta en teselas con traslape, cada tesela pasa por la red, se descartan los contornos cortados en el borde de la tesela, se unen los resultados y se eliminan los contornos repetidos.
- La red solo localiza. **El tamaño se mide con código** (OpenCV y numpy) dentro de cada contorno, de modo que el resultado es verificable.
- **Entrenamiento:** en Google Colab, con el cuaderno `entrenamiento/entrenar_mask_rcnn.ipynb`. En el servidor solo se hace inferencia, en CPU.
- **Reentrenamiento:** el modelo no aprende en línea. Para nuevas imágenes, otras tinciones u otro tipo de célula se reentrena en Colab y se vuelven a cargar los pesos.
- Los archivos de los modelos (`.pt`, unos 176 MB cada uno) no están en Git. Ver [`model/README.md`](model/README.md).

### Sitio

- **Flask** con plantillas **Jinja2** y **Bootstrap**, sin framework de frontend.
- **Cuentas:** Flask-Login. **Formularios:** Flask-WTF con protección CSRF.
- **Base de datos:** SQLite con Flask-SQLAlchemy.
- **Gráficas:** Chart.js en la página y matplotlib en el PDF. **PDF:** fpdf2. **CSV:** módulo `csv` de Python.
- **Videos:** `<iframe>` de YouTube.

### Despliegue

- Servidor virtual (VPS) con Docker: un contenedor `web` (Flask con Gunicorn) y otro `nginx` (proxy inverso y HTTPS con Certbot). El hosting compartido no sirve, porque no puede ejecutar Flask con PyTorch.
- Un solo proceso de Gunicorn con 4 hilos, para cargar los modelos una sola vez. Los análisis esperan turno, de modo que solo uno usa la CPU a la vez.
- Tiempo máximo de 1800 s en Gunicorn y en Nginx, y límite de subida de 300 MB (10 imágenes BMP sin compresión).
- Tamaño recomendado: 2 vCPU y de 2 a 4 GB de RAM. Los tiempos de análisis dependen del servidor y conviene medirlos en el equipo real.

La guía completa está en [`docs/despliegue.md`](docs/despliegue.md).

## Estructura del repositorio

```
app/              sitio en Flask: rutas, plantillas, estilos y lógica de análisis
app/analisis/     detección con los modelos, medición, CSV y PDF
boceto/           prototipo estático del sitio
deploy/           configuración de Nginx
docs/             documentación del proyecto
entrenamiento/    cuaderno de Colab con el que se entrenan los modelos
model/            archivos de los modelos entrenados (.pt, fuera de Git)
scripts/          herramientas auxiliares (preanotador de imágenes e imagen de prueba)
tests/            pruebas automáticas
```

## Instalación y ejecución

En Windows, con PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run --debug
```

El sitio queda en `http://127.0.0.1:5000`. La base de datos, los PDF y las imágenes marcadas se guardan en `instance/`, que no se sube a Git.

Para usar los modelos reales hay que instalar PyTorch para CPU (`requirements-modelo.txt`) y copiar los dos archivos `.pt` a `model/`. Sin ellos, el sitio funciona con una detección provisional por umbral de color y lo avisa en los resultados.

Con Docker:

```bash
docker compose up -d --build
```

## Configuración

Variables de entorno (en el servidor van en un archivo `.env` que no se sube a Git):

| Variable | Uso |
|---|---|
| `SECRET_KEY` | Clave secreta de Flask. Obligatoria en producción. |
| `MODELOS_DIR` | Carpeta con los archivos `.pt`. Por omisión, `model/`. |
| `TORCH_HILOS` | Hilos que usa PyTorch en cada análisis. Por omisión, hasta 4 según las CPU. |
| `MAIL_SERVIDOR`, `MAIL_PUERTO`, `MAIL_USUARIO`, `MAIL_REMITENTE`, `MAIL_CLAVE` | Servidor SMTP para recuperar la contraseña. Sin ellos, la recuperación avisa que no está disponible. |
| `MOSTRAR_TEMPORIZADOR` | Con `1`, muestra un temporizador en la pantalla de espera. Solo para desarrollo. |

## Modelos

| Archivo | Tipo de fotografía | Origen |
|---|---|---|
| `fluorescencia.pt` | Fondo oscuro | Entrenado en Colab con 4 fotografías y 258 etiquetas |
| `campo_claro.pt` | Fondo claro | Entrenado en Colab con 4 fotografías y 45 etiquetas |

Son modelos **preliminares**, entrenados con pocas imágenes, y los resultados lo indican. Cada archivo guarda sus pesos y la configuración con la que se entrenó (tamaño de tesela, traslape, reducción de la fotografía, umbrales), y el sitio lee todo de ahí, por lo que un modelo se reemplaza sin cambiar el código.

## Pruebas

```powershell
python -m pytest
```

Las pruebas se ejecutan sin PyTorch ni modelos. La prueba con los modelos reales solo corre si están instalados PyTorch y los dos archivos `.pt` en `model/`, con la variable `PROBAR_MODELOS=1`.

## Estado y limitaciones

- **Escala en micras provisional:** se usa 60 px = 1 µm, sin calibrar con el equipo real. Mientras no haya una calibración medida, la medida en píxeles es el dato principal y las micras son aproximadas. Ver [`docs/integracion-modelos.md`](docs/integracion-modelos.md).
- **Modelos preliminares:** entrenados con pocas imágenes. No tienen validez científica y deben validarse con fotografías nuevas antes de usarse en resultados.
- **Conteos aproximados:** en zonas con muchos espermatozoides juntos, el modelo puede repetir o partir contornos y omitir algunos.
- **Qué se mide:** el contorno cubre el espermatozoide visible completo, con parte de la cola, no solo la cabeza.
- **Falsos positivos:** el modelo puede marcar fibras o manchas brillantes, y siempre devuelve una respuesta aunque la imagen no sea de espermatozoides.
- **Medidas de cabeza a cola y aviso de imagen ajena:** aún no están implementados.
- **Mensajes de contacto:** se guardan en la base de datos y todavía no se envían por correo.
- **Contenido:** el aviso de privacidad y varios textos, infografías y videos son marcadores de posición hasta contar con el material definitivo.

## Documentación

- [`docs/requisitos.md`](docs/requisitos.md): requisitos funcionales y no funcionales.
- [`docs/despliegue.md`](docs/despliegue.md): despliegue en un VPS con Docker, HTTPS, actualización y respaldo.
- [`docs/integracion-modelos.md`](docs/integracion-modelos.md): integración de los modelos, limitaciones y escala en micras.
- [`docs/versionado.md`](docs/versionado.md): reglas de versionado.
- [`CHANGELOG.md`](CHANGELOG.md): historial de versiones.
- [`model/README.md`](model/README.md): archivos de los modelos.

## Trabajo futuro

- **Reentrenamiento** con un lote mayor y más variado de imágenes, con validación en fotografías nuevas.
- **Calibración de la escala** de las imágenes con una regla de calibración del equipo.
- **Clasificación de control contra tratamiento** a partir de la forma, el tamaño y la distribución de tamaños de las células.
- **Red neuronal multimodal** que combine las imágenes con datos numéricos de la misma muestra (AnnData/Scanpy). Primero hay que confirmar su viabilidad con los datos disponibles.

## Autoría

Proyecto Institucional UAM Iztapalapa. ImageBioPro. Octubre, 2026.

El contenido del sitio se distribuye bajo la licencia Creative Commons Attribution-NonCommercial 4.0.
