"""Registro, inicio y cierre de sesión, y perfil con "mis análisis"."""
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensiones import db
from app.modelos import Usuario

bp = Blueprint("cuentas", __name__)

LARGO_MINIMO_CLAVE = 8


def destino_seguro(siguiente):
    """Solo permite redirigir a direcciones del mismo sitio."""
    if siguiente and not urlsplit(siguiente).netloc and siguiente.startswith("/"):
        return siguiente
    return url_for("analisis.ia")


@bp.route("/entrar", methods=["GET", "POST"])
def entrar():
    if current_user.is_authenticated:
        return redirect(url_for("analisis.ia"))

    if request.method == "POST":
        accion = request.form.get("accion")
        correo = request.form.get("correo", "").strip().lower()
        clave = request.form.get("clave", "")

        if accion == "registrar":
            nombre = request.form.get("nombre", "").strip()
            if not (nombre and correo and clave):
                flash("Llena nombre, correo y contraseña para crear tu cuenta.", "warning")
            elif "@" not in correo:
                flash("Escribe un correo electrónico válido.", "warning")
            elif len(clave) < LARGO_MINIMO_CLAVE:
                flash(f"La contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres.", "warning")
            elif Usuario.query.filter_by(correo=correo).first():
                flash("Ya existe una cuenta con ese correo. Inicia sesión.", "warning")
            else:
                usuario = Usuario(nombre=nombre[:120], correo=correo[:254])
                usuario.poner_clave(clave)
                db.session.add(usuario)
                db.session.commit()
                login_user(usuario)
                flash(f"Bienvenido, {usuario.nombre}. Tu cuenta quedó creada.", "success")
                return redirect(destino_seguro(request.args.get("next")))
        else:
            usuario = Usuario.query.filter_by(correo=correo).first()
            if usuario and usuario.revisar_clave(clave):
                login_user(usuario, remember=bool(request.form.get("recordar")))
                return redirect(destino_seguro(request.args.get("next")))
            flash("Correo o contraseña incorrectos.", "danger")

    return render_template("cuentas/entrar.html", form=request.form)


@bp.route("/salir", methods=["POST"])
@login_required
def salir():
    logout_user()
    flash("Cerraste sesión.", "info")
    return redirect(url_for("sitio.inicio"))


@bp.route("/perfil")
@login_required
def perfil():
    return render_template("cuentas/perfil.html", analisis=current_user.analisis.all())
