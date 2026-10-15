import json
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensiones import db, login_manager


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(254), unique=True, nullable=False, index=True)
    clave_cifrada = db.Column(db.String(256), nullable=False)
    creado = db.Column(db.DateTime, default=datetime.now, nullable=False)

    analisis = db.relationship("Analisis", backref="usuario", lazy="dynamic",
                               order_by="Analisis.fecha.desc()")

    def poner_clave(self, clave):
        self.clave_cifrada = generate_password_hash(clave)

    def revisar_clave(self, clave):
        return check_password_hash(self.clave_cifrada, clave)


class Analisis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False, index=True)
    fecha = db.Column(db.DateTime, default=datetime.now, nullable=False)
    # Resultados completos en JSON, para volver a mostrarlos igual que al hacerlos (RF-48)
    resultados_json = db.Column(db.Text, nullable=False)
    # Nombre del PDF guardado en instance/pdfs (RF-46)
    pdf = db.Column(db.String(255))

    @property
    def resultados(self):
        return json.loads(self.resultados_json)

    @property
    def nombres_imagenes(self):
        return [img["nombre"] for img in self.resultados["imagenes"]]


class Mensaje(db.Model):
    """Mensajes del formulario de contacto. Se guardan mientras no haya correo definido."""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(254), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.now, nullable=False)


@login_manager.user_loader
def cargar_usuario(usuario_id):
    return db.session.get(Usuario, int(usuario_id))
