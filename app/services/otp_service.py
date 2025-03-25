from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from app.db.models.models import OTP, Usuario
import logging
from dotenv import load_dotenv
import os


load_dotenv()

OTP_EXPIRATION = int(os.getenv("OTP_EXPIRATION", "10"))


logger = logging.getLogger(__name__)


class OTPService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def generate_otp(self, email: str) -> str:
        try:
            logger.debug(f"Iniciando generación de OTP para: {email}")            
            user = self.db_session.query(Usuario).filter(Usuario.email == email).first()
            if not user:
                logger.error(f"Usuario no encontrado: {email}")
                raise ValueError("Usuario no encontrado")            
           
            self.db_session.query(OTP).filter(OTP.user_id == user.id).delete()
            
            otp_code = str(secrets.randbelow(900000) + 100000)
            expiration = datetime.now() + timedelta(minutes=OTP_EXPIRATION)
            
            otp_entry = OTP(
                user_id = user.id,
                code = otp_code,
                expiration = expiration,
                is_used = False
            )
            
            self.db_session.add(otp_entry)
            self.db_session.commit()
            logger.info(f"OTP generado para usuario ID: {user.id}")
            return otp_code
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error en generación de OTP: {str(e)}")
            raise


    def verify_otp(self, email: str, otp_code: str) -> bool:
        try:
            logger.debug(f"Iniciando verificación de OTP para: {email}")
            user = self.db_session.query(Usuario).filter(Usuario.email == email).first()
            if not user:
                logger.warning(f"Intento de verificación con email no registrado: {email}")
                return False

            otp_entry = (
                self.db_session.query(OTP)
                .filter(
                    OTP.user_id == user.id,
                    OTP.code == otp_code
                )
                .first()
            )

            if not otp_entry:
                logger.warning(f"Código OTP no existe para usuario ID: {user.id}")
                return False
                
            
            is_valid = not otp_entry.is_used and otp_entry.expiration > datetime.now()
            
            otp_entry.is_used = True
            self.db_session.delete(otp_entry)
            self.db_session.commit()
            
            if is_valid:
                logger.info(f"OTP válido para usuario ID: {user.id}")
            else:
                logger.warning(f"OTP inválido o expirado para usuario ID: {user.id}")
            
            return is_valid
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Error en verificación de OTP: {str(e)}")
            return False