"""Detección y medición de cabezas en una imagen de fluorescencia.

La detección de este archivo es PROVISIONAL: separa las cabezas por umbral de color con
OpenCV mientras no exista el modelo Mask R-CNN entrenado. Cuando el modelo esté listo,
solo cambia `detectar_cabezas`; la medición de tamaño y color dentro de cada contorno
(`medir_cabeza`) y la estadística se quedan igual.
"""
import os

import cv2
import numpy as np
from PIL import Image

DETECCION_PROVISIONAL = True

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
    return {
        "area_px": int(np.count_nonzero(mascara)),          # RF-25
        "longitud_px": round(float(max(lado1, lado2)), 1),  # RF-22: lo que abarca la cabeza
        "indice_color": round(indice_amarillo, 4),
    }


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


def dibujar_marcas(rgb, contornos, ruta_salida, lado_maximo=1400):
    """Guarda una copia reducida con cada cabeza marcada y numerada."""
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    escala_texto = max(0.35, min(bgr.shape[:2]) / 1500)
    for numero, c in enumerate(contornos, start=1):
        cv2.drawContours(bgr, [c], -1, (255, 255, 255), 1)
        x, y, _, _ = cv2.boundingRect(c)
        cv2.putText(bgr, str(numero), (x, max(y - 2, 10)), cv2.FONT_HERSHEY_SIMPLEX,
                    escala_texto, (255, 255, 255), 1, cv2.LINE_AA)
    alto, ancho = bgr.shape[:2]
    factor = lado_maximo / max(alto, ancho)
    if factor < 1:
        bgr = cv2.resize(bgr, (int(ancho * factor), int(alto * factor)), interpolation=cv2.INTER_AREA)
    cv2.imwrite(ruta_salida, bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])


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

    contornos = detectar_cabezas(rgb)
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
        cabezas.append(medida)

    resultado["cabezas"] = cabezas
    resultado["conteo"] = len(cabezas)                       # RF-15, RF-28
    resultado["area"] = resumen([c["area_px"] for c in cabezas])
    resultado["longitud"] = resumen([c["longitud_px"] for c in cabezas])
    resultado["histograma"] = histograma([c["area_px"] for c in cabezas])  # RF-26
    resultado["grados"] = asignar_grados(cabezas)              # RF-32, RF-34

    dibujar_marcas(rgb, contornos, ruta_marcada)
    resultado["marcada"] = os.path.basename(ruta_marcada)

    if len(cabezas) < 3:
        # RF-40: contó, pero con tan pocas cabezas la clasificación por color no dice nada
        resultado["estado"] = "aviso"
        resultado["mensajes"].append(
            ("warning", "Se contaron muy pocas cabezas: la clasificación por color y la "
                        "distribución de tamaños no son confiables."))
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
