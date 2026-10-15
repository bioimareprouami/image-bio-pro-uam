"""Páginas informativas: inicio, nosotros, aliados, infografías y videos, contacto."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensiones import db
from app.modelos import Mensaje

bp = Blueprint("sitio", __name__)

# Contenido de relleno hasta que el grupo pase los textos, fotos e infografías.
LOREM = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
         "incididunt ut labore et dolore magna aliqua.")

ALIADOS = [
    {"nombre": nombre, "foto": None, "resena": LOREM}
    for nombre in ["Dr. Nombre Apellido", "Dra. Nombre Apellido", "Dr. Nombre Apellido",
                   "Dra. Nombre Apellido", "Mtra. Nombre Apellido", "Ing. Nombre Apellido",
                   "Biól. Nombre Apellido", "Lic. Nombre Apellido"]
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
