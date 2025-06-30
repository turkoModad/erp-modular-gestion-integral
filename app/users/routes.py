from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import EmailStr
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.users.schemas import UsuarioUpdatePassword, UsuarioUpdate
from app.security.schemas import UsuarioOut
from app.db.models.models import Usuario, OTP
from app.security.hashing import verify_password, hash_password
from app.security.jwt import get_current_verified_user
from app.services.otp_service import OTPService
from app.services.schemas import OTPRequest
from app.services.email_otp import enviar_email_otp
from app.security.jwt import create_access_token, verify_access_token
import logging



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users/consulta_datos/", response_model=UsuarioOut)
async def read_users_me(current_user: Usuario = Depends(get_current_verified_user)):
    logger.info(f"Consulta de datos del usuario autenticado: {current_user.email}")
    return current_user


@router.put("/users/actualizar_datos/", response_model=UsuarioOut)
async def update_user_profile(
    user_update: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_verified_user)
):
    update_data = user_update.model_dump(exclude_unset=True)  
    
    if not update_data:
        logger.warning(f"No se enviaron datos para actualizar el perfil de {current_user.email}")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "No se enviaron datos para actualizar el perfil"
        )

    for key, value in update_data.items():
        if hasattr(current_user, key): 
            setattr(current_user, key, value)
        else:
            logger.warning(f"Campo desconocido: {key}")  
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST, 
                detail = f"Campo no válido: {key}"
            )

    db.commit()
    db.refresh(current_user)

    response_data = UsuarioOut.model_validate(current_user)

    logger.info(f"Usuario {current_user.email} actualizó su perfil con los campos: {list(update_data.keys())}")

    return response_data


@router.put("/users/cambio_password/")
async def update_password(
    password_data: UsuarioUpdatePassword,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_verified_user)
):
    logger.info(f"Intento de cambio de contraseña para {current_user.email}")

    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(f"Contraseña incorrecta para {current_user.email}")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )

    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()
    db.refresh(current_user)

    logger.info(f"Contraseña actualizada exitosamente para {current_user.email}")

    return {"message": "Contraseña actualizada exitosamente"}


@router.post("/users/recuperar-acceso/")
async def recuperar_acceso(email: EmailStr, db: Session = Depends(get_db)):
    try:
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND, 
                detail = "Usuario no encontrado"
                )

        otp_service = OTPService(db)
        otp_code, expiration, user_id = otp_service.create_otp_code(email)
        await enviar_email_otp(user.email, otp_code)
        otp_service.save_otp(user_id, otp_code, expiration)
        return {"detail": "Se envió un código OTP al correo"}

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Error durante el proceso de recuperación: {str(e)}")
        raise HTTPException(
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo completar el proceso. Intente nuevamente."
        )
    

@router.post("/users/recuperar_con_OTP/")
async def recuperar_con_OTP(data: OTPRequest, db: Session = Depends(get_db)):
    
    user = db.query(Usuario).filter(Usuario.email == data.email).first()
    if not user:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
            )
    
    otp_service = OTPService(db)
    if not otp_service.verify_otp(data.email, data.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código OTP inválido, expirado o ya utilizado"
        )
    
    reset_token = create_access_token(
    email=user.email,
    role=user.role,
    expires_delta = timedelta(minutes=10),
    extra_data={"token_type": "password_reset"}
    )
    
    return {"detail": "Código OTP verificado correctamente"}


@router.get("/users/cambiar_contraseña/")
def mostrar_formulario_cambio(token: str):
    try:
        payload = verify_access_token(token)
        if payload.get("token_type") != "password_reset":
            raise HTTPException(status_code=403, detail="Token inválido")
        return {"detail": "Token válido. Ya podés enviar la nueva contraseña.", "email": payload["email"]}
    except Exception:
        raise HTTPException(status_code=403, detail="Token inválido o expirado")
