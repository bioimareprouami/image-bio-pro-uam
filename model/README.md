# Modelos entrenados

Aquí van los dos modelos que usa el sitio. **No están en Git** (pesan unos 176 MB cada uno): se copian a mano.

| Archivo | Qué es | Sale de |
|---|---|---|
| `fluorescencia.pt` | Fotos de fondo oscuro | `modelo_cabezas.pt` de `corrida_02` (cuaderno 0.3.1) |
| `campo_claro.pt` | Fotos de fondo claro | `modelo_cabezas.pt` de `corrida_04` (cuaderno 0.5.0, perfil `campo_claro`) |

Cada archivo trae los pesos y la configuración con la que se entrenó (tamaño de tesela, traslape, reducción de la foto, umbral de seguridad...). El sitio lee todo de ahí, así que se puede cambiar un modelo por otro más nuevo sin tocar el código.

Si faltan los archivos (o PyTorch no está instalado), el sitio sigue funcionando con la detección provisional por umbral de color y lo avisa en los resultados.

La carpeta se puede cambiar con la variable de entorno `MODELOS_DIR`.
