"""Genera app/static/muestras/prueba.png: una imagen sintética parecida a las de fluorescencia.

Fondo negro, cabezas de rojo a amarillo, colas verde-amarillo y puntos de ruido.
Sirve como imagen de prueba del sitio (RF-52) mientras no haya una real
autorizada para publicarse.

Uso:  python scripts/generar_imagen_prueba.py
"""
import os

import cv2
import numpy as np

ANCHO, ALTO = 1200, 900
CABEZAS = 45
SEMILLA = 7

DESTINO = os.path.join(os.path.dirname(__file__), "..", "app", "static", "muestras", "prueba.png")


def main():
    azar = np.random.default_rng(SEMILLA)
    lienzo = np.zeros((ALTO, ANCHO, 3), dtype=np.uint8)  # BGR para OpenCV

    centros = []
    while len(centros) < CABEZAS:
        x, y = azar.integers(60, ANCHO - 60), azar.integers(60, ALTO - 60)
        if all((x - cx) ** 2 + (y - cy) ** 2 > 70 ** 2 for cx, cy in centros):
            centros.append((int(x), int(y)))

    for x, y in centros:
        angulo = float(azar.uniform(0, 360))
        # Cola verde-amarillo, larga y delgada
        rad = np.deg2rad(angulo)
        largo = int(azar.integers(80, 140))
        fin = (int(x + largo * np.cos(rad)), int(y + largo * np.sin(rad)))
        cv2.line(lienzo, (x, y), fin, (40, 200, 150), 2, cv2.LINE_AA)

        # Cabeza: de rojo (verde 0) a amarillo-anaranjado (verde alto)
        verde = int(azar.integers(0, 190))
        ejes = (int(azar.integers(9, 14)), int(azar.integers(5, 8)))
        cv2.ellipse(lienzo, (x, y), ejes, angulo, 0, 360, (20, verde, 235), -1, cv2.LINE_AA)

    # Ruido del microscopio: puntos chicos que no deben contarse (RF-16)
    for _ in range(120):
        punto = (int(azar.integers(0, ANCHO)), int(azar.integers(0, ALTO)))
        cv2.circle(lienzo, punto, 1, (60, 60, 180), -1)

    lienzo = cv2.GaussianBlur(lienzo, (3, 3), 0)
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    cv2.imwrite(DESTINO, lienzo)
    print(f"Imagen de prueba con {CABEZAS} cabezas guardada en {os.path.normpath(DESTINO)}")


if __name__ == "__main__":
    main()
