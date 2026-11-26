import os
import re
import smtplib
from email.message import EmailMessage
from urllib.parse import quote


def correo_configurado():
    variables = ("SMTP_SERVIDOR", "SMTP_USUARIO", "SMTP_CLAVE")
    return all(os.environ.get(variable) for variable in variables)


def enviar_correo(destinatarios, asunto, mensaje):
    """Envía un correo. Devuelve True si se pudo enviar."""
    destinatarios = [correo for correo in destinatarios if correo]

    if not destinatarios or not correo_configurado():
        print(f"[Aviso sin correo enviado] {asunto}: {mensaje}")
        return False

    correo = EmailMessage()
    correo["Subject"] = asunto
    correo["From"] = os.environ["SMTP_USUARIO"]
    correo["To"] = ", ".join(destinatarios)
    correo.set_content(mensaje)

    try:
        puerto = int(os.environ.get("SMTP_PUERTO", "587"))

        with smtplib.SMTP(os.environ["SMTP_SERVIDOR"], puerto, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(os.environ["SMTP_USUARIO"], os.environ["SMTP_CLAVE"])
            servidor.send_message(correo)

        return True

    except (smtplib.SMTPException, OSError, ValueError) as error:
        # Si falla el correo no queremos que se caiga la aplicación
        print(f"[Error al enviar correo] {error}")
        return False


def correos_encargados(conexion, organizacion_id):
    """Correos de los encargados TI de una organización."""
    filas = conexion.execute(
        """
        SELECT email
        FROM usuarios
        WHERE organizacion_id = ?
        AND rol = 'encargado'
        AND email IS NOT NULL
        """,
        (organizacion_id,)
    ).fetchall()

    return [fila["email"] for fila in filas]


def avisar_encargados(conexion, organizacion_id, asunto, mensaje):
    return enviar_correo(correos_encargados(conexion, organizacion_id), asunto, mensaje)


def enlace_whatsapp(telefono, mensaje):
    """
    Crea un enlace https://wa.me/... que abre WhatsApp con el mensaje
    escrito. No necesita una API: la persona solo presiona "Enviar".
    """
    if not telefono:
        return None

    solo_numeros = re.sub(r"\D", "", telefono)
    return f"https://wa.me/{solo_numeros}?text={quote(mensaje)}"
