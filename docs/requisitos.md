# Requisitos del sistema

Especificación de requisitos de **BioImage-Repro UAM**, plataforma web con inteligencia artificial para el análisis de imágenes de microscopía de fluorescencia de espermatozoides.

Cada requisito tiene un identificador para poder citarlo en el código, las pruebas y la documentación. Los identificadores se conservan aunque un requisito se sustituya por otro, de modo que la numeración tiene huecos en los requisitos no funcionales. Las decisiones técnicas están en el [README](../README.md).

- **Requisito funcional (RF):** describe lo que el sistema hace.
- **Requisito no funcional (RNF):** describe cómo debe ser el sistema o qué condiciones debe cumplir.

## 1. Alcance

El sistema es un sitio web bilingüe (español e inglés) con dos partes:

1. **Sitio informativo:** presenta el proyecto, a las personas que participan, las infografías, los videos del curso y un formulario de contacto.
2. **Análisis de imágenes:** una red neuronal detecta cada espermatozoide en una fotografía, el sistema lo cuenta, mide su tamaño, genera la estadística descriptiva y entrega los resultados en pantalla, en CSV y en PDF.

## 2. Requisitos funcionales

### 2.1 Sitio informativo

| ID | Requisito |
|---|---|
| RF-01 | El sitio tendrá un menú tipo hamburguesa con sus secciones, entre ellas una de infografías. |
| RF-02 | La página principal llevará como título *BioImage-Repro UAM*. |
| RF-03 | El sitio estará disponible en español e inglés, con un selector ES/EN y traducción automática mediante el servicio de traducción de Google. |
| RF-04 | La sección Nosotros mostrará únicamente la pregunta "¿Qué es BioImage-Repro UAM?" y su respuesta, con el texto que proporcione el grupo. |
| RF-05 | La sección Contacto incluirá el formulario habitual con nombre, correo electrónico y mensaje. |
| RF-06 | La sección Aliados mostrará a las personas del grupo con su nombre, su fotografía y una breve reseña. |
| RF-07 | Las infografías se presentarán como cuadros. Al seleccionar uno, se abrirá una ventana ampliada con la imagen y su texto, a la manera de una publicación de blog. |
| RF-08 | El título de cada infografía se mostrará fuera de la imagen. |
| RF-09 | El sitio mostrará los 15 videos del curso (cuatro módulos de unos 20 minutos cada video) alojados en YouTube, reproducidos dentro de la misma página. |

### 2.2 Página de inteligencia artificial y cuentas

| ID | Requisito |
|---|---|
| RF-10 | La página de inteligencia artificial tendrá una imagen de fondo, una sección para cargar la imagen y un botón para analizarla. |
| RF-11 | La página podrá ofrecer parámetros ajustables si resultan necesarios. *Sustituido por RF-42.* |
| RF-12 | La página incluirá infografías como complemento, para que no quede vacía. |
| RF-13 | Para usar la red neuronal será necesario iniciar sesión. |
| RF-14 | Cada persona se registrará con su correo electrónico y una contraseña. La cuenta sirve para tener acceso al análisis y a su historial. |

### 2.3 Análisis de imágenes

| ID | Requisito |
|---|---|
| RF-15 | El sistema contará las células que aparecen en la imagen. |
| RF-16 | El sistema no contará los puntos ni las líneas del fondo, que corresponden a ruido del microscopio. |
| RF-17 | El sistema medirá cada célula. *Sustituido por RF-22 a RF-25.* |
| RF-18 | El sistema generará la gráfica de distribución de tamaños. |
| RF-19 | El sistema clasificará las células por color. *Sustituido por RF-31 a RF-34.* |
| RF-20 | Los resultados podrán descargarse en CSV y en PDF. |
| RF-21 | El modelo podrá reentrenarse y volver a cargarse en el sitio cuando se disponga de más imágenes o de otro tipo de células. |

### 2.4 Mediciones y estadística

| ID | Requisito |
|---|---|
| RF-22 | Medida 1: distancia que abarca la cabeza. |
| RF-23 | Medida 2: distancia en línea recta de la punta de la cabeza a la punta de la cola. |
| RF-24 | Medida 3: distancia real a lo largo de la cola, aunque esté doblada. En una célula doblada, la línea recta subestima la longitud. |
| RF-25 | Medida 4: área de la cabeza, en píxeles. |
| RF-26 | Para cada imagen, el sistema generará la gráfica de distribución del tamaño de la cabeza: el eje horizontal es el tamaño (área en píxeles), con mínimo y máximo tomados de esa imagen, y el eje vertical es el número de células. No se supone una forma de distribución determinada. |
| RF-27 | Cuando se analicen varias imágenes, el sistema generará una segunda gráfica con el promedio, por cada tamaño, entre las imágenes, usando el mínimo y el máximo encontrados en el conjunto. |
| RF-28 | El sistema mostrará el número de células contadas. |
| RF-29 | La pantalla y el PDF mostrarán la media y la desviación estándar. |
| RF-30 | La separación entre cabeza y cola la determina el modelo. Como estrategia de apoyo, se puede considerar cabeza lo que queda dentro de un radio fijo desde la punta (por ejemplo, 1.5 µm) y validarlo manualmente con el conjunto de entrenamiento. |

### 2.5 Clasificación por color

| ID | Requisito |
|---|---|
| RF-31 | Las células se distinguen por color: el rojo corresponde a células sanas y el amarillo a células enfermas. |
| RF-32 | El color es una variable ordinal. El sistema repartirá el color, del mínimo al máximo, en 10 grados equidistantes entre rojo y amarillo, y cada célula quedará en uno de ellos. El anaranjado no es una categoría aparte, sino un grado intermedio de la escala. El extremo de la escala que corresponde a la célula sana está por confirmar. |
| RF-33 | El color se medirá solo en la cabeza. Si dos cabezas están juntas, se promedia su color. |
| RF-34 | El resultado de color será el número y el porcentaje de células en cada grado. Actualmente el color se calcula y se conserva, pero no se muestra en los resultados. |

### 2.6 Entrada y avisos

| ID | Requisito |
|---|---|
| RF-35 | Se podrán cargar hasta 10 imágenes a la vez. |
| RF-36 | Mientras se analiza, el sistema mostrará una barra de progreso o un mensaje que indique que está trabajando. |
| RF-37 | Si la imagen no corresponde a espermatozoides, el sistema avisará que no es una imagen válida para el análisis. |
| RF-38 | Si no se encuentran espermatozoides o la calidad de la imagen es insuficiente, el sistema avisará que no es factible analizarla. |
| RF-39 | Si el análisis termina correctamente, el sistema avisará que la imagen se analizó con éxito. |
| RF-40 | El sistema mostrará avisos cuando el análisis se haya realizado sin distinguir bien la clasificación, los tamaños o la forma, o cuando haya contado sin clasificar o clasificado sin contar. |
| RF-41 | Cuando el aviso indique que la red no funcionó para una imagen, el sistema dejará claro que no la analizó, en lugar de presentar un resultado dudoso. |
| RF-42 | La interfaz de análisis tendrá únicamente el botón para ejecutar el análisis, sin parámetros que modificar. |

### 2.7 Resultados, PDF e historial

| ID | Requisito |
|---|---|
| RF-43 | El resultado se mostrará en pantalla y, al final de la página, se ofrecerá la opción de imprimir. |
| RF-44 | Si se cargan varias imágenes, el sistema generará un solo PDF con el análisis de cada una. |
| RF-45 | El PDF incluirá: nombre de la persona usuaria, fecha y hora, encabezado con logotipo, características de la imagen (metadatos), resultados, gráfica de distribución, media y desviación estándar. |
| RF-46 | El PDF de cada análisis se conservará en el servidor. |
| RF-47 | Las imágenes cargadas se eliminarán al terminar el análisis. |
| RF-48 | En su perfil, cada persona verá la lista de sus análisis anteriores ("Mis análisis"). Al abrir uno se muestra igual que al hacerlo, solo para consulta. Cada persona ve únicamente sus propios análisis. |

### 2.8 Acceso y contenido

| ID | Requisito |
|---|---|
| RF-49 | El sitio podrá consultarse sin iniciar sesión. Para analizar imágenes se requiere una cuenta, que se puede crear en el momento. |
| RF-50 | Cualquier persona podrá registrarse sin aprobación de una persona administradora. |
| RF-51 | Las personas usuarias no tendrán acceso al código de la red neuronal. |
| RF-52 | El sitio ofrecerá una imagen de prueba para que cualquier persona pueda probar el análisis sin cargar la suya y descargar su PDF. Esta función es temporal; en la versión definitiva se conserva una sola imagen. |
| RF-53 | El pie de página incluirá el aviso de privacidad, la licencia Creative Commons Attribution-NonCommercial 4.0 y los enlaces del menú. El texto del aviso lo proporciona el grupo. |

## 3. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-01 | El diseño será sencillo y funcional, con pocos colores y sin un nivel de detalle gráfico elevado. Otros sitios sirven solo como referencia de estructura, no de diseño. |
| RNF-02 | El formato de los resultados es flexible. Si una gráfica resulta compleja, basta con entregar un archivo de texto o CSV con el conteo y las medidas. |
| RNF-06 | Un tiempo de análisis de unos minutos por lote de imágenes es aceptable. |
| RNF-07 | Las imágenes de entrada deberán tener la mayor calidad posible: formato original del microscopio sin compresión (por ejemplo, TIFF o BMP) y no imágenes comprimidas por aplicaciones de mensajería. |
| RNF-09 | Si un dato de configuración cambia después (por ejemplo, los colores), se admite un ajuste menor sin rehacer el diseño. |

## 4. Restricciones

- **Datos iniciales:** se dispone de una imagen de ejemplo. El modelo inicial se entrena con unas 10 imágenes y sirve como esqueleto para mostrar el flujo completo; **no tiene validez científica**. El entrenamiento definitivo requiere un lote mayor de imágenes.
- **Formato de las imágenes de entrenamiento:** BMP. Falta confirmar en qué formato cargarán imágenes las personas usuarias del sitio.
- **Tinción de las imágenes de ejemplo:** rojo, amarillo y anaranjado. El tono de las imágenes definitivas puede ser más sutil.
- **Aprendizaje:** el modelo no aprende en línea. Para nuevas imágenes, otras tinciones u otro tipo de célula hay que reentrenarlo por separado y volver a cargar sus pesos.

## 5. Fuera de alcance

- **Distinguir control contra tratamiento** (o tejido sano contra enfermo): es una línea de trabajo posterior.
- **Red neuronal con imágenes y datos AnnData:** es un proyecto aparte. Solo se evaluará su viabilidad.

## 6. Pendientes por confirmar

| Tema | Descripción | Requisitos afectados |
|---|---|---|
| Imágenes originales | Formato, escala, peso y cantidad de las imágenes originales del microscopio, incluidas las que cargarán las personas usuarias. | RF-22 a RF-30, RNF-07 |
| Unidad de las medidas | Área en píxeles y radio de la cabeza y escala en micrómetros. Confirmar que las imágenes reales traen una barra de escala o el aumento usado. | RF-22 a RF-27, RF-30 |
| Confirmación del correo | La recuperación de la contraseña por correo ya está disponible. Falta definir si, además, se confirma el correo al registrarse. | RF-14, RF-49, RF-50 |
| Administración de usuarios | Definir si habrá una persona administradora con un panel para ver y dar de baja cuentas. | RF-50 |
| Imágenes de prueba | Cuántas imágenes de prueba se ofrecen y cuáles. | RF-52 |
| Extremo sano de la escala de color | Definir qué extremo de la escala de 10 grados corresponde a la célula sana. | RF-32 |
| Imágenes sin espermatozoides | Contar con imágenes que no sean de espermatozoides para entrenar al modelo a no marcarlas. | RF-37 |
| Ubicación de los videos | Definir en qué parte del sitio se muestran. | RF-09 |
| Contenido de Contacto | Definir si la sección lleva solo el formulario o también los datos del área. | RF-05 |
| Contenidos del sitio | Fotografías, nombres, textos, infografías, videos, logotipo y texto del pie de página. | RF-04 a RF-09, RF-45, RF-53 |
