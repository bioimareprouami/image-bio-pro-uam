import os
from datetime import datetime

from flask import Flask, request, session

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
        # Solo para desarrollo: muestra un temporizador en la pantalla de espera del análisis.
        # Se activa con la variable de entorno MOSTRAR_TEMPORIZADOR=1; en producción va apagado.
        MOSTRAR_TEMPORIZADOR=os.environ.get("MOSTRAR_TEMPORIZADOR") == "1",
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

    @app.before_request
    def contar_visitante():
        """Suma un visitante la primera vez que una sesión abre una página (sin guardar datos de la persona)."""
        if request.method != "GET" or not request.endpoint or request.endpoint == "static" or session.get("contado"):
            return
        from app.modelos import Contador
        fila = db.session.get(Contador, "visitantes")
        if fila is None:
            fila = Contador(clave="visitantes", valor=0)
            db.session.add(fila)
        fila.valor += 1
        db.session.commit()
        session["contado"] = True

    @app.context_processor
    def datos_globales():
        from app.modelos import Contador
        fila = db.session.get(Contador, "visitantes")
        return {"anio": datetime.now().year, "visitantes": fila.valor if fila else 0}

    with app.app_context():
        db.create_all()

    return app
