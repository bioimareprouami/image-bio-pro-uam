import os
from datetime import datetime

from flask import Flask

from app.extensiones import csrf, db, login_manager


def crear_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.update(
        # En el servidor, SECRET_KEY debe venir de una variable de entorno
        SECRET_KEY=os.environ.get("SECRET_KEY", "solo-para-desarrollo"),
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "imagebio.db"),
        # Hasta 10 imágenes BMP sin compresión (RF-35)
        MAX_CONTENT_LENGTH=300 * 1024 * 1024,
        MAX_IMAGENES=10,
        CARPETA_PDF=os.path.join(app.instance_path, "pdfs"),
        CARPETA_SUBIDAS=os.path.join(app.instance_path, "subidas"),
        # Copias reducidas con las cabezas marcadas, para volver a ver un análisis (RF-48)
        CARPETA_MARCADAS=os.path.join(app.instance_path, "marcadas"),
    )
    if config:
        app.config.update(config)

    for carpeta in (app.instance_path, app.config["CARPETA_PDF"],
                    app.config["CARPETA_SUBIDAS"], app.config["CARPETA_MARCADAS"]):
        os.makedirs(carpeta, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "cuentas.entrar"
    login_manager.login_message = "Inicia sesión para analizar imágenes."
    login_manager.login_message_category = "info"

    from app import modelos  # noqa: F401  (registra las tablas)
    from app.analisis.rutas import bp as bp_analisis
    from app.cuentas import bp as bp_cuentas
    from app.sitio import bp as bp_sitio

    app.register_blueprint(bp_sitio)
    app.register_blueprint(bp_cuentas)
    app.register_blueprint(bp_analisis)

    @app.context_processor
    def datos_globales():
        return {"anio": datetime.now().year}

    with app.app_context():
        db.create_all()

    return app
