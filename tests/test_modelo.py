"""Pruebas del módulo que usa los modelos entrenados (app/analisis/modelo.py).

Casi todas corren sin PyTorch ni archivos de modelo. La prueba con los modelos reales tarda cerca de un minuto y
solo corre si están PyTorch y los dos .pt:  PROBAR_MODELOS=1 python -m pytest tests/test_modelo.py
"""
import os

import numpy as np
import pytest

from app.analisis import modelo


def _det(caja, mascara, puntaje):
    return {"caja": caja, "mascara": mascara, "area": int(mascara.sum()), "puntaje": puntaje}


def test_tipo_de_foto_por_el_brillo_del_fondo():
    assert modelo.tipo_de_foto(np.zeros((400, 600, 3), np.uint8)) == "fluorescencia"
    assert modelo.tipo_de_foto(np.full((400, 600, 3), 200, np.uint8)) == "campo_claro"
    # unos cuantos puntos brillantes sobre fondo negro siguen siendo fluorescencia
    foto = np.zeros((400, 600, 3), np.uint8)
    foto[100:110, 100:140] = 255
    assert modelo.tipo_de_foto(foto) == "fluorescencia"


def test_no_hay_modelos_si_faltan_los_archivos(tmp_path, monkeypatch):
    monkeypatch.setenv("MODELOS_DIR", str(tmp_path))
    assert modelo.disponible() is False


def test_preparar_imagen_reduce_toma_el_brillo_maximo_e_invierte_el_campo_claro():
    rgb = np.full((100, 200, 3), (230, 190, 200), np.uint8)          # fondo rosa claro
    rgb[40:60, 50:150] = (150, 50, 110)                              # un filamento oscuro
    cfg = {"reduccion_foto": 0.5, "usar_grises": True, "invertir_si_fondo_claro": True}
    x = modelo.preparar_imagen(rgb, cfg)
    assert x.shape == (50, 100)                                      # la mitad de ancho y de alto
    assert x[25, 50] > x[5, 5]                                       # tras invertir, el filamento queda más claro que el fondo
    sin_invertir = modelo.preparar_imagen(rgb, dict(cfg, invertir_si_fondo_claro=False))
    assert sin_invertir[25, 50] < sin_invertir[5, 5]


def test_teselas_cubren_toda_la_foto():
    pos = modelo._posiciones(1374, 640, 256)
    assert pos[0] == 0 and pos[-1] == 1374 - 640                     # la última tesela llega al borde
    assert modelo._posiciones(500, 640, 256) == [0]                  # foto más chica que la tesela


def test_se_quita_el_contorno_repetido_dentro_de_otro():
    grande = np.ones((40, 40), bool)
    dentro = np.ones((10, 10), bool)                                 # cabe entero en el grande
    aparte = np.ones((20, 20), bool)
    detecciones = [_det((0, 0, 40, 40), grande, 0.95), _det((5, 5, 15, 15), dentro, 0.80),
                   _det((100, 100, 120, 120), aparte, 0.90)]
    conservadas = modelo._quitar_repetidos(detecciones, 0.5)
    assert sorted(d["puntaje"] for d in conservadas) == [0.90, 0.95]  # se fue el que estaba dentro del grande


@pytest.mark.skipif(not (os.environ.get("PROBAR_MODELOS") and modelo.disponible()),
                    reason="necesita PyTorch, los dos .pt en model/ y PROBAR_MODELOS=1")
def test_modelos_reales_devuelven_contornos_dentro_de_la_foto():
    rng = np.random.default_rng(0)
    foto = np.zeros((600, 800, 3), np.uint8)
    for _ in range(6):                                               # algunas manchas rojas alargadas
        y, x = int(rng.integers(50, 500)), int(rng.integers(50, 700))
        foto[y:y + 12, x:x + 50] = (230, 60, 20)
    contornos, info = modelo.detectar(foto)
    assert info["modelo"] == "fluorescencia"
    for c in contornos:
        assert c.ndim == 3 and c.shape[1:] == (1, 2) and len(c) >= 3
        assert c.min() >= 0 and c[..., 0].max() <= 800 and c[..., 1].max() <= 600
