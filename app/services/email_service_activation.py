from dotenv import load_dotenv
import logging
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import re

# Importaciones para envio de SMTP o SMTP_SSL
# import smtplib
# from email.mime.multipart import MIMEMultipart  
# from email.mime.text import MIMEText

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Envio con Api_key
# Para evitar el bloqueo de puertos en el servidor


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME")
FRONTEND_URL = os.getenv("FRONTEND_URL")



def enviar_email_activacion(email: str, asunto: str, cuerpo: str):
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
    
    email_obj = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": email}],
        sender = {"email": EMAIL_SENDER, "name": EMAIL_SENDER_NAME},
        subject = asunto,
        html_content = cuerpo
    )

    try:
        enlaces = re.findall(r'href="([^"]+)"', cuerpo)
        if enlaces:
            logger.info(f"Enlace de activación: {enlaces[0]}")
        else:
            logger.warning("No se encontró enlace de activación en el cuerpo del email.")

        api_instance.send_transac_email(email_obj)
        logger.info("Correo enviado correctamente.")
    except ApiException as e:
        logger.error(f"Error al enviar correo: {e}")
        raise RuntimeError("No se pudo enviar el correo con Brevo.")

# Envio con SMTP O SMTP_SSL

# SMTP_SERVER = os.getenv("SMTP_SERVER")
# SMTP_PORT = os.getenv("SMTP_PORT")
# SMTP_USER = os.getenv("SMTP_USER")
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


# def enviar_email_activacion(email: str, asunto: str, cuerpo: str):
#     logger.info(f"Preparando correo de activación para {email}")
    
#     try:
#         mensaje = MIMEMultipart()
#         mensaje["From"] = SMTP_USER
#         mensaje["To"] = email
#         mensaje["Subject"] = asunto

#         logger.info(f"Mensaje de activacion: {cuerpo}") 

#         mensaje.attach(MIMEText(cuerpo, "html"))
#         logger.info("Conectando con el servidor SMTP...")

        # Envio con SMTP_SSL

        # with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        #     server.login(SMTP_USER, SMTP_PASSWORD)
        #     logger.info("Autenticación SMTP exitosa.") 
            
        #     server.sendmail(SMTP_USER, email, mensaje.as_string())
        #     logger.info(f"Correo enviado a {email}")
      
    # Envio con SMTP

    #     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
    #         server.ehlo()  # Identifica el cliente al servidor
    #         server.starttls()  # Inicia la capa TLS
    #         server.ehlo()  # Vuelve a identificarse tras activar TLS
    #         server.login(SMTP_USER, SMTP_PASSWORD)
    #         logger.info("Autenticación SMTP exitosa.")
            
    #         server.sendmail(SMTP_USER, email, mensaje.as_string())
    #         logger.info(f"Correo enviado a {email}")

    
    # except smtplib.SMTPException as e:
    #     logger.error(f"Error enviando correo a {email}: {e}")
    #     raise RuntimeError(f"Fallo SMTP al enviar el email a {email}") from e
    # except Exception as e:
    #     logger.error(f"Error inesperado enviando correo a {email}: {e}")
    #     raise RuntimeError(f"Fallo inesperado al enviar el email a {email}") from e