from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.services.email_otp import enviar_email_otp
from app.services.otp_service import OTPService
from app.db.database import get_db
from app.db.models.models import Usuario
from app.security.jwt import create_access_token
from sqlalchemy.orm import Session
import logging


logger = logging.getLogger(__name__)


class OTPRequest(BaseModel):
    email: str
    otp_code: str


router = APIRouter()


def get_otp_service(db: Session = Depends(get_db)) -> OTPService:
    return OTPService(db)


@router.post("/request_otp/")
async def request_otp(email: str, otp_service: OTPService = Depends(get_otp_service)):
    try:
        logger.info(f"Solicitando OTP para email: {email}")
        otp_code = otp_service.generate_otp(email)
        await enviar_email_otp(email, otp_code)
        logger.info(f"OTP enviado a {email}")
        return {"message": "Código OTP enviado"}
    except ValueError as e:
        logger.error(f"Error al generar OTP: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    


@router.post("/verify-otp")
async def verify_otp(
    otp_data: OTPRequest, 
    db: Session = Depends(get_db)
):
    logger.info(f"Verificando OTP para el usuario: {otp_data.email}")
    otp_service = OTPService(db)
    is_valid = otp_service.verify_otp(otp_data.email, otp_data.otp_code)
    
    if not is_valid:
        logger.warning(f"OTP incorrecto o expirado para el usuario {otp_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP incorrecto o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(Usuario).filter(Usuario.email == otp_data.email).first()
    access_token = create_access_token(
        data={"sub": user.email, "otp_verified": True} 
    )
    
    logger.info(f"Login exitoso para el usuario {otp_data.email}.")
    return {"access_token": access_token, "token_type": "bearer"}