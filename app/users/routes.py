from fastapi import APIRouter, HTTPException, Depends, status, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.models import Usuario
from app.users.schemas import UsuarioUpdate
from app.security.schemas import UsuarioOut
from app.security.jwt import get_current_verified_user
import logging
from dotenv import load_dotenv
import os



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates/users")


load_dotenv()

PORT = os.getenv("PORT")


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