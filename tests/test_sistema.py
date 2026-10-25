"""Pruebas del flujo completo: páginas, cuentas, análisis, resultados y descargas.

Uso:  python -m pytest
"""
import io
import os
import re

import cv2
import numpy as np
import pytest

from app import crear_app

PRUEBA = os.path.join(os.path.dirname(__file__), "..", "app", "static", "muestras", "prueba.png")


@pytest.fixture
def app(tmp_path, monkeypatch):
    # Sin modelos: así las pruebas usan la detección provisional, rápida y que no depende de PyTorch
    monkeypatch.setenv("MODELOS_DIR", str(tmp_path / "sin_modelos"))
    app = crear_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "prueba.db"),
        "CARPETA_PDF": str(tmp_path / "pdfs"),
        "CARPETA_SUBIDAS": str(tmp_path / "subidas"),
        "CARPETA_MARCADAS": str(tmp_path / "marcadas"),
    })
    return app


@pytest.fixture
def cliente(app):
    return app.test_client()


def registrar(cliente, correo="ana@ejemplo.com"):
    return cliente.post("/entrar", data={"accion": "registrar", "nombre": "Ana",
                                         "correo": correo, "clave": "secreta123"})


def imagen_bytes(ruta, formato):
    ok, datos = cv2.imencode("." + formato, cv2.imread(ruta))
    assert ok
    return io.BytesIO(datos.tobytes())


@pytest.mark.parametrize("url", ["/", "/nosotros", "/aliados", "/infografias", "/ia",
                                 "/contacto", "/entrar", "/aviso-de-privacidad"])
def test_paginas_publicas(cliente, url):
    assert cliente.get(url).status_code == 200


def test_analizar_requiere_sesion(cliente):
    respuesta = cliente.post("/analizar")
    assert respuesta.status_code == 302
    assert "/entrar" in respuesta.headers["Location"]


def test_registro_entrar_y_salir(cliente):
    assert registrar(cliente).status_code == 302
    assert b"Ana" in cliente.get("/perfil").data
    cliente.post("/salir")
    assert cliente.get("/perfil").status_code == 302
    malo = cliente.post("/entrar", data={"accion": "entrar", "correo": "ana@ejemplo.com",
                                         "clave": "otra"})
    assert "incorrectos" in malo.get_data(as_text=True)
    bueno = cliente.post("/entrar", data={"accion": "entrar", "correo": "ana@ejemplo.com",
                                          "clave": "secreta123"})
    assert bueno.status_code == 302


def test_redireccion_externa_bloqueada(cliente):
    registrar(cliente)
    cliente.post("/salir")
    respuesta = cliente.post("/entrar?next=https://malo.com", data={
        "accion": "entrar", "correo": "ana@ejemplo.com", "clave": "secreta123"})
    assert "malo.com" not in respuesta.headers["Location"]


def test_analisis_completo_y_descargas(app, cliente):
    registrar(cliente)
    respuesta = cliente.post("/analizar", data={"imagenes": [
        (imagen_bytes(PRUEBA, "bmp"), "muestra_1.bmp"),
        (imagen_bytes(PRUEBA, "png"), "muestra_2.png"),
    ]}, content_type="multipart/form-data")
    assert respuesta.status_code == 302
    url = respuesta.headers["Location"]

    pagina = cliente.get(url).get_data(as_text=True)
    assert "analizada con éxito" in pagina
    assert "Promedio entre las 2 imágenes" in pagina

    # RF-47: no quedan imágenes subidas en el servidor
    assert os.listdir(app.config["CARPETA_SUBIDAS"]) == []

    marcada = re.search(r'src="(/resultados/\d+/marcada/[^"]+)"', pagina).group(1)
    assert cliente.get(marcada).mimetype == "image/jpeg"

    csv = cliente.get(url + "/csv").get_data(as_text=True)
    assert csv.count("\n") == 1 + 2 * 45  # encabezado + 45 espermatozoides por imagen
    # El color queda declarado pero sin usar: no aparece en los resultados ni en el CSV
    assert csv.splitlines()[0].lstrip("﻿") == "imagen,espermatozoide,area_px,longitud_px,area_um2,longitud_um"
    assert "Clasificación por color" not in pagina and "Índice de color" not in pagina

    pdf = cliente.get(url + "/pdf")
    assert pdf.data.startswith(b"%PDF")


def test_jpg_con_aviso(cliente):
    registrar(cliente)
    respuesta = cliente.post("/analizar", data={"imagenes": [
        (imagen_bytes(PRUEBA, "jpg"), "foto.jpg")]}, content_type="multipart/form-data",
        follow_redirects=True)
    assert "formato con compresión" in respuesta.get_data(as_text=True)


def test_imagen_sin_cabezas_no_se_analiza(cliente):
    registrar(cliente)
    negra = io.BytesIO(cv2.imencode(".png", np.zeros((200, 200, 3), np.uint8))[1].tobytes())
    respuesta = cliente.post("/analizar", data={"imagenes": [(negra, "negra.png")]},
                             content_type="multipart/form-data", follow_redirects=True)
    assert "No es factible analizar la imagen" in respuesta.get_data(as_text=True)


def test_formato_no_permitido(cliente):
    registrar(cliente)
    respuesta = cliente.post("/analizar", data={"imagenes": [(io.BytesIO(b"hola"), "notas.txt")]},
                             content_type="multipart/form-data", follow_redirects=True)
    assert "Formato no permitido" in respuesta.get_data(as_text=True)


def test_mas_de_diez_imagenes(cliente):
    registrar(cliente)
    archivos = [(imagen_bytes(PRUEBA, "png"), f"m{i}.png") for i in range(11)]
    respuesta = cliente.post("/analizar", data={"imagenes": archivos},
                             content_type="multipart/form-data", follow_redirects=True)
    assert "como máximo 10" in respuesta.get_data(as_text=True)


def test_imagen_de_prueba(cliente):
    registrar(cliente)
    respuesta = cliente.post("/analizar/prueba", follow_redirects=True)
    assert "analizada con éxito" in respuesta.get_data(as_text=True)


def test_analisis_privados(cliente):
    registrar(cliente)
    url = cliente.post("/analizar/prueba").headers["Location"]
    cliente.post("/salir")
    registrar(cliente, "beto@ejemplo.com")
    assert cliente.get(url).status_code == 404
    assert cliente.get(url + "/pdf").status_code == 404


def test_contacto_guarda_mensaje(app, cliente):
    from app.modelos import Mensaje
    cliente.post("/contacto", data={"nombre": "Luis", "correo": "l@e.com", "mensaje": "Hola"})
    with app.app_context():
        assert Mensaje.query.count() == 1


def test_imagen_marcada_lleva_la_regla_de_escala(tmp_path):
    """La imagen marcada trae una regla de 300 px (5 micras con 60 px por micra), con su borde negro."""
    from app.analisis import medicion
    negra = np.zeros((600, 800, 3), np.uint8)
    destino = str(tmp_path / "marcada.png")
    medicion.dibujar_marcas(negra, [], destino)          # 800 px de ancho: no se reduce
    gris = cv2.cvtColor(cv2.imread(destino), cv2.COLOR_BGR2GRAY)
    y = 600 - medicion.MARGEN_REGLA_PX
    x0 = medicion.MARGEN_REGLA_PX
    largo = medicion.LONGITUD_REGLA_PX
    assert gris[y, x0 + largo // 2] == 255              # el trazo blanco de la regla
    assert gris[y, x0 + largo + 20] == 0                # termina a los 300 px
    assert medicion.LONGITUD_REGLA_PX / medicion.PX_POR_MICRA == 5


def test_imagen_muy_chica_no_lleva_regla(tmp_path):
    from app.analisis import medicion
    chica = np.zeros((100, 120, 3), np.uint8)
    destino = str(tmp_path / "chica.png")
    medicion.dibujar_marcas(chica, [], destino)
    assert cv2.imread(destino).max() == 0               # no se dibuja nada


def test_sin_modelos_se_avisa_que_la_deteccion_es_provisional(cliente):
    registrar(cliente)
    pagina = cliente.post("/analizar/prueba", follow_redirects=True).get_data(as_text=True)
    assert "Los modelos entrenados no se cargaron" in pagina
    assert "detección provisional" in pagina
    assert "Modelo preliminar" not in pagina


def test_temporizador_de_espera_solo_si_se_activa(app, cliente):
    """Es una ayuda para el desarrollador: por omisión no aparece en el sitio."""
    assert "temporizador-analisis" not in cliente.get("/ia").get_data(as_text=True)
    app.config["MOSTRAR_TEMPORIZADOR"] = True
    assert "temporizador-analisis" in cliente.get("/ia").get_data(as_text=True)


def test_resultados_traen_el_visor_con_zoom_y_la_copia_ampliada(app, cliente):
    registrar(cliente)
    url = cliente.post("/analizar/prueba").headers["Location"]
    pagina = cliente.get(url).get_data(as_text=True)
    assert 'id="visor-zoom"' in pagina and "data-ampliar=" in pagina
    ampliada = re.search(r'data-ampliar="(/resultados/\d+/marcada/[^"]+_ampliada\.jpg)"', pagina).group(1)
    respuesta = cliente.get(ampliada)
    assert respuesta.status_code == 200 and respuesta.mimetype == "image/jpeg"
    # solo se sirven las imágenes del propio análisis
    assert cliente.get(ampliada.replace("_ampliada", "_otra")).status_code == 404


def test_copia_ampliada_es_mas_grande_que_la_de_la_pagina(tmp_path):
    from app.analisis import medicion
    foto = np.zeros((2000, 3000, 3), np.uint8)
    chica, grande = str(tmp_path / "a.jpg"), str(tmp_path / "b.jpg")
    medicion.dibujar_marcas(foto, [], chica, ruta_ampliada=grande)
    assert max(cv2.imread(chica).shape[:2]) == 1400          # la que usan la página y el PDF
    assert max(cv2.imread(grande).shape[:2]) == 2800         # la del zoom


def test_resultados_traen_una_zona_con_el_detalle_de_cada_espermatozoide(cliente):
    registrar(cliente)
    url = cliente.post("/analizar/prueba").headers["Location"]
    pagina = cliente.get(url).get_data(as_text=True)
    zonas = re.findall(r'<polygon class="zona-esperma"[^>]*>', pagina)
    assert len(zonas) == 45                                   # una por cada espermatozoide que sale en la tabla
    primera = zonas[0]
    for atributo in ("data-numero", "data-area-px", "data-largo-px", "data-area-um", "data-largo-um"):
        assert atributo in primera
    assert 'class="capa-esperma"' in pagina and 'viewBox="0 0 ' in pagina
    # el detalle del mouse y el de la tabla dicen lo mismo
    n, area = re.search(r'data-numero="(\d+)" data-area-px="(\d+)"', primera).groups()
    assert f"<tr><td>{n}</td><td>{area}</td>" in pagina


def test_contorno_simple_guarda_puntos_dentro_de_la_foto():
    from app.analisis import medicion
    c = np.array([[[10, 10]], [[60, 10]], [[60, 40]], [[10, 40]]], np.int32)
    puntos = medicion.contorno_simple(c)
    assert puntos == [[10, 10], [60, 10], [60, 40], [10, 40]]


def test_videos_del_curso_en_infografias(cliente):
    html = cliente.get("/infografias").get_data(as_text=True)
    assert html.count('class="video-item"') == 15          # los 15 videos del curso
    assert html.count('role="tab"') == 2                   # dos secciones: red neuronal y sitio web
    assert 'id="video-marco"' in html and "videos.js" in html
    from app import sitio
    assert html.count('data-youtube="') == 15              # todos llevan el atributo, vacío si aún no hay video
    for youtube_id in sitio._YOUTUBE.values():             # los videos activados salen con su id, una vez
        assert html.count('data-youtube="%s"' % youtube_id) == 1
