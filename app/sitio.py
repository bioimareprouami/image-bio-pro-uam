"""Páginas informativas: inicio, nosotros, aliados, infografías y videos, contacto."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensiones import db
from app.modelos import Mensaje

bp = Blueprint("sitio", __name__)

# Contenido de relleno hasta que el grupo pase los textos, fotos e infografías.
LOREM = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
         "incididunt ut labore et dolore magna aliqua.")

# Personas del proyecto, tal como las entregó el grupo.
# scholar: dirección del perfil de Google Scholar de la persona; None = sin enlace.
ALIADOS = [
    {"nombre": "Dra. Sheila Irais Peña Corona", "foto": None, "scholar": None, "lineas": [
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
    {"nombre": "Dra. Edith Arenas Ríos", "foto": None, "scholar": None, "lineas": [
        "Directora de la División de Ciencias Biológicas y de la Salud",
        "Nivel I del SNII"]},
    {"nombre": "Dra. María del Rosario Tarragó Castellanos", "foto": None, "scholar": None, "lineas": [
        "Jefa del Departamento de Biología de la Reproducción",
        "División de Ciencias Biológicas y de la Salud",
        "Nivel I del SNII"]},
    {"nombre": "Dr. Juan Villegas Cortez", "foto": None, "scholar": None, "lineas": [
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
    {"nombre": "Dr. Gerardo Blancas Flores", "foto": None, "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Dr. Juan José Pérez Rivero", "foto": None, "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Dra. Marcela Vergara Onofre", "foto": None, "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Dr. Jesús Eduardo Barrera Morales", "foto": None, "scholar": None, "lineas": ["Colaborador"]},
    {"nombre": "Biól. Isaac Emanuel Mani Arellano", "foto": None, "scholar": None, "lineas": ["Colaborador", "Estudiante"]},
    {"nombre": "Luis", "foto": None, "scholar": None, "lineas": ["Logística y coordinador de actividades de difusión"]},
]

INFOGRAFIAS = [
    {"numero": i, "titulo": f"Título de la infografía {i}", "imagen": None, "texto": LOREM}
    for i in range(1, 9)
]

# id del video de YouTube (lo que va después de "watch?v="); None = marcador de posición
VIDEOS = [{"titulo": f"Título del video {i}", "youtube_id": None} for i in range(1, 5)]


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
    return render_template("sitio/infografias.html", infografias=INFOGRAFIAS, videos=VIDEOS)


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
