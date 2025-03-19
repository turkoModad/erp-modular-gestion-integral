from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.security.schemas import UsuarioCreate, UsuarioOut
from app.db.models import Usuario
from app.security.hashing import verify_password, hash_password
from app.security.jwt import create_access_token
from app.services.email_service import enviar_email_activacion
from app.services.hash_activacion_email import crear_token
import bcrypt
import datetime
import logging
from app.enums import AccountStatus
from app.security.dependencies import OAuth2EmailRequestForm


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()


@router.post("/registro/", response_model=UsuarioOut)
def register(user: UsuarioCreate, db: Session = Depends(get_db)):
    logger.info(f"Intento de registro para el usuario: {user.email}")
    db_user = db.query(Usuario).filter(Usuario.email == user.email).first()
    if db_user:
        logger.warning(f"Registro fallido: el usuario {user.email} ya existe")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "El usuario ya existe"
        )
    
    hashed_password = hash_password(user.password)
    token, hash_token, expiracion = crear_token(user.email)

    new_user = Usuario( 
        email = user.email, 
        password_hash = hashed_password,
        first_name = user.first_name,
        last_name = user.last_name,
        date_of_birth = user.date_of_birth,
        phone_number = user.phone_number,
        shipping_address = user.shipping_address,
        shipping_city = user.shipping_city,
        shipping_country = user.shipping_country,
        shipping_zip_code = user.shipping_zip_code,
        email_verification_token = hash_token,
        email_verification_expiration = expiracion,
        is_email_verified = False
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        enviar_email_activacion(
            email = new_user.email,
            token = token,
            nombre = f"{new_user.first_name} {new_user.last_name}"
        )

        logger.info(f"Usuario {new_user.email} registrado exitosamente.")
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error al registrar usuario {user.email}: {str(e)}")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = f"Error al crear el usuario: {str(e)}"
        )
    finally:
        db.close()

    
@router.get("/activate/")
def activate_email(email: str, token: str, db: Session = Depends(get_db)):
    logger.info(f"Intento de activación de cuenta para: {email}")
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        logger.warning(f"Activación fallida: Usuario {email} no encontrado")
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail = "Usuario no encontrado"
        )
    
    if not usuario.email_verification_token or not usuario.email_verification_expiration:
        logger.warning(f"Activación fallida: No se encontró token para {email}")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "No se encontró un token de verificación"
        )
    
    if datetime.datetime.now() > usuario.email_verification_expiration:
        logger.warning(f"Activación fallida: Token expirado para {email}")    
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "El token ha expirado"
        )
    
    if not bcrypt.checkpw(token.encode('utf-8'), usuario.email_verification_token.encode('utf-8')):
        logger.warning(f"Activación fallida: Token inválido para {email}")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "Token inválido"
        )
    
    if usuario.account_status == AccountStatus.pending:    
        usuario.is_email_verified = True
        usuario.email_verification_token = None
        usuario.email_verification_expiration = None 
        usuario.account_status = AccountStatus.active  
        db.commit()
        db.refresh(usuario)
        db.close()
        logger.info(f"Usuario {email} activado exitosamente.")
        return {"message": "Email activado exitosamente"}
    elif usuario.account_status == AccountStatus.active:
        logger.warning(f"Activación fallida: Usuario {email} ya ha sido activado")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "El usuario ya ha sido activado"
        )
    elif usuario.account_status == AccountStatus.banned:
        logger.warning(f"Activación fallida: Usuario {email} ha sido suspendido")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "El usuario ha sido suspendido"
        )
    elif usuario.account_status == AccountStatus.deleted:
        logger.warning(f"Activación fallida: Usuario {email} ha sido eliminado")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "El usuario ha sido eliminado"
        )
    else:
        logger.warning(f"Activación fallida: Estado de cuenta inválido para {email} estado: {usuario.account_status}")
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST, 
            detail = "Estado de cuenta inválido"
        )


@router.post("/login")
async def login(form_data: OAuth2EmailRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Intento de login para el usuario: {form_data.email}")
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Inicio de sesión fallido para {form_data.email}")
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Credenciales incorrectas",
            headers = {"WWW-Authenticate": "Bearer"},
        )
    
    user.last_login = datetime.datetime.now()
    db.commit()
    db.refresh(user)
    db.close()
    
    access_token = create_access_token(data={"email": user.email})
    logger.info(f"Inicio de sesión exitoso para {form_data.email}, última conexión actualizada.")
    return {"access_token": access_token, "token_type": "bearer"}