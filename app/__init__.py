from flask import Flask


def crear_app():
    app = Flask(__name__)

    @app.route("/")
    def inicio():
        return "Hola, Image Bio Pro"

    return app
