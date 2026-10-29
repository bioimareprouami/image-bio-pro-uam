"""Páginas informativas: inicio, nosotros, aliados, infografías, videos, contacto."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensiones import db
from app.modelos import Mensaje

bp = Blueprint("sitio", __name__)

# Contenido de relleno hasta que el grupo pase los textos, fotos e infografías.
LOREM = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
         "incididunt ut labore et dolore magna aliqua.")

# Personas del proyecto, tal como las entregó el grupo.
# foto: ruta dentro de app/static (fotos cuadradas en app/static/aliados); None = marcador de posición.
# scholar: dirección del perfil de Google Scholar de la persona; None = sin enlace.
ALIADOS = [
    {"nombre": "Dra. Sheila Irais Peña Corona", "foto": "aliados/sheila-irais-pena-corona.jpg", "scholar": None, "lineas": [
        "Responsable y líder del proyecto BioImage-Repro UAM",
        "Profesora Asociada de Carrera Nivel D de Tiempo Completo",
        "Departamento de Biología de la Reproducción",
        "División de Ciencias Biológicas y de la Salud",
        "Nivel I del SNII"]},
    {"nombre": "Dr. Saúl Jiménez Jiménez", "foto": None, "scholar": None, "lineas": [
        "Responsable del sitio web y del modelo de IA alojados en BioImage-Repro UAM",
        "PostDoc SECIHTI en la UAM-Iztapalapa",
        "Departamento de Química",
        "Departamento de Fisicoquímica de superficies",
        "División de Ciencias Básicas e Ingeniería",
        "Candidato SNII"]},
    {"nombre": "Dra. Edith Arenas Ríos", "foto": "aliados/edith-arenas-rios.jpg", "scholar": None, "lineas": [
        "Directora de la División de Ciencias Biológicas y de la Salud",
        "Nivel I del SNII"]},
    {"nombre": "Dra. María del Rosario Tarragó Castellanos", "foto": "aliados/rosario-tarrago-castellanos.jpg", "scholar": None, "lineas": [
        "Jefa del Departamento de Biología de la Reproducción",
        "División de Ciencias Biológicas y de la Salud",
        "Nivel I del SNII"]},
    {"nombre": "Dr. Juan Villegas Cortez", "foto": "aliados/juan-villegas-cortez.jpg", "scholar": None, "lineas": [
        "Colaborador",
        "Profesor Titular de Carrera Nivel C de Tiempo Completo",
        "Departamento de Sistemas",
        "División de Ciencias Básicas e Ingeniería",
        "Nivel I del SNII"]},
    {"nombre": "Dr. Juan Isaac Chavez Corona", "foto": None, "scholar": None, "lineas": [
        "Colaborador",
        "Estudiante de doctorado en ciencias Químicas en la UNAM",
        "Departamento de Farmacia"]},
    {"nombre": "Dr. Roberto Carlos Lazzarini Lechuga", "foto": None, "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Dr. Jorge Eduardo Vieyra Durán", "foto": None, "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Gerardo Mejia Hernandez", "foto": "aliados/gerardo-mejia-hernandez.jpeg", "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Biól. Isaac Emanuel Mani Arellano", "foto": "aliados/isaac-emanuel-mani-arellano.jpeg", "scholar": None, "lineas": ["Colaborador", "Estudiante"]},
    {"nombre": "Luis Enrique Perez Caltzontzin", "foto": "aliados/luis-enrique-perez-caltzontzin.jpg", "scholar": None, "lineas": ["Logística y coordinador de actividades de difusión"]},
]

# Los colaboradores van al final; el orden dentro de cada grupo es el de la lista.
ALIADOS.sort(key=lambda a: a["lineas"][0] == "Colaborador")

INFOGRAFIAS = [
    {"numero": i, "titulo": f"Título de la infografía {i}", "imagen": None, "texto": LOREM}
    for i in range(1, 9)
]

# Videos del curso en dos secciones. Cada video lleva su número en el curso (1 a 15) y el módulo al que
# pertenece. youtube_id es lo que va después de "watch?v="; None = marcador de posición hasta subir el video
# (los ids están en _YOUTUBE).
_VIDEOS = {
    1: ("El problema y la imagen digital", "Contar y medir espermatozoides a mano, y qué es una imagen para una computadora."),
    2: ("Inteligencia artificial, entrenamiento y la neurona", "Definiciones, entrenamiento contra inferencia y la neurona artificial."),
    3: ("Capas, cómo aprende una red y cierre", "De la neurona a la red, y cómo una red aprende de ejemplos."),
    4: ("Cómo ve una imagen una red convolucional", "El filtro que recorre la imagen, con un ejemplo numérico de 3 por 3."),
    5: ("Mask R-CNN", "La red que usa el sistema, explicada en lenguaje sencillo."),
    6: ("Aprendizaje por transferencia", "Cómo aprovechar una red entrenada para otra cosa."),
    7: ("Datos y entrenamiento", "Anotación, entrenamiento y validación, sobreajuste y curvas."),
    8: ("Frontend: el sitio funcionando", "Cómo se ve y cómo está hecho el sitio: plantillas, Bootstrap y la pantalla de resultados."),
    9: ("Backend", "Flask, las rutas y qué pasa cuando se sube una imagen."),
    10: ("Inferencia con recortes", "Cómo se usa el modelo: recortes, juntar resultados y quitar repetidos."),
    11: ("Medición, escala y retos", "Contorno, área, largo y escala, y cómo se resolvieron los retos."),
    12: ("Cuaderno de Colab, primera parte", "Del entorno a la preparación de las imágenes y los recortes."),
    13: ("Cuaderno de Colab, segunda parte", "Construir la red, entrenar, ver los resultados y exportar el modelo."),
    14: ("Despliegue en la nube", "El servidor, la clave SSH, Docker y Docker Compose."),
    15: ("Nginx, dominio y HTTPS", "Cómo recibe visitas el sitio, el dominio, el certificado y el cierre."),
}
# Videos ya subidos a YouTube: número del curso -> id. Los que no están salen como marcador de posición.
_YOUTUBE = {
    # 1: "ucNXMX2AXAg",
    # 2: "5LMw9Kyl1j4",
    # 3: "pqSKnbEho38",
}
# (nombre de la sección, nombre corto para la pestaña, [(número, módulo del curso), ...])
_SECCIONES = [
    ("Desarrollo de la red neuronal convolucional", "Red neuronal",
     [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (6, 2), (7, 2), (12, 4), (13, 4)]),
    ("Desarrollo del sitio web", "Sitio web",
     [(8, 3), (9, 3), (10, 3), (11, 3), (14, 4), (15, 4)]),
]
VIDEOS = [
    {"nombre": nombre, "corto": corto,
     "videos": [{"numero": n, "modulo": m, "titulo": _VIDEOS[n][0], "texto": _VIDEOS[n][1], "youtube_id": _YOUTUBE.get(n)}
                for n, m in lista]}
    for nombre, corto, lista in _SECCIONES
]


@bp.route("/")
def inicio():
    return render_template("sitio/inicio.html")


@bp.route("/nosotros")
def nosotros():
    return render_template("sitio/nosotros.html")


@bp.route("/aliados")
def aliados():
    return render_template("sitio/aliados.html", aliados=ALIADOS)


@bp.route("/infografias")
def infografias():
    return render_template("sitio/infografias.html", infografias=INFOGRAFIAS)


@bp.route("/videos")
def videos():
    total_videos = sum(len(g["videos"]) for g in VIDEOS)
    return render_template("sitio/videos.html", videos=VIDEOS, total_videos=total_videos)


@bp.route("/contacto", methods=["GET", "POST"])
def contacto():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        correo = request.form.get("correo", "").strip()
        texto = request.form.get("mensaje", "").strip()
        if not (nombre and correo and texto):
            flash("Llena tu nombre, tu correo y el mensaje.", "warning")
            return render_template("sitio/contacto.html", form=request.form)
        db.session.add(Mensaje(nombre=nombre[:120], correo=correo[:254], texto=texto))
        db.session.commit()
        flash("Gracias, recibimos tu mensaje.", "success")
        return redirect(url_for("sitio.contacto"))
    return render_template("sitio/contacto.html", form={})


@bp.route("/aviso-de-privacidad")
def privacidad():
    return render_template("sitio/privacidad.html")
