from fastapi import APIRouter, HTTPException, Depends, status, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from datetime import timedelta
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.users.schemas import UsuarioUpdate
from app.security.schemas import UsuarioOut
from app.db.models.models import Usuario
from app.security.hashing import verify_password, hash_password
from app.security.jwt import get_current_verified_user
from app.security.jwt import create_access_token, verify_access_token
from app.services.email_service_activation import enviar_email_activacion
import logging
from dotenv import load_dotenv
import os



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")


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


@router.post("/users/recuperar_acceso/")
async def recuperar_acceso(email: EmailStr, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    reset_token = create_access_token(
        email=user.email,
        role=user.role,
        expires_delta=timedelta(minutes=10),
        extra_data={"token_type": "password_reset"}
    )

    asunto = f"{user.first_name}, Cambia tu contraseña"
    cuerpo = f"""
    <h2>Solicitud de restablecimiento de contraseña</h2>
    <p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>
    <a href="http://localhost:{PORT}/users/reset-password-form?token={reset_token}">
        Restablecer contraseña
    </a>
    """

    try:
        enviar_email_activacion(user.email, asunto, cuerpo)
        return {"detail": "Se ha enviado un enlace para restablecer tu contraseña"}
    except Exception as e:
        logger.error(f"No se pudo enviar el email a {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el correo. Intenta más tarde."
        )



@router.get("/users/reset-password-form", response_class=HTMLResponse)
def mostrar_formulario_cambio(token: str, request: Request):
    try:
        payload = verify_access_token(token)
        if payload.get("token_type") != "password_reset":
            raise HTTPException(status_code=403, detail="Token inválido")
        return templates.TemplateResponse("reset_password_form.html", {
            "request": request,
            "token": token
        })
    except Exception:
        raise HTTPException(status_code=403, detail="Token inválido o expirado")



@router.post("/users/reset-password/")
def cambiar_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if new_password != confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden"
        )

    try:
        payload = verify_access_token(token)
        if payload.get("token_type") != "password_reset":
            raise HTTPException(status_code=403, detail="Token inválido")

        email = payload.get("sub")
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        user.password_hash = hash_password(new_password)
        db.commit()

        return {"detail": "Contraseña actualizada correctamente"}
    except Exception:
        raise HTTPException(status_code=403, detail="Token inválido o expirado")