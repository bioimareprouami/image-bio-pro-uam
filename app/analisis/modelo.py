"""Detección de espermatozoides con los modelos Mask R-CNN entrenados en Colab.

Hay un modelo por tipo de foto: `fluorescencia.pt` (fondo oscuro) y `campo_claro.pt` (fondo claro). Cada archivo
trae los pesos y la configuración con la que se entrenó (tamaño de tesela, traslape, reducción de la foto, umbral de
seguridad...); aquí se lee todo de ahí. El procedimiento es el mismo del cuaderno de entrenamiento
(`entrenamiento/entrenar_mask_rcnn.ipynb`, función `detectar`), y tiene que seguir igual a él:

1. Se mide el brillo de la foto para elegir el modelo.
2. Se prepara la foto como en el entrenamiento: reducción, brillo máximo de los canales y, en campo claro, inversión.
3. Se corta en teselas con traslape y cada una pasa por la red.
4. Se juntan los resultados, se quitan los duplicados entre teselas y los contornos repetidos dentro de uno mismo.

PyTorch se importa solo al usarlo: sin PyTorch o sin los archivos de los modelos, `disponible()` da False y el sitio
usa la detección provisional de `medicion.py`. Este módulo no depende de Flask.
"""
import importlib.util
import logging
import os
import threading

import cv2
import numpy as np

log = logging.getLogger(__name__)

ARCHIVOS = {"fluorescencia": "fluorescencia.pt", "campo_claro": "campo_claro.pt"}
UMBRAL_BRILLO_FONDO_CLARO = 127     # mediana del brillo (0 a 255) arriba de la cual la foto es de fondo claro
UMBRAL_MINIMO = 0.05                # las detecciones con menos seguridad ni se guardan
LOTE_TESELAS = 2

_BLOQUEO_CARGA = threading.Lock()
_BLOQUEO_INFERENCIA = threading.Lock()   # un análisis a la vez: la CPU del servidor no da para dos
_CARGADOS = {}


def carpeta_modelos():
    """Carpeta con los .pt: la variable MODELOS_DIR o, si no existe, la carpeta `model/` del proyecto."""
    return os.environ.get("MODELOS_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "model")


def _ruta(tipo):
    return os.path.join(carpeta_modelos(), ARCHIVOS[tipo])


def disponible():
    """True si PyTorch está instalado y están los dos archivos de modelo."""
    if not all(importlib.util.find_spec(m) for m in ("torch", "torchvision")):
        return False
    return all(os.path.isfile(_ruta(t)) for t in ARCHIVOS)


def motivo_no_disponible():
    """Texto que explica por qué los modelos no se pueden usar, o None si están disponibles."""
    faltan_libs = [m for m in ("torch", "torchvision") if not importlib.util.find_spec(m)]
    if faltan_libs:
        return f"PyTorch no está instalado (falta {', '.join(faltan_libs)})."
    faltan = [ARCHIVOS[t] for t in ARCHIVOS if not os.path.isfile(_ruta(t))]
    if faltan:
        return f"No se encontraron los archivos {', '.join(faltan)} en {carpeta_modelos()}."
    return None


def tipo_de_foto(rgb):
    """'campo_claro' si el fondo es claro, 'fluorescencia' si es oscuro (mediana del brillo máximo por píxel)."""
    pequena = cv2.resize(rgb, None, fx=1 / 8, fy=1 / 8, interpolation=cv2.INTER_AREA)
    brillo = float(np.median(pequena.max(axis=2)))
    return "campo_claro" if brillo > UMBRAL_BRILLO_FONDO_CLARO else "fluorescencia"


# ---------- Carga ----------

def _congelar_normalizacion(modulo, eps, torch, FrozenBatchNorm2d):
    """Cambia cada BatchNorm2d por una FrozenBatchNorm2d con el eps del entrenamiento (como en el cuaderno)."""
    for nombre, hijo in modulo.named_children():
        if isinstance(hijo, torch.nn.BatchNorm2d):
            setattr(modulo, nombre, FrozenBatchNorm2d(hijo.num_features, eps=eps))
        else:
            _congelar_normalizacion(hijo, eps, torch, FrozenBatchNorm2d)


def _construir_red(cfg):
    import torch
    from torchvision.models.detection import maskrcnn_resnet50_fpn
    from torchvision.models.detection.anchor_utils import AnchorGenerator
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchvision.models.detection.mask_rcnn import MaskRCNNPredictor
    from torchvision.ops import MultiScaleRoIAlign
    from torchvision.ops.misc import FrozenBatchNorm2d

    anclas = tuple(cfg["anclas"])
    lado = int(cfg["lado"] * (cfg.get("escala_entrada") or 1.0))
    red = maskrcnn_resnet50_fpn(
        weights=None, weights_backbone=None, min_size=lado, max_size=lado,
        rpn_anchor_generator=AnchorGenerator(sizes=tuple((s,) for s in anclas),
                                             aspect_ratios=((0.5, 1.0, 2.0),) * len(anclas)),
        box_detections_per_img=cfg["max_detecciones"], box_nms_thresh=cfg["umbral_nms_cajas"],
        mask_roi_pool=MultiScaleRoIAlign(featmap_names=["0", "1", "2", "3"],
                                         output_size=cfg.get("roi_mascara") or 14, sampling_ratio=2))
    red.roi_heads.box_predictor = FastRCNNPredictor(red.roi_heads.box_predictor.cls_score.in_features, 2)
    red.roi_heads.mask_predictor = MaskRCNNPredictor(red.roi_heads.mask_predictor.conv5_mask.in_channels, 256, 2)
    _congelar_normalizacion(red, cfg["bn_eps"], torch, FrozenBatchNorm2d)
    return red


def _hilos():
    pedidos = os.environ.get("TORCH_HILOS")
    return max(1, int(pedidos)) if pedidos else max(1, min(4, os.cpu_count() or 1))


def _cargar(tipo):
    """Carga un modelo la primera vez que se pide y lo guarda en memoria."""
    with _BLOQUEO_CARGA:
        if tipo not in _CARGADOS:
            import torch
            from torch.serialization import safe_globals
            from torch.torch_version import TorchVersion
            torch.set_num_threads(_hilos())
            # Carga segura (solo tensores y datos simples). El archivo guarda la versión de PyTorch con un tipo
            # propio, TorchVersion, que se permite aparte.
            with safe_globals([TorchVersion]):
                contenido = torch.load(_ruta(tipo), map_location="cpu", weights_only=True)
            cfg = contenido["config"]
            if "bn_eps" not in cfg:
                raise RuntimeError(f"{ARCHIVOS[tipo]} no trae bn_eps: es de una versión vieja del cuaderno y "
                                   "no calcularía lo mismo que en el entrenamiento. Hay que exportarlo de nuevo.")
            red = _construir_red(cfg)
            resultado = red.load_state_dict(contenido["state_dict"], strict=False)
            faltan = [k for k in resultado.missing_keys if not k.endswith("num_batches_tracked")]
            if faltan or resultado.unexpected_keys:
                raise RuntimeError(f"{ARCHIVOS[tipo]} no coincide con la red: faltan {faltan[:3]}, "
                                   f"sobran {list(resultado.unexpected_keys)[:3]}")
            red.eval()
            _CARGADOS[tipo] = (red, cfg)
            log.info("Modelo %s cargado (cuaderno %s, tesela %s, reducción %s)", tipo,
                     cfg.get("version_cuaderno"), cfg["lado"], cfg.get("reduccion_foto") or 1.0)
        return _CARGADOS[tipo]


# ---------- Preparación y geometría ----------

def preparar_imagen(rgb, cfg):
    """RGB -> lo que ve la red. Igual a `preparar_imagen` del cuaderno de entrenamiento."""
    reduccion = cfg.get("reduccion_foto") or 1.0
    if reduccion != 1.0:
        alto, ancho = rgb.shape[:2]
        rgb = cv2.resize(rgb, (int(round(ancho * reduccion)), int(round(alto * reduccion))),
                         interpolation=cv2.INTER_AREA)
    x = rgb.max(axis=2) if cfg.get("usar_grises", True) else rgb
    if cfg.get("invertir_si_fondo_claro") and np.median(x) > UMBRAL_BRILLO_FONDO_CLARO:
        x = 255 - x
    return np.ascontiguousarray(x)


def _posiciones(n, lado, paso):
    if n <= lado:
        return [0]
    return list(range(0, n - lado, paso)) + [n - lado]


def _interseccion(a, b):
    ax0, ay0, ax1, ay1 = a["caja"]
    bx0, by0, bx1, by1 = b["caja"]
    x0, y0, x1, y1 = max(ax0, bx0), max(ay0, by0), min(ax1, bx1), min(ay1, by1)
    if x1 <= x0 or y1 <= y0:
        return 0
    return int(np.count_nonzero(a["mascara"][y0 - ay0:y1 - ay0, x0 - ax0:x1 - ax0]
                                & b["mascara"][y0 - by0:y1 - by0, x0 - bx0:x1 - bx0]))


def _iou(a, b):
    inter = _interseccion(a, b)
    return inter / (a["area"] + b["area"] - inter) if inter else 0.0


def _quitar_repetidos(detecciones, umbral_contenido):
    """De mayor a menor seguridad, descarta un contorno si al menos `umbral_contenido` de su área ya está cubierta
    por uno que se conservó (la red a veces dibuja dos veces el mismo espermatozoide)."""
    conservadas = []
    for d in sorted(detecciones, key=lambda d: -d["puntaje"]):
        if all(_interseccion(d, k) / d["area"] < umbral_contenido for k in conservadas):
            conservadas.append(d)
    return conservadas


# ---------- Detección ----------

def _inferir(red, arreglo, cfg):
    """La foto ya preparada, por teselas con traslape. Devuelve las detecciones en coordenadas de esa foto."""
    import torch

    lado, solape = cfg["lado"], cfg["solape"]
    alto, ancho = arreglo.shape[:2]
    paso = lado - solape
    teselas = [(x, y) for y in _posiciones(alto, lado, paso) for x in _posiciones(ancho, lado, paso)]
    encontrados = []
    with torch.inference_mode():
        for i in range(0, len(teselas), LOTE_TESELAS):
            grupo = teselas[i:i + LOTE_TESELAS]
            entradas = []
            for x, y in grupo:
                t = arreglo[y:y + lado, x:x + lado]
                if t.shape[0] < lado or t.shape[1] < lado:
                    relleno = [(0, lado - t.shape[0]), (0, lado - t.shape[1])] + [(0, 0)] * (t.ndim - 2)
                    t = np.pad(t, relleno)
                t = np.repeat(t[None], 3, axis=0) if t.ndim == 2 else t.transpose(2, 0, 1)
                entradas.append(torch.from_numpy(np.ascontiguousarray(t)).float().div(255))
            for (x, y), salida in zip(grupo, red(entradas)):
                mascaras = (salida["masks"][:, 0] > 0.5).numpy()
                puntajes = salida["scores"].float().numpy()
                for m, puntaje in zip(mascaras, puntajes):
                    if puntaje < UMBRAL_MINIMO:
                        continue
                    filas, cols = np.flatnonzero(m.any(1)), np.flatnonzero(m.any(0))
                    if len(filas) == 0:
                        continue
                    f0, f1, c0, c1 = filas[0], filas[-1] + 1, cols[0], cols[-1] + 1
                    # Si toca un borde interno de la tesela puede estar cortado: lo verá entero la tesela vecina
                    if ((c0 <= 0 and x > 0) or (c1 >= lado and x + lado < ancho)
                            or (f0 <= 0 and y > 0) or (f1 >= lado and y + lado < alto)):
                        continue
                    local = m[f0:f1, c0:c1][:max(alto - (y + f0), 0), :max(ancho - (x + c0), 0)]
                    if local.size == 0 or not local.any():
                        continue
                    encontrados.append({"caja": (x + c0, y + f0, x + c0 + local.shape[1], y + f0 + local.shape[0]),
                                        "mascara": local, "area": int(local.sum()), "puntaje": float(puntaje)})
    # Duplicados entre teselas: se queda el de mayor seguridad
    conservados = []
    for d in sorted(encontrados, key=lambda d: -d["puntaje"]):
        if all(_iou(d, k) < 0.5 for k in conservados):
            conservados.append(d)
    if cfg.get("umbral_contenido"):
        conservados = _quitar_repetidos(conservados, cfg["umbral_contenido"])
    return conservados


def _a_contorno(det, reduccion):
    """Máscara local -> contorno de OpenCV (N, 1, 2) en las coordenadas de la foto original."""
    contornos, _ = cv2.findContours(det["mascara"].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contornos:
        return None
    mayor = max(contornos, key=cv2.contourArea).astype(np.float32)
    mayor += np.array([[[det["caja"][0], det["caja"][1]]]], np.float32)
    mayor = np.round(mayor / reduccion).astype(np.int32)
    return mayor if len(mayor) >= 3 else None


def detectar(rgb):
    """Analiza una foto RGB con el modelo que le toca. Devuelve (contornos, info).

    `contornos` es la lista de contornos de OpenCV en las coordenadas de la foto original, ya filtrados con el umbral
    de seguridad guardado en el modelo. `info` dice qué modelo se usó y con qué configuración."""
    tipo = tipo_de_foto(rgb)
    red, cfg = _cargar(tipo)
    reduccion = cfg.get("reduccion_foto") or 1.0
    with _BLOQUEO_INFERENCIA:
        detecciones = _inferir(red, preparar_imagen(rgb, cfg), cfg)
    umbral = cfg.get("umbral_deteccion", 0.5)
    contornos, puntajes = [], []
    for d in sorted((d for d in detecciones if d["puntaje"] >= umbral), key=lambda d: (d["caja"][1], d["caja"][0])):
        c = _a_contorno(d, reduccion)
        if c is not None:
            contornos.append(c)
            puntajes.append(round(d["puntaje"], 3))
    info = {"modelo": tipo, "version_cuaderno": cfg.get("version_cuaderno"), "umbral": umbral,
            "reduccion": reduccion, "puntajes": puntajes}
    return contornos, info
