"""Página de inteligencia artificial, análisis, resultados y descargas."""
import json
import os
import uuid

from flask import (Blueprint, Response, abort, current_app, flash, redirect, render_template,
                   request, send_from_directory, url_for)
from flask_login import current_user, login_required

from app.analisis import medicion, reportes
from app.extensiones import db
from app.modelos import Analisis
from app.sitio import INFOGRAFIAS

bp = Blueprint("analisis", __name__)

EXTENSIONES = {"bmp", "png", "tif", "tiff", "jpg", "jpeg"}
IMAGEN_PRUEBA = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "static", "muestras", "prueba.png")


def extension(nombre):
    return nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""


@bp.route("/ia")
def ia():
    return render_template("analisis/ia.html", infografias=INFOGRAFIAS[:4],
                           extensiones=sorted(EXTENSIONES),
                           max_imagenes=current_app.config["MAX_IMAGENES"])


@bp.route("/analizar", methods=["POST"])
@login_required
def analizar():
    archivos = [a for a in request.files.getlist("imagenes") if a and a.filename]
    maximo = current_app.config["MAX_IMAGENES"]

    if not archivos:
        flash("Elige al menos una imagen.", "warning")
        return redirect(url_for("analisis.ia"))
    if len(archivos) > maximo:
        flash(f"Puedes subir como máximo {maximo} imágenes a la vez.", "warning")
        return redirect(url_for("analisis.ia"))
    no_validos = [a.filename for a in archivos if extension(a.filename) not in EXTENSIONES]
    if no_validos:
        flash("Formato no permitido: " + ", ".join(no_validos)
              + ". Usa BMP, PNG o TIFF (JPG se acepta con aviso).", "warning")
        return redirect(url_for("analisis.ia"))

    clave = uuid.uuid4().hex
    imagenes = []
    for i, archivo in enumerate(archivos, start=1):
        # En disco se guarda con un nombre generado; el original solo se usa para mostrarlo
        ruta = os.path.join(current_app.config["CARPETA_SUBIDAS"],
                            f"{clave}_{i}.{extension(archivo.filename)}")
        archivo.save(ruta)
        try:
            imagenes.append(_analizar_una(ruta, os.path.basename(archivo.filename), clave, i))
        finally:
            os.remove(ruta)  # RF-47: las imágenes se borran al terminar el análisis

    return _guardar_y_mostrar(imagenes)


@bp.route("/analizar/prueba", methods=["POST"])
@login_required
def analizar_prueba():
    """RF-52: analizar la imagen de prueba sin subir una propia."""
    if not os.path.exists(IMAGEN_PRUEBA):
        abort(404)
    clave = uuid.uuid4().hex
    return _guardar_y_mostrar([_analizar_una(IMAGEN_PRUEBA, "prueba.png", clave, 1)])


def _analizar_una(ruta, nombre_original, clave, numero):
    ruta_marcada = os.path.join(current_app.config["CARPETA_MARCADAS"], f"{clave}_{numero}.jpg")
    return medicion.analizar_imagen(ruta, nombre_original, ruta_marcada)


def _guardar_y_mostrar(imagenes):
    detectores = {img.get("detector") for img in imagenes if img.get("detector")}
    resultados = {
        # Provisional si alguna imagen se analizó con la detección por umbral de color; si no, con los modelos
        "provisional": "provisional" in detectores,
        "motivo_provisional": next((img["motivo_provisional"] for img in imagenes if img.get("motivo_provisional")), None),
        "modelo_preliminar": bool(detectores - {"provisional"}),
        "imagenes": imagenes,
        "promedios": medicion.promedios_entre_imagenes(imagenes),
    }
    analisis = Analisis(usuario_id=current_user.id, resultados_json=json.dumps(resultados))
    db.session.add(analisis)
    db.session.commit()

    # RF-46: el PDF se guarda en el servidor
    nombre_pdf = f"analisis_{analisis.id}.pdf"
    reportes.generar_pdf(resultados, current_user.nombre, analisis.fecha,
                         current_app.config["CARPETA_MARCADAS"],
                         os.path.join(current_app.config["CARPETA_PDF"], nombre_pdf))
    analisis.pdf = nombre_pdf
    db.session.commit()

    return redirect(url_for("analisis.resultados", analisis_id=analisis.id))


def _analisis_propio(analisis_id):
    """Cada usuario solo ve sus propios análisis."""
    analisis = db.session.get(Analisis, analisis_id)
    if analisis is None or analisis.usuario_id != current_user.id:
        abort(404)
    return analisis


@bp.route("/resultados/<int:analisis_id>")
@login_required
def resultados(analisis_id):
    analisis = _analisis_propio(analisis_id)
    return render_template("analisis/resultados.html", analisis=analisis,
                           resultados=analisis.resultados)


@bp.route("/resultados/<int:analisis_id>/marcada/<nombre>")
@login_required
def imagen_marcada(analisis_id, nombre):
    analisis = _analisis_propio(analisis_id)
    permitidos = {img.get(clave) for img in analisis.resultados["imagenes"] for clave in ("marcada", "marcada_ampliada")}
    if nombre not in permitidos:
        abort(404)
    return send_from_directory(current_app.config["CARPETA_MARCADAS"], nombre)


@bp.route("/resultados/<int:analisis_id>/csv")
@login_required
def descargar_csv(analisis_id):
    analisis = _analisis_propio(analisis_id)
    return Response(
        reportes.generar_csv(analisis.resultados),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analisis_{analisis.id}.csv"},
    )


@bp.route("/resultados/<int:analisis_id>/pdf")
@login_required
def descargar_pdf(analisis_id):
    analisis = _analisis_propio(analisis_id)
    if not analisis.pdf:
        abort(404)
    return send_from_directory(current_app.config["CARPETA_PDF"], analisis.pdf,
                               as_attachment=True)
