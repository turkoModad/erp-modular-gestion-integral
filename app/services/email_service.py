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
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
PORT = os.getenv("PORT")


def enviar_email_activacion(email: str, token: str, nombre: str):
    logger.info(f"Preparando correo de activación para {email}")
    
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = SMTP_USER
        mensaje["To"] = email
        mensaje["Subject"] = f"{nombre}, activa tu cuenta en CodePyHub" 

        cuerpo = f"""
        <h1>¡Bienvenido {nombre}!</h1>
        <p>Haz clic en el siguiente enlace para activar tu cuenta:</p>
        <a href="http://localhost:{PORT}/activar/?email={email}&token={token}">Activar en Local</a>
        """
        logger.info(f"Mensaje de activacion: {cuerpo}")        
        mensaje.attach(MIMEText(cuerpo, "html"))
        logger.info("Conectando con el servidor SMTP...")
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            logger.info("Autenticación SMTP exitosa.") 
            
            server.sendmail(SMTP_USER, email, mensaje.as_string())
            logger.info(f"Correo de activación enviado a {email}")
    
    except smtplib.SMTPException as e:
        logger.error(f"Error enviando correo a {email}: {e}")
        raise RuntimeError(f"Fallo SMTP al enviar el email a {email}") from e
    except Exception as e:
        logger.error(f"Error inesperado enviando correo a {email}: {e}")
        raise RuntimeError(f"Fallo inesperado al enviar el email a {email}") from e