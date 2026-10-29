"""Envío de correo por SMTP. Los datos salen de variables de entorno (archivo .env del servidor)."""
import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger(__name__)


def configurado():
    """True si están definidos el servidor, el usuario y la contraseña de aplicación."""
    return all(os.environ.get(v) for v in ("MAIL_SERVIDOR", "MAIL_USUARIO", "MAIL_CLAVE"))


def enviar(destino, asunto, texto):
    """Manda un correo de texto. Devuelve True si salió y False si falta configuración o falla el envío."""
    if not configurado():
        log.warning("Correo sin configurar: no se envió el mensaje a %s", destino)
        return False
    usuario = os.environ["MAIL_USUARIO"]
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto
    mensaje["From"] = os.environ.get("MAIL_REMITENTE") or usuario
    mensaje["To"] = destino
    mensaje.set_content(texto)
    try:
        with smtplib.SMTP(os.environ["MAIL_SERVIDOR"], int(os.environ.get("MAIL_PUERTO") or 587), timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            # Google muestra la contraseña de aplicación en grupos de cuatro letras; los espacios no cuentan
            smtp.login(usuario, os.environ["MAIL_CLAVE"].replace(" ", ""))
            smtp.send_message(mensaje)
    except (smtplib.SMTPException, OSError):
        log.exception("No se pudo enviar el correo a %s", destino)
        return False
    return True
