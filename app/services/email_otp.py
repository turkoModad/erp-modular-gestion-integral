import smtplib
from dotenv import load_dotenv
import os
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
import logging


load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
PORT = os.getenv("PORT")


async def enviar_email_otp(email: str, otp_code: str):
    logger.info(f"Preparando correo con OTP para {email}")

    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = SMTP_USER
        mensaje["To"] = email
        mensaje["Subject"] = "Tu código de verificación"
        
        cuerpo = f"""
        <h1>¡Tu código de verificación OTP!</h1>
        <p>Tu código OTP es: <strong>{otp_code}</strong></p>
        <p>Este código es válido por 10 minutos.</p>
        """

        mensaje.attach(MIMEText(cuerpo, "html"))

        logger.info("Conectando con el servidor SMTP...")
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            logger.info("Conectando con el servidor SMTP...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            logger.info("Autenticación SMTP exitosa.")

            server.sendmail(SMTP_USER, email, mensaje.as_string())
            logger.info(f"Correo de OTP enviado a {email}")

    except smtplib.SMTPException as e:
        logger.error(f"Error enviando correo a {email}: {e}")
        raise RuntimeError(f"No se pudo enviar el email OTP a {email}") from e
    except Exception as e:
        logger.error(f"Error inesperado enviando correo a {email}: {e}")
        raise RuntimeError(f"Fallo inesperado al enviar el email OTP a {email}") from e