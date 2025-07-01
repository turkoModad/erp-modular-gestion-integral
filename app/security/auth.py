from fastapi import APIRouter, HTTPException, Depends, status, Request, Form
from fastapi.responses import JSONResponse, Response, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models.models import Usuario, FailedLoginAttempt
from app.security.hashing import verify_password, hash_password
from app.security.schemas import UsuarioCreate, UsuarioOut
from app.security.dependencies import OAuth2EmailRequestForm
from app.security.jwt import create_access_token, verify_access_token
from app.services.email_service_activation import enviar_email_activacion
from app.services.hash_activacion_email import crear_token, verificar_token
from app.services.otp_service import OTPService
from app.services.email_otp import enviar_email_otp
from app.services.schemas import OTPRequest
from app.enums import AccountStatus, Role
from slowapi import Limiter
from slowapi.util import get_remote_address
from dotenv import load_dotenv
import logging
import os


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


router = APIRouter()

templates = Jinja2Templates(directory="frontend/templates/auth")


def get_limiter(request: Request):
    if hasattr(request.app, "limiter"):
        return request.app.limiter
    raise RuntimeError("Limiter no ha sido inicializado correctamente")


limiter = Limiter(key_func=get_remote_address)

load_dotenv()

PORT = os.getenv("PORT")


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
        nombre = user.first_name
        asunto = f"{nombre}, activa tu cuenta en CodePyHub"
        cuerpo = f"""
        <h1>¡Bienvenido {nombre}!</h1>
        <p>Haz clic en el siguiente enlace para activar tu cuenta:</p>
        <a href="http://localhost:{PORT}/activar/?email={user.email}&token={token}">Activar cuenta</a>
        """

        enviar_email_activacion(email = user.email, asunto = asunto, cuerpo = cuerpo)

    
    except Exception as e:
        logger.error(f"No se pudo enviar el email a {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el email de verificación. Intente nuevamente."
        )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Usuario {new_user.email} registrado exitosamente.")
        return new_user

    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar el usuario {user.email} en la base: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al guardar el usuario en la base de datos."
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
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user:
        logger.warning(f"Intento de login con usuario inexistente: {form_data.email}")
        raise generic_error

    failed_attempt = db.query(FailedLoginAttempt).filter(
        FailedLoginAttempt.email == form_data.email
    ).first()
    
    if failed_attempt and failed_attempt.is_locked:
        tiempo_bloqueo = datetime.now() - failed_attempt.last_attempt
        if tiempo_bloqueo < timedelta(minutes=15):
            logger.warning(f"Cuenta {form_data.email} bloqueada temporalmente")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Espere 15 minutos."
            )
        else:
            # Eliminar registro si ya pasó el bloqueo
            db.delete(failed_attempt)
            db.commit()   
    
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Inicio de sesión fallido para {form_data.email}")
        if failed_attempt:
            failed_attempt.attempt_count += 1
            failed_attempt.last_attempt = datetime.now()
            if failed_attempt.attempt_count >= 5:
                failed_attempt.is_locked = True
        else:
            failed_attempt = FailedLoginAttempt(
                email=form_data.email,
                attempt_count=1,
                last_attempt=datetime.now()
            )
            db.add(failed_attempt)
        
        db.commit()
        
        # Verificar si se superó el límite
        if failed_attempt.attempt_count >= 5:
            logger.warning(f"Bloqueando cuenta: {form_data.email}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiados intentos fallidos. Cuenta bloqueada por 15 minutos."
            )
        
        else:
            raise generic_error
    
    if user.account_status is None or user.account_status != AccountStatus.active:
        current_status = user.account_status.name if user.account_status else "None"
        logger.warning(f"El usuario {form_data.email} no puede iniciar porque tiene un status de: {current_status}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cuenta no activada. Revisa tu correo electrónico para activarla.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    failed_attempt = db.query(FailedLoginAttempt).filter(
            FailedLoginAttempt.email == form_data.username
        ).first()
        
    if failed_attempt:
        db.delete(failed_attempt)
        db.commit() 

    if user.two_factor_enabled or user.role == Role.ADMIN:    
        otp_service = OTPService(db) 
        otp_code, expiration, user_id = otp_service.create_otp_code(user.email)
        try:
            await enviar_email_otp(user.email, otp_code)
        except RuntimeError as e:
            logger.error(f"Error al enviar OTP a {user.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo enviar el código OTP. Intente nuevamente más tarde."
            )

        try:
            otp_service.save_otp(user_id, otp_code, expiration)
        except Exception as e:
            logger.error(f"No se pudo guardar el OTP en la base: {str(e)}")
            raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno guardando el código OTP"
        )

        user.last_login = datetime.now()
        db.commit()
        db.refresh(user)  

        logger.info(f"OTP enviado para el usuario {form_data.email}")    
        return {"detail": "OTP enviado a tu correo. Ingresa el código para completar el login."}
    
    access_token = create_access_token(
        email = user.email, 
        otp_verified = True, 
        role = Role(user.role) 
    )
    logger.info(f"Login exitoso para el usuario {user.email}.") 
    logger.info(f" Para su seguridad, recuerde activar su doble factor de autenticacion")   
    return {"access_token": access_token, "token_type": "bearer"}
    


@router.post("/verify_otp/")
@limiter.limit("5/minute")  
async def verify_otp(
    request: Request,
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
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    access_token = create_access_token(
    email = otp_data.email, 
    otp_verified = True,
    role = Role(user.role)
    )    
    logger.info(f"Login exitoso para el usuario {otp_data.email}.")    
    return {"access_token": access_token, "token_type": "bearer"}




@router.post("/recuperar_acceso/")
async def recuperar_acceso(email: EmailStr, db: Session = Depends(get_db)):
    logger.info(f"Solicitud de recuperación para: {email}")
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        logger.warning(f"Usuario no encontrado: {email}")
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
    <a href="http://localhost:{PORT}/reset-password-form?token={reset_token}">
        Restablecer contraseña
    </a>
    """

    try:
        enviar_email_activacion(user.email, asunto, cuerpo)
        logger.info(f"Email de recuperación enviado a: {user.email}")
        return {"detail": "Se ha enviado un enlace para restablecer tu contraseña"}
    except Exception as e:
        logger.error(f"No se pudo enviar el email a {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo enviar el correo. Intenta más tarde."
        )



@router.get("/reset-password-form", response_class=HTMLResponse)
def mostrar_formulario_cambio(token: str, request: Request):
    logger.info("Solicitud de formulario con token recibido")

    try:
        payload = verify_access_token(token)
        if payload.get("token_type") != "password_reset":
            logger.warning("Token inválido")
            raise HTTPException(status_code=403, detail="Token inválido")
        logger.info("Token válido, mostrando formulario")
        return templates.TemplateResponse("reset_password_form.html", {
            "request": request,
            "token": token
        })
    except Exception:
        logger.warning("Token inválido o expirado")
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN, 
            detail="Token inválido o expirado"
        )



@router.post("/reset-password/")
def cambiar_password(
    token: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    logger.info("Solicitud de cambio de contraseña vía token")
    if new_password != confirm_password:
        logger.warning("Las contraseñas no coinciden")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas no coinciden"
            )

    try:
        payload = verify_access_token(token)
        if payload.get("token_type") != "password_reset":
            logger.warning("Token inválido")
            raise HTTPException(
                status_code = status.HTTP_403_FORBIDDEN, 
                detail="Token inválido"
            )

        email = payload.get("sub")
        user = db.query(Usuario).filter(Usuario.email == email).first()
        if not user:
            logger.warning(f"Usuario no encontrado: {email}")

            raise HTTPException(
                status_code = status.HTTP_404_NOT_FOUND, 
                detail="Usuario no encontrado"
                )

        user.password_hash = hash_password(new_password)
        db.commit()

        logger.info(f"Contraseña actualizada para: {user.email}")
        return {"detail": "Contraseña actualizada correctamente"}
    except Exception as e:
        logger.error(f"Token inválido o expirado: {str(e)}")
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN, 
            detail = "Token inválido o expirado"
        )