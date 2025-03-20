from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.users.schemas import UsuarioUpdatePassword, UsuarioUpdate
from app.security.schemas import UsuarioOut
from app.db.models.models import Usuario
from app.security.hashing import verify_password, hash_password
from app.security.jwt import get_current_verified_user
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users/me", response_model=UsuarioOut)
async def read_users_me(current_user: Usuario = Depends(get_current_verified_user)):
    logger.info(f"Consulta de datos del usuario autenticado: {current_user.email}")
    return current_user


@router.put("/users/me", response_model=UsuarioOut)
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


@router.put("/users/me/password")
async def update_password(
    password_data: UsuarioUpdatePassword,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_verified_user)
):
    logger.info(f"Intento de cambio de contraseña para {current_user.email}")

    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(f"Contraseña incorrecta para {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta"
        )

    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()
    db.refresh(current_user)

    logger.info(f"Contraseña actualizada exitosamente para {current_user.email}")

    return {"message": "Contraseña actualizada exitosamente"}