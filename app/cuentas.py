"""Registro, inicio y cierre de sesión, y perfil con "mis análisis"."""
from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from itsdangerous import BadData, URLSafeTimedSerializer

from app import correo
from app.extensiones import db
from app.modelos import Usuario

bp = Blueprint("cuentas", __name__)

LARGO_MINIMO_CLAVE = 8
VIGENCIA_ENLACE = 3600   # segundos que dura el enlace para cambiar la contraseña


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


def _serializador():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="restablecer-clave")


def _token(usuario):
    # Lleva un pedazo de la contraseña actual: al cambiarla, el enlace deja de servir
    return _serializador().dumps({"id": usuario.id, "c": usuario.clave_cifrada[-10:]})


def _usuario_del_token(token):
    try:
        datos = _serializador().loads(token, max_age=VIGENCIA_ENLACE)
    except BadData:
        return None
    usuario = db.session.get(Usuario, datos.get("id"))
    if usuario is None or usuario.clave_cifrada[-10:] != datos.get("c"):
        return None
    return usuario


@bp.route("/olvide", methods=["GET", "POST"])
def olvide():
    if request.method == "POST":
        direccion = request.form.get("correo", "").strip().lower()
        usuario = Usuario.query.filter_by(correo=direccion).first() if direccion else None
        enviado = True
        if usuario:
            enlace = url_for("cuentas.restablecer", token=_token(usuario), _external=True)
            enviado = correo.enviar(
                usuario.correo, "Recupera tu contraseña de BioImage-Repro UAM",
                f"Hola, {usuario.nombre}.\n\nPara elegir una contraseña nueva abre este enlace. "
                f"Dura una hora y solo sirve una vez:\n\n{enlace}\n\n"
                "Si no lo pediste tú, ignora este mensaje: tu contraseña sigue igual.\n")
        if enviado:
            # La respuesta es la misma exista o no la cuenta, para no revelar quién está registrado
            flash("Si el correo está registrado, te mandamos un enlace para elegir una contraseña nueva. "
                  "Revisa también la carpeta de spam.", "info")
            return redirect(url_for("cuentas.entrar"))
        flash("No pudimos enviar el correo en este momento. Escríbenos a uamiztapalapa62@gmail.com.", "danger")
    return render_template("cuentas/olvide.html", form=request.form)


@bp.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer(token):
    usuario = _usuario_del_token(token)
    if usuario is None:
        flash("El enlace no es válido o ya venció. Pide uno nuevo.", "warning")
        return redirect(url_for("cuentas.olvide"))
    if request.method == "POST":
        clave = request.form.get("clave", "")
        if len(clave) < LARGO_MINIMO_CLAVE:
            flash(f"La contraseña debe tener al menos {LARGO_MINIMO_CLAVE} caracteres.", "warning")
        elif clave != request.form.get("clave2", ""):
            flash("Las dos contraseñas no coinciden.", "warning")
        else:
            usuario.poner_clave(clave)
            db.session.commit()
            flash("Tu contraseña quedó cambiada. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("cuentas.entrar"))
    return render_template("cuentas/restablecer.html")
