from dotenv import load_dotenv
import logging
import os
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
import re


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_SENDER_NAME = os.getenv("EMAIL_SENDER_NAME")



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