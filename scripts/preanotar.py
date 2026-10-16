"""Pre-anotador: propone el contorno de cada cabeza para corregirlo después a mano.

Sirve para fluorescencia con muchas cabezas rojas o anaranjadas sobre fondo negro.
En imágenes con un solo espermatozoide marca puntos sueltos del fondo: ahí no se usa.
No es el modelo ni el detector final: es un borrador que ahorra dibujar los
contornos desde cero. Deja casi solo cabezas de verdad, pero se le pasan las
más tenues; esas se agregan a mano al corregir.

Genera, en la carpeta de salida:
  anotaciones.json   formato COCO, para importar en CVAT
  revision/*.png     cada imagen con los contornos en verde, para echar un vistazo

Uso:
  python scripts/preanotar.py "ruta/a/la/carpeta" --patron "*epifluorescencia*.bmp"
"""
import argparse
import glob
import json
import os

import cv2
import numpy as np
from PIL import Image

# Las fotos del microscopio son enormes y las entrega el grupo
Image.MAX_IMAGE_PIXELS = None


def detectar_cabezas(rgb, umbral=40, grosor=5, area_min=60, area_max=1500,
                     pico_min=130, solidez_min=0.6):
    """Devuelve los contornos de las cabezas probables en una imagen de fluorescencia."""
    rojo = rgb[:, :, 0]

    # Top-hat: deja lo pequeño y brillante y quita las manchas rojas grandes y difusas
    grande = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))
    realce = cv2.subtract(rojo, cv2.morphologyEx(rojo, cv2.MORPH_OPEN, grande))
    mascara = (realce > umbral).astype(np.uint8) * 255

    # Apertura: borra lo más delgado que "grosor" píxeles, o sea las colas
    nucleo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grosor, grosor))
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, nucleo)

    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cabezas = []
    for c in contornos:
        area = cv2.contourArea(c)
        if not area_min <= area <= area_max:
            continue
        casco = cv2.contourArea(cv2.convexHull(c))
        if casco == 0 or area / casco < solidez_min:
            continue  # formas ramificadas: colas que se cruzan
        relleno = np.zeros(rojo.shape, np.uint8)
        cv2.drawContours(relleno, [c], -1, 255, cv2.FILLED)
        if rojo[relleno > 0].max() < pico_min:
            continue  # sin un centro brillante: es cola
        cabezas.append(c)
    return cabezas


def a_poligono(contorno):
    """Contorno de OpenCV a la lista plana [x1, y1, x2, y2, ...] que pide COCO."""
    simple = cv2.approxPolyDP(contorno, 1.0, True).reshape(-1, 2)
    if len(simple) < 3:
        return None
    return [float(v) for punto in simple for v in punto]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", help="carpeta con las imágenes")
    ap.add_argument("--patron", default="*.bmp", help="qué archivos tomar (por defecto *.bmp)")
    ap.add_argument("--salida", default=os.path.join("instance", "preanotacion"))
    ap.add_argument("--umbral", type=int, default=40, help="qué tanto debe destacar del fondo")
    ap.add_argument("--pico-min", type=int, default=130, help="rojo mínimo del centro; bájalo para captar cabezas tenues")
    args = ap.parse_args()

    archivos = [f for f in sorted(glob.glob(os.path.join(args.carpeta, args.patron)))
                if not os.path.basename(f).startswith("._")]  # basura que deja macOS al copiar
    if not archivos:
        raise SystemExit("No encontré imágenes con ese patrón.")

    os.makedirs(os.path.join(args.salida, "revision"), exist_ok=True)
    coco = {"images": [], "annotations": [], "categories": [{"id": 1, "name": "cabeza"}]}
    id_anotacion = 1

    for id_imagen, ruta in enumerate(archivos, 1):
        with Image.open(ruta) as img:
            rgb = np.array(img.convert("RGB"))
        alto, ancho = rgb.shape[:2]
        nombre = os.path.basename(ruta)
        cabezas = detectar_cabezas(rgb, umbral=args.umbral, pico_min=args.pico_min)

        coco["images"].append({"id": id_imagen, "file_name": nombre, "width": ancho, "height": alto})
        usadas = []
        for c in cabezas:
            poligono = a_poligono(c)
            if poligono is None:
                continue
            x, y, w, h = cv2.boundingRect(c)
            coco["annotations"].append({
                "id": id_anotacion, "image_id": id_imagen, "category_id": 1,
                "segmentation": [poligono], "area": float(cv2.contourArea(c)),
                "bbox": [x, y, w, h], "iscrowd": 0,
            })
            id_anotacion += 1
            usadas.append(c)

        vista = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        cv2.drawContours(vista, usadas, -1, (0, 255, 0), 3)
        escala = 1400 / max(alto, ancho)
        vista = cv2.resize(vista, (int(ancho * escala), int(alto * escala)))
        # imencode/tofile en vez de imwrite: OpenCV falla con acentos en rutas de Windows
        destino = os.path.join(args.salida, "revision", os.path.splitext(nombre)[0] + ".png")
        cv2.imencode(".png", vista)[1].tofile(destino)
        print(f"{nombre}: {len(usadas)} cabezas propuestas")

    with open(os.path.join(args.salida, "anotaciones.json"), "w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False)
    print(f"\nListo. Resultados en {args.salida}")


if __name__ == "__main__":
    main()
