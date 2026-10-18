"""Detección y medición de espermatozoides en una imagen.

La detección la hacen los modelos Mask R-CNN entrenados en Colab (`modelo.py`). Si no están disponibles
(falta PyTorch o los archivos .pt), se usa la detección PROVISIONAL de este archivo, que separa las cabezas
por umbral de color con OpenCV, y los resultados lo avisan. La medición de tamaño y color dentro de cada contorno
(`medir_cabeza`) y la estadística son las mismas en los dos casos.

Nota: en los datos guardados la lista de espermatozoides se llama `cabezas` (así se llamaba al principio);
se conserva el nombre para que los análisis ya guardados sigan abriéndose.
"""
import logging
import os

import cv2
import numpy as np
from PIL import Image

from app.analisis import modelo

log = logging.getLogger(__name__)

DETECCION_PROVISIONAL = True     # valor por omisión; cada imagen dice con qué se analizó (resultado["detector"])

# Ruido del microscopio: objetos más chicos que esto no se cuentan (RF-16)
AREA_MINIMA_PX = 20
# Manchas grandes difusas: más grandes que N veces la mediana no son una cabeza
VECES_MEDIANA_MAXIMA = 6
# Objetos muy alargados son colas, no cabezas
ALARGAMIENTO_MAXIMO = 5.0

# Clasificación de color (RF-32): 10 grados equidistantes entre el mínimo y el máximo.
GRADOS_COLOR = 10
# True: el grado 10 es el más rojo (sano) y el 1 el más amarillo (enfermo).
# El anaranjado es un grado intermedio. Si hay que invertir la escala, se cambia aquí.
GRADO_ALTO_ES_ROJO = True

# Escala PROVISIONAL, sin calibrar: indicación del grupo de investigación (16-oct-2026):
# una raya de 300 px equivale a 5 micras, es decir, 60 px = 1 micra. Más adelante la
# escala se leerá de la raya de cada imagen; por ahora es una sola constante para todas.
PX_POR_MICRA = 60
# La imagen marcada lleva una regla de LONGITUD_REGLA_PX píxeles (de la foto original) con su valor en micras,
# para que se vea la escala que se está usando. Con 60 px por micra, 300 px son 5 micras.
LONGITUD_REGLA_PX = 300
MARGEN_REGLA_PX = 40

BINS_HISTOGRAMA = 10
FORMATOS_SIN_PERDIDA = {"BMP", "PNG", "TIFF"}


def leer_imagen(ruta):
    """Abre la imagen con Pillow y devuelve (arreglo RGB, metadatos)."""
    with Image.open(ruta) as img:
        metadatos = {
            "formato": img.format,
            "ancho": img.width,
            "alto": img.height,
            "modo": img.mode,
            "peso_kb": round(os.path.getsize(ruta) / 1024, 1),
        }
        dpi = img.info.get("dpi")
        if dpi:
            metadatos["dpi"] = f"{round(float(dpi[0]))} x {round(float(dpi[1]))}"
        rgb = np.array(img.convert("RGB"))
    return rgb, metadatos


def detectar_cabezas(rgb):
    """Devuelve la lista de contornos de las cabezas encontradas (detección provisional)."""
    r = rgb[:, :, 0]
    g = rgb[:, :, 1].astype(np.float32)

    # Píxeles brillantes en el canal rojo; Otsu elige el umbral según la imagen
    umbral, _ = cv2.threshold(r, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    umbral = max(umbral, 40)
    brillante = r > umbral
    # Cabezas rojas a amarillas: el rojo domina o empata con el verde.
    # Las colas verde-amarillo tienen más verde que rojo y quedan fuera.
    no_verde = r.astype(np.float32) >= 0.85 * g
    mascara = (brillante & no_verde).astype(np.uint8) * 255

    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, nucleo)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    candidatos = [c for c in contornos if cv2.contourArea(c) >= AREA_MINIMA_PX]
    if not candidatos:
        return []

    mediana = float(np.median([cv2.contourArea(c) for c in candidatos]))
    cabezas = []
    for c in candidatos:
        if cv2.contourArea(c) > VECES_MEDIANA_MAXIMA * mediana:
            continue
        (_, _), (lado1, lado2), _ = cv2.minAreaRect(c)
        if min(lado1, lado2) > 0 and max(lado1, lado2) / min(lado1, lado2) > ALARGAMIENTO_MAXIMO:
            continue
        cabezas.append(c)
    return cabezas


def detectar_espermatozoides(rgb):
    """Devuelve (contornos, detector, aviso): con el modelo si está disponible y, si no, con la detección provisional.
    `detector` es 'fluorescencia', 'campo_claro' o 'provisional'. `aviso` explica por qué se usó la provisional
    cuando se esperaba el modelo."""
    if modelo.disponible():
        try:
            contornos, info = modelo.detectar(rgb)
            return contornos, info["modelo"], None
        except Exception:
            log.exception("Falló el modelo; se usa la detección provisional")
            return detectar_cabezas(rgb), "provisional", "No se pudo usar el modelo; se usó la detección provisional."
    return detectar_cabezas(rgb), "provisional", None


def medir_cabeza(rgb, contorno):
    """Mide tamaño y color dentro de un contorno."""
    mascara = np.zeros(rgb.shape[:2], dtype=np.uint8)
    cv2.drawContours(mascara, [contorno], -1, 255, thickness=cv2.FILLED)
    pixeles = rgb[mascara > 0].astype(np.float32)

    r = pixeles[:, 0].mean()
    g = pixeles[:, 1].mean()
    # 0 = rojo puro, 0.5 = amarillo (rojo y verde iguales). Promedio de toda la cabeza (RF-33).
    indice_amarillo = float(g / (r + g)) if (r + g) > 0 else 0.0

    (_, _), (lado1, lado2), _ = cv2.minAreaRect(contorno)
    area_px = int(np.count_nonzero(mascara))
    longitud_px = float(max(lado1, lado2))
    return {
        "area_px": area_px,                                    # RF-25
        "longitud_px": round(longitud_px, 1),                  # RF-22: lo que abarca la cabeza
        "area_um2": round(area_px / PX_POR_MICRA ** 2, 3),
        "longitud_um": round(longitud_px / PX_POR_MICRA, 2),
        "indice_color": round(indice_amarillo, 4),
    }


def contorno_simple(contorno, tolerancia=1.5):
    """Contorno simplificado como lista de [x, y] en las coordenadas de la foto original. Se guarda con los
    resultados para dibujar sobre la imagen una zona por espermatozoide (el detalle que sale al pasar el mouse)."""
    puntos = cv2.approxPolyDP(contorno, tolerancia, True).reshape(-1, 2)
    return [[int(x), int(y)] for x, y in puntos]


def asignar_grados(cabezas):
    """Reparte el color en GRADOS_COLOR grados equidistantes entre el mínimo y el máximo (RF-32)."""
    indices = [c["indice_color"] for c in cabezas]
    minimo, maximo = min(indices), max(indices)
    ancho = (maximo - minimo) / GRADOS_COLOR
    for c in cabezas:
        if ancho == 0:
            posicion = 0
        else:
            posicion = min(int((c["indice_color"] - minimo) / ancho), GRADOS_COLOR - 1)
        # posicion 0 = el más rojo
        c["grado"] = GRADOS_COLOR - posicion if GRADO_ALTO_ES_ROJO else posicion + 1

    total = len(cabezas)
    return [
        {
            "grado": g,
            "conteo": sum(1 for c in cabezas if c["grado"] == g),
            "porcentaje": round(100 * sum(1 for c in cabezas if c["grado"] == g) / total, 1),
        }
        for g in range(GRADOS_COLOR, 0, -1)
    ]


def resumen(valores):
    arreglo = np.array(valores, dtype=float)
    return {
        "media": round(float(arreglo.mean()), 2),
        "desviacion": round(float(arreglo.std(ddof=1)), 2) if len(arreglo) > 1 else 0.0,
        "minimo": round(float(arreglo.min()), 2),
        "maximo": round(float(arreglo.max()), 2),
    }


def histograma(valores, minimo=None, maximo=None, bins=BINS_HISTOGRAMA):
    rango = None if minimo is None else (minimo, maximo if maximo > minimo else minimo + 1)
    frecuencias, bordes = np.histogram(valores, bins=bins, range=rango)
    return {"bordes": [round(float(b), 1) for b in bordes],
            "frecuencias": [int(f) for f in frecuencias]}


def dibujar_regla(bgr):
    """Dibuja abajo a la izquierda una regla de LONGITUD_REGLA_PX píxeles con lo que vale en micras.
    Va con borde negro para que se vea sobre fondos claros y oscuros."""
    alto, ancho = bgr.shape[:2]
    if ancho < LONGITUD_REGLA_PX + 2 * MARGEN_REGLA_PX or alto < 3 * MARGEN_REGLA_PX:
        return                                  # la imagen es muy chica para la regla
    micras = LONGITUD_REGLA_PX / PX_POR_MICRA
    texto = f"{LONGITUD_REGLA_PX} px = {micras:g} micras (escala provisional)"
    x0, x1 = MARGEN_REGLA_PX, MARGEN_REGLA_PX + LONGITUD_REGLA_PX
    y = alto - MARGEN_REGLA_PX
    grosor = max(3, min(alto, ancho) // 250)
    escala_texto = max(0.6, min(alto, ancho) / 900)
    for color, extra in (((0, 0, 0), 4), ((255, 255, 255), 0)):          # primero el borde, luego el trazo blanco
        cv2.line(bgr, (x0, y), (x1, y), color, grosor + extra)
        for x in (x0, x1):                                                # topes en los extremos
            cv2.line(bgr, (x, y - 3 * grosor), (x, y + 3 * grosor), color, grosor + extra)
        cv2.putText(bgr, texto, (x0, y - 5 * grosor), cv2.FONT_HERSHEY_SIMPLEX, escala_texto, color,
                    max(1, grosor // 2) + (3 if extra else 0), cv2.LINE_AA)


def _guardar_reducida(bgr, ruta, lado_maximo, calidad):
    """Guarda la imagen en JPG, reducida si su lado mayor pasa de lado_maximo (nunca se agranda)."""
    alto, ancho = bgr.shape[:2]
    factor = lado_maximo / max(alto, ancho)
    if factor < 1:
        bgr = cv2.resize(bgr, (int(ancho * factor), int(alto * factor)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(ruta, bgr, [cv2.IMWRITE_JPEG_QUALITY, calidad])


def dibujar_marcas(rgb, contornos, ruta_salida, lado_maximo=1400, ruta_ampliada=None, lado_ampliado=2800):
    """Guarda una copia reducida con cada espermatozoide marcado y numerado, y la regla de escala.
    Si se da ruta_ampliada, guarda además una copia más grande para hacer zoom en la pantalla de resultados
    (la reducida es la que usan la página y el PDF)."""
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    escala_texto = max(0.35, min(bgr.shape[:2]) / 1500)
    for numero, c in enumerate(contornos, start=1):
        # Borde oscuro debajo del trazo blanco: así se ve tanto en fondo negro como en fondo claro
        cv2.drawContours(bgr, [c], -1, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.drawContours(bgr, [c], -1, (255, 255, 255), 1, cv2.LINE_AA)
        x, y, _, _ = cv2.boundingRect(c)
        for color, grosor in (((0, 0, 0), 3), ((255, 255, 255), 1)):
            cv2.putText(bgr, str(numero), (x, max(y - 2, 10)), cv2.FONT_HERSHEY_SIMPLEX,
                        escala_texto, color, grosor, cv2.LINE_AA)
    dibujar_regla(bgr)
    if ruta_ampliada:
        _guardar_reducida(bgr, ruta_ampliada, lado_ampliado, 88)
    _guardar_reducida(bgr, ruta_salida, lado_maximo, 90)


def analizar_imagen(ruta, nombre, ruta_marcada):
    """Analiza una imagen y devuelve un diccionario con resultados y avisos (RF-37 a RF-41)."""
    resultado = {"nombre": nombre, "mensajes": [], "cabezas": []}
    try:
        rgb, metadatos = leer_imagen(ruta)
    except Exception:
        resultado.update(estado="no_analizada", metadatos={})
        resultado["mensajes"].append(
            ("danger", "No se pudo abrir el archivo como imagen. No se analizó."))
        return resultado

    resultado["metadatos"] = metadatos
    if metadatos["formato"] not in FORMATOS_SIN_PERDIDA:
        resultado["mensajes"].append(
            ("warning", f"La imagen está en {metadatos['formato']}, un formato con compresión. "
                        "El color y los bordes pueden alterarse; usa BMP, PNG o TIFF."))

    contornos, detector, aviso = detectar_espermatozoides(rgb)
    resultado["detector"] = detector
    if aviso:
        resultado["mensajes"].append(("warning", aviso))
    if not contornos:
        # RF-38 y RF-41: decir claramente que no se analizó, en lugar de dar un resultado dudoso
        resultado["estado"] = "no_analizada"
        resultado["mensajes"].append(
            ("danger", "No se encontraron espermatozoides o la imagen es de mala calidad. "
                       "No es factible analizar la imagen."))
        return resultado

    cabezas = []
    for numero, c in enumerate(contornos, start=1):
        medida = medir_cabeza(rgb, c)
        medida["numero"] = numero
        medida["contorno"] = contorno_simple(c)
        cabezas.append(medida)

    resultado["cabezas"] = cabezas
    resultado["conteo"] = len(cabezas)                       # RF-15, RF-28
    resultado["area"] = resumen([c["area_px"] for c in cabezas])
    resultado["longitud"] = resumen([c["longitud_px"] for c in cabezas])
    resultado["area_um"] = resumen([c["area_um2"] for c in cabezas])
    resultado["longitud_um"] = resumen([c["longitud_um"] for c in cabezas])
    resultado["histograma"] = histograma([c["area_px"] for c in cabezas])  # RF-26
    resultado["grados"] = asignar_grados(cabezas)              # RF-32, RF-34

    ruta_ampliada = os.path.splitext(ruta_marcada)[0] + "_ampliada.jpg"
    dibujar_marcas(rgb, contornos, ruta_marcada, ruta_ampliada=ruta_ampliada)
    resultado["marcada"] = os.path.basename(ruta_marcada)
    resultado["marcada_ampliada"] = os.path.basename(ruta_ampliada)       # para el zoom de la pantalla de resultados

    if len(cabezas) < 3:
        # RF-40: contó, pero con tan pocos espermatozoides la distribución de tamaños no dice nada
        resultado["estado"] = "aviso"
        resultado["mensajes"].append(
            ("warning", "Se contaron muy pocos espermatozoides: la distribución de tamaños "
                        "no es confiable."))
    else:
        resultado["estado"] = "ok"
        resultado["mensajes"].append(("success", "La imagen fue analizada con éxito."))  # RF-39
    return resultado


def promedios_entre_imagenes(imagenes):
    """RF-27: por cada rango de tamaño, el promedio de células entre imágenes,
    con rangos tomados del mínimo y máximo de todas."""
    analizadas = [img for img in imagenes if img["cabezas"]]
    if len(analizadas) < 2:
        return None
    areas = [c["area_px"] for img in analizadas for c in img["cabezas"]]
    minimo, maximo = min(areas), max(areas)
    por_imagen = [histograma([c["area_px"] for c in img["cabezas"]], minimo, maximo)
                  for img in analizadas]
    bordes = por_imagen[0]["bordes"]
    promedios = np.mean([h["frecuencias"] for h in por_imagen], axis=0)
    return {"bordes": bordes, "promedios": [round(float(p), 2) for p in promedios],
            "imagenes": len(analizadas)}
