# Historial de versiones

Las reglas para numerar las versiones están en [`docs/versionado.md`](docs/versionado.md). Cada commit de `main` que cambia el sitio es una versión. Los que solo tocan documentos no llevan versión.

**En producción: 1.0.0.** El repositorio va en 1.12.0.

## 1.12.0 (3 de noviembre de 2026)

- Cabecera: pasa a una banda azul institucional, con los logos y el nombre del proyecto en blanco, al estilo de la cabecera de la UNAM.
- Botones principales: de verde con letra negra a azul institucional con letra blanca, para que haya contraste. El enlace "Ver todas las infografías" se ve más oscuro y en negrita.
- Analizar imagen: sin cuenta, el aviso dice "Para el análisis de imágenes se requiere el acceso con una cuenta" y hay dos botones, "Iniciar sesión" y "Crear cuenta", que llevan a cada formulario de la página de acceso.
- Inicio: nuevos textos en la descripción, el objetivo, las tres tarjetas del recorrido de una imagen, los resultados y la sección de análisis. La red se describe como de aprendizaje supervisado y el estudio estadístico como descriptivo.
- Correo de contacto oficial: bioimareprouami@gmail.com, en el pie, en Contacto y en el aviso de recuperar contraseña.
- Tipografía: títulos en Playfair Display y texto en Source Sans 3, con una escala de tamaños más marcada en todo el sitio.
- Colores: azul marino con detalles dorados y mayor contraste en textos, bordes y botones; la cabecera lleva degradado.
- Infografías: el bloque de la página de IA se llama "Infografías ImageRepro UAM", va centrado y deja ocho huecos en dos filas.
- Contador de visitantes en el pie: suma una vez por sesión del navegador y no guarda datos de la persona. Usa la tabla nueva `contador`, que se crea sola al arrancar.
- Aliados: fotos del Dr. Roberto Carlos Lazzarini Lechuga y del Dr. Jorge Eduardo Vieyra Durán, y un icono de perfil sin foto para el Dr. Saúl Jiménez Jiménez, mientras llega la suya.

## 1.11.1 (30 de octubre de 2026)

- Configuración: `requirements-modelo.txt` ya no dice que PyTorch es opcional, porque el sitio necesita los modelos para analizar.

## 1.11.0 (28 de octubre de 2026)

- Recuperar contraseña: Entrar lleva el enlace "¿Olvidaste tu contraseña?". La persona escribe su correo y recibe un enlace para elegir una contraseña nueva; el enlace dura una hora y sirve una sola vez.
- La respuesta es la misma exista o no la cuenta, para no revelar quién está registrado.
- El sitio manda correo por SMTP con las variables `MAIL_SERVIDOR`, `MAIL_PUERTO`, `MAIL_USUARIO`, `MAIL_REMITENTE` y `MAIL_CLAVE`, que van en el archivo `.env` del servidor (no se sube a Git). Si faltan, se avisa a la persona que escriba al correo de contacto.

## 1.10.3 (28 de octubre de 2026)

- Pie de página: los logos del proyecto y de la UAM se muestran en blanco para que no se pierdan en el fondo azul.

## 1.10.2 (28 de octubre de 2026)

- Pie de página: más discreto, con letra, espacios y logos más chicos, y en celular se ve como una sola columna centrada.

## 1.10.1 (28 de octubre de 2026)

- Pie de página: se quita la fila de enlaces a las páginas y las redes oficiales de la UAM Iztapalapa pasan a ser iconos blancos (Facebook, X, Instagram y YouTube) en lugar de texto.
- Fondo: el difuminado de color ya no se repite, así que no se corta con una línea en las páginas largas como Nosotros.

## 1.10.0 (28 de octubre de 2026)

- Pie de página: pasa a una banda oscura centrada con el nombre del proyecto, el domicilio, el teléfono, el correo, los logos del proyecto y de la UAM, los enlaces, las redes y la leyenda legal.
- Correo de contacto provisional: uamiztapalapa62@gmail.com, en el pie y en Contacto.
- Aliados: los colaboradores aparecen al final de la lista.

## 1.9.0 (27 de octubre de 2026)

- Aliados: se agregan las fotos de Isaac Emanuel Mani Arellano y de Gerardo Mejia Hernandez, y Gerardo Mejia Hernandez aparece como colaborador.

## 1.8.1 (27 de octubre de 2026)

- Videos: los videos 1, 2 y 3 vuelven a quedar comentados en `app/sitio.py`; la página muestra el marcador hasta que se publiquen.
- Aliados: se quitan Gerardo Blancas Flores, Juan José Pérez Rivero, Marcela Vergara Onofre y Jesús Eduardo Barrera Morales.

## 1.8.0 (26 de octubre de 2026)

- Infografías y Videos pasan a ser dos páginas distintas, cada una con su entrada en el menú y en el pie.
- Infografías (`/infografias`) muestra solo el mosaico y su ventana. Videos (`/videos`) muestra el reproductor y la lista del curso.
- La página de Inteligencia Artificial enlaza solo a las infografías.

## 1.7.0 (26 de octubre de 2026)

- Infografías y videos: los videos 1, 2 y 3 del curso (módulo 1) ya se reproducen en la página, con el reproductor de YouTube. Los otros 12 siguen como marcador hasta que se suban.

## 1.6.2 (26 de octubre de 2026)

- Nosotros: cada párrafo de la sección "Cómo está hecha" termina con "(Artículo en preparación)".

## 1.6.1 (25 de octubre de 2026)

- Infografías y videos: el video seleccionado ya no lleva la franja verde a la izquierda; se distingue por el borde y el fondo.

## 1.6.0 (25 de octubre de 2026)

- Aliados: se agregan las fotos de la Dra. Sheila Irais Peña Corona, la Dra. Edith Arenas Ríos, la Dra. María del Rosario Tarragó Castellanos, el Dr. Juan Villegas Cortez y Luis Enrique Perez Caltzontzin, en cuadros del mismo tamaño.
- Aliados muestra la foto del equipo arriba de la lista.

## 1.5.1 (25 de octubre de 2026)

- El video 1 queda comentado en `app/sitio.py`: la página lo muestra como marcador hasta que el video se publique.

## 1.5.0 (25 de octubre de 2026)

- Infografías y videos: el video 1 del curso (El problema y la imagen digital) ya se reproduce en la página, con el reproductor de YouTube. Los otros 14 siguen como marcador hasta que se suban.

## 1.4.7 (25 de octubre de 2026)

- Aliados: Luis aparece con su nombre completo, Luis Enrique Perez Caltzontzin.

## 1.4.6 (25 de octubre de 2026)

- El logo de la UAM se separa de la orilla y queda a la misma altura que el logo del proyecto.
- El logo del proyecto es el ícono de la pestaña del navegador y de la pantalla de inicio del celular.

## 1.4.5 (25 de octubre de 2026)

- El encabezado muestra el logo del proyecto en lugar del círculo.
- El logo de la UAM Unidad Iztapalapa va en la esquina superior izquierda del encabezado; en tableta y celular queda arriba del nombre para no encimarse.

## 1.4.4 (25 de octubre de 2026)

- El encabezado del sitio dice "Plataforma Web con Inteligencia Artificial para análisis de imágenes de microscopía de fluorescencia" debajo del nombre.
- En celular el texto baja de línea y el círculo del logo ya no se corta.

## 1.4.3 (25 de octubre de 2026)

- Aliados: la foto va primero y todas son cuadradas y del mismo tamaño, así las filas quedan alineadas aunque el nombre ocupe más de una línea.

## 1.4.2 (25 de octubre de 2026)

- La guía de versionado pide que el mensaje de cada commit lleve el tipo, dos puntos, el número de versión y el resumen: `fix: v1.4.2 corrige el enlace de contacto`.

## 1.4.1 (25 de octubre de 2026)

- Se agregan las reglas para numerar las versiones (`docs/versionado.md`) y este historial de versiones.
- Cada commit de `main` pasa a ser una versión, y los commits del 24 de octubre quedan etiquetados de la 1.0.1 a la 1.4.0.

## 1.4.0 (24 de octubre de 2026)

- Infografías y videos muestra los 15 videos del curso en dos secciones: desarrollo de la red neuronal convolucional y desarrollo del sitio web.
- Reproductor grande, botones de anterior y siguiente, pestañas por sección y marca de videos vistos, que se guarda en el navegador de cada persona.

## 1.3.0 (24 de octubre de 2026)

- El pie lleva los datos de la UAM Unidad Iztapalapa y sus redes oficiales.
- Contacto con la dirección y el teléfono de Iztapalapa.
- Aliados muestra las 14 personas del proyecto con su cargo, y cada tarjeta puede llevar el enlace a Google Académico.
- Nosotros lleva el texto del grupo y la sección "Cómo está hecha".

## 1.2.2 (24 de octubre de 2026)

- El plan de videos del curso pasa a 15 videos: frontend y backend en el módulo 3 y el cuaderno de Colab en dos videos del módulo 4.

## 1.2.0 (24 de octubre de 2026)

- El proyecto pasa a llamarse BioImage-Repro UAM en el sitio, el informe en PDF y la documentación.

## 1.0.2 (24 de octubre de 2026)

- La descripción del proyecto del video 1 se dice con otras palabras.

## 1.0.0 (21 de octubre de 2026)

Primera versión en producción.

- Detección con los dos modelos, conteo, área y largo, con media y desviación estándar.
- Gráfica de distribución por imagen y, con varias imágenes, la de promedios.
- Hasta 10 imágenes por análisis, con barra de progreso, avisos y un solo PDF.
- Descarga de CSV y PDF, y "Mis análisis" para volver a ver un análisis.
- Imagen marcada con zoom y datos de cada espermatozoide al pasar el mouse.
- Cuentas, páginas informativas y sitio en español e inglés.

Los commits del 21 al 23 de octubre que van después de la 1.0.0 (configuración de Nginx) son anteriores a este esquema y no tienen versión.
