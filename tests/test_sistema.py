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
def app(tmp_path):
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
    assert csv.count("\n") == 1 + 2 * 45  # encabezado + 45 cabezas por imagen

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
