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


def enviar_email_activacion(email: str, token: str, nombre: str):
    logger.info(f"Preparando correo de activación para {email}")
    
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = SMTP_USER
        mensaje["To"] = email
        mensaje["Subject"] = f"{nombre}, activa tu cuenta en CodePyHub"
        
        cuerpo = f"""
        <h1>¡Bienvenido {nombre}!</h1>
        <p>Haz clic para activar tu cuenta: 
        <a href='http://codepyhub.com/activar?token={token}'>Activar</a></p>
        """
        mensaje.attach(MIMEText(cuerpo, "html"))
        
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            logger.info("Conectando con el servidor SMTP...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            logger.info("Autenticación SMTP exitosa.")
            
            server.sendmail(SMTP_USER, email, mensaje.as_string())
            logger.info(f"Correo de activación enviado a {email}")
    
    except smtplib.SMTPException as e:
        logger.error(f"Error enviando correo a {email}: {e}")
    except Exception as e:
        logger.error(f"Error inesperado enviando correo a {email}: {e}")