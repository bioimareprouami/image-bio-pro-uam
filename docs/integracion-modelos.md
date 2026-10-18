# Integración de los modelos al sitio

Describe cómo el sitio usa los modelos entrenados, qué limitaciones tienen y cómo se resuelve la escala en micras.

## Modelos

Los modelos se entrenan en Colab con `entrenamiento/entrenar_mask_rcnn.ipynb`:

- **Fluorescencia** (fondo oscuro): teselas de 512 px.
- **Campo claro** (fondo claro): fotografías reducidas a la mitad y teselas de 640 px.

Los archivos `.pt` (unos 176 MB cada uno) no están en Git: se montan como volumen de solo lectura. Ver [`model/README.md`](../model/README.md).

## Funcionamiento

El módulo `app/analisis/modelo.py`:

1. **Carga** los dos modelos una sola vez, la primera vez que se usan, y los conserva en memoria.
2. **Elige** el modelo midiendo el brillo de la fotografía: la mediana del valor máximo de rojo, verde y azul. Si es mayor que 127, el fondo es claro.
3. **Prepara** la fotografía igual que en el entrenamiento: reducción, valor máximo de los canales e inversión en campo claro.
4. **Corta** la imagen en teselas con traslape y pasa cada una por la red, sin calcular gradientes.
5. **Descarta** los contornos que tocan el borde interno de una tesela, porque la tesela vecina los verá completos.
6. **Une** los resultados, elimina los contornos repetidos y devuelve los contornos en las coordenadas de la fotografía original.

Cada archivo `.pt` trae su configuración: `lado`, `solape`, `anclas`, `roi_mascara` (si falta, 14), `reduccion_foto`, `bn_eps`, `umbral_deteccion` y `umbral_contenido`.

`app/analisis/medicion.py` usa el modelo cuando está disponible y, si no, la detección provisional por umbral de color con OpenCV. Cada imagen guarda con qué detector se analizó. El conteo, el área, el largo, el histograma, el CSV y el PDF salen de los contornos.

El análisis se ejecuta dentro de la petición, imagen por imagen, y los análisis esperan turno (solo uno usa la CPU a la vez). Gunicorn y Nginx tienen un tiempo máximo de 1800 s. Si en el servidor 10 imágenes tardaran demasiado, se puede limitar el tamaño o el número de imágenes por subida, o pasar el análisis a segundo plano con una página de espera.

## Qué se mide

- Los contornos cubren el espermatozoide visible completo, con parte de la cola, no solo la cabeza. En pantalla, CSV y PDF los textos dicen "espermatozoide". Dentro de los datos guardados la lista se llama `cabezas`, para que los análisis ya guardados se sigan abriendo.
- El **color** se calcula y se guarda, pero no se muestra en los resultados, el CSV ni el PDF.

## Limitaciones

- **Tiempo en el servidor.** En una computadora de escritorio se midieron unos 40 s por fotografía de 1792 px en fluorescencia y de 10 a 20 s en campo claro. Un servidor con una sola CPU puede tardar varias veces más, por lo que hay que medirlo en el equipo real.
- **Datos de entrenamiento.** Fluorescencia: 4 fotografías y 258 etiquetas. Campo claro: 4 fotografías y 45 etiquetas. Las pruebas en campo claro se hicieron con otras tomas de las mismas escenas del entrenamiento, así que no se conoce el comportamiento con otras muestras, otras tinciones o fotografías comprimidas.
- **Conteos aproximados.** En zonas con muchos espermatozoides juntos, el modelo repite o parte contornos y no encuentra algunos (en fluorescencia, cerca de 85 de cada 100 amontonados). Los conteos son aproximados.
- **Falsos positivos.** El modelo puede marcar fibras, manchas brillantes o núcleos de otras células, y siempre devuelve una respuesta.

## Escala en micras

**Por qué no se obtiene de las fotografías.** Las fotografías no traen barra de escala ni regla impresa, y la cabecera de los BMP no trae medida. De la imagen sola no se puede deducir cuánto mide un píxel sin suponer el tamaño de algo, y no se debe suponer nada del espermatozoide.

**De qué depende.** Del aumento del objetivo, del tamaño del sensor de la cámara y de cualquier adaptador, y de la resolución a la que se guarda la fotografía. Se calibra una sola vez por equipo; las personas usuarias no tienen que conocerla.

**Estado actual (provisional).** La constante `PX_POR_MICRA = 60` de `app/analisis/medicion.py` equivale a 300 px = 5 µm. La imagen marcada lleva abajo a la izquierda una regla de 300 px con el texto "300 px = 5 micras (escala provisional)", y los resultados, el CSV y el PDF avisan que la escala no está calibrada. En campo claro no hay ninguna calibración conocida.

**Solución propuesta.**

1. Una tabla de escalas en un archivo de configuración, con píxeles por micra para cada resolución. Se edita sin tocar el código y el sitio la usa en cada análisis. Si una resolución no está en la tabla, se usa la constante provisional y se indica.
2. Obtención de cada valor, de más a menos confiable: una fotografía de una regla de calibración (micrómetro de platina) tomada con el mismo microscopio y la misma cámara; la calibración del programa de la cámara; o el cálculo a partir de la ficha de la cámara y el adaptador.
3. Una herramienta auxiliar para quien mantiene el sitio: dada la fotografía de la regla y la distancia conocida entre dos marcas, calcula el valor y lo guarda en la tabla.
4. Mientras no haya un valor medido, la medida en píxeles es el dato principal y las micras se presentan como aproximadas.
5. Si las fotografías llegaran a traer una barra de escala impresa, podría leerse con procesamiento de imagen (una línea recta y larga en una esquina), sin necesidad de una red neuronal. Antes hay que revisar ejemplos reales.

**Dato por confirmar.** Si las fotografías de 1792 y de 3584 px de ancho son del mismo campo con distinta resolución, cada una necesita su propio valor (el de 3584 sería el doble). Si no lo son, la constante actual sería incorrecta para una de las dos.

## Servidor

`requirements-modelo.txt` instala PyTorch y torchvision para CPU. Los hilos de PyTorch se limitan con `TORCH_HILOS`. El `Dockerfile`, `docker-compose.yml` (volumen `model/`) y la guía [`despliegue.md`](despliegue.md) describen el despliegue.

## Pruebas

Las pruebas comprueban cada pieza sin los modelos. Las pruebas que usan los modelos reales se omiten solas si PyTorch o los archivos `.pt` no están disponibles. Con los modelos, el sitio da los mismos conteos que el cuaderno de entrenamiento.
