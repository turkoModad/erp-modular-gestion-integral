from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from app.db.models.models import Usuario, AccountStatus
from app.db.database import get_db
from app.security.exceptions import TokenValidationError
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl = "/auth/login", scheme_name = "bearerAuth")

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) 


def create_access_token(
    email: str, 
    otp_verified: bool = False, 
    expires_delta: Optional[timedelta] = None, 
    extra_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Crea un token JWT usando el email como subject (sub).
    
    Args:
        email (str): Correo del usuario.
        otp_verified (bool): Indica si el usuario ha pasado la verificación OTP.
        expires_delta (Optional[timedelta]): Tiempo de expiración personalizado.
        extra_data (Optional[Dict[str, Any]]): Información adicional que se quiera incluir en el token.
    
    Returns:
        str: Token JWT firmado.
    """
    if not email:
        raise ValueError("El campo 'email' es requerido para generar el token")

    to_encode = {
        "sub": email,
        "email": email,
        "otp_verified": otp_verified,  
        "exp": datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    }
    
    if extra_data:
        to_encode.update(extra_data)

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verifica y decodifica un token de acceso JWT.

    Args:
        token (str): El token JWT a verificar.

    Returns:
        Dict[str, Any]: El payload decodificado si el token es válido.

    Raises:
        TokenValidationError: Si el token es inválido o ha expirado.
    """
    credentials_exception = TokenValidationError("Token inválido o expirado")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])        
        email: str = payload.get("sub")
        if not email:
            raise credentials_exception
        
        return payload  
    
    except JWTError:
        raise credentials_exception



def get_current_user(
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
):
    """
    Obtiene el usuario actual basado en el token JWT
    
    Args:
        db: Sesión de base de datos
        token: JWT recibido
    
    Returns:
        Usuario: Modelo de usuario autenticado
    
    Raises:
        TokenValidationError: Si no se puede validar el usuario
    """
    try:
        payload = verify_access_token(token)
        email = payload.get("sub")
        
        if not email:
            raise TokenValidationError("Email no encontrado en el token")
        
        user = db.query(Usuario).filter(Usuario.email == email).first()
        
        if not user:
            raise TokenValidationError("Usuario no encontrado")
            
        if user.account_status != AccountStatus.active:
            raise TokenValidationError("Cuenta inactiva")
            
        return user
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise TokenValidationError(str(e))
    


def get_current_verified_user(token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    

    if not payload.get("otp_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OTP verification required"
        )
    
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if user is None:
        raise credentials_exception

    if not user.account_status:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account inactive"
        )

    return user