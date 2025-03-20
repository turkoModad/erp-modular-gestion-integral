from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.models import Usuario
from app.security.hashing import verify_password, hash_password
from app.security.jwt import create_access_token
from app.services.email_service import enviar_email_activacion
from app.services.hash_activacion_email import crear_token, verificar_token
from app.services.otp_service import OTPService
from app.services.email_otp import enviar_email_otp
from app.services.schemas import OTPRequest
from app.security.schemas import UsuarioCreate, UsuarioOut
from app.security.dependencies import OAuth2EmailRequestForm
from app.enums import AccountStatus
import datetime
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates")


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
    

    
@router.get("/activar/", response_class=JSONResponse)
def mostrar_form_activacion(request: Request, email: str, token: str, response: Response):
    logger.info(f"Generando formulario de activación para el email: {email}")
    
    response = templates.TemplateResponse("activar.html", {"request": request})
    response.set_cookie(
        key="activation_data",
        value=f"{email}:{token}",
        secure=False,
        samesite="Lax",
        max_age=600 
    )
    
    logger.info(f"Cookie de activación establecida para el email: {email}")
    return response



@router.post("/activate/")
def activate_email(request: Request, response: Response, db: Session = Depends(get_db)):
    # Leer datos desde cookie
    activation_data = request.cookies.get("activation_data")
    
    if not activation_data:
        logger.warning("Intento de activación sin datos de cookie")
        raise HTTPException(400, "Datos de activación no encontrados")
    
    email, token = activation_data.split(":", 1)
    
    logger.info(f"Recibido email: {email} y token para activación.")
    
    if not email or not token:
        logger.warning("Faltan datos de activación")
        raise HTTPException(status_code=400, detail="Faltan datos de activación")
    
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        logger.warning(f"El usuario con email {email} no existe en la base de datos.")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    try:
        verificar_token(token, usuario)
        logger.info(f"Token de activación verificado para el usuario: {email}")
    except ValueError as e:
        logger.error(f"Error al verificar el token para el usuario {email}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    if usuario.account_status == AccountStatus.pending:
        usuario.is_email_verified = True
        usuario.email_verification_token = None
        usuario.email_verification_expiration = None 
        usuario.account_status = AccountStatus.active  
        db.commit()
        db.refresh(usuario)

        response.delete_cookie("activation_data")

        logger.info(f"Cuenta activada exitosamente para el usuario {email}")
        return JSONResponse(content={"message": "Email activado exitosamente"})
    
    logger.warning(f"El usuario {email} ya ha sido activado o no es válido para activación.")
    raise HTTPException(status_code=400, detail="El usuario ya ha sido activado o no es válido")



@router.post("/login/")
async def login(form_data: OAuth2EmailRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Intento de login para el usuario: {form_data.email}")
    
    user = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Inicio de sesión fallido para {form_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.account_status is None or user.account_status != AccountStatus.active:
        logger.warning(f"Usuario {form_data.email} no activado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no activada. Revisa tu correo electrónico para activarla.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    otp_service = OTPService(db) 
    otp_code = otp_service.generate_otp(user.email)
    await enviar_email_otp(user.email, otp_code)

    user.last_login = datetime.datetime.now()
    db.commit()
    db.refresh(user)  

    logger.info(f"OTP enviado para el usuario {form_data.email}")
    
    return {"detail": "OTP enviado a tu correo. Ingresa el código para completar el login."}


@router.post("/verify_otp/")
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
    access_token = create_access_token(
    email=otp_data.email, 
    otp_verified=True
    )    
    logger.info(f"Login exitoso para el usuario {otp_data.email}.")    
    return {"access_token": access_token, "token_type": "bearer"}