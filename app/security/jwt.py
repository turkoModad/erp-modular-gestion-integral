from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv
import os
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from typing import Optional
from app.db.models import Usuario, AccountStatus
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.security.exceptions import TokenValidationError


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl = "/auth/login", scheme_name = "EmailBasedAuth")

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")  
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")) 


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Crea un JWT usando el email como subject (sub)
    
    Args:
        data: Diccionario con los datos del usuario (debe contener 'email')
        expires_delta: Tiempo de expiración personalizado
    
    Returns:
        str: Token JWT firmado
    """
    if "email" not in data:
        raise ValueError("El campo 'email' es requerido para generar el token")
    
    to_encode = data.copy()
    expire = datetime.now(tz = timezone.utc) + (
        expires_delta or timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({
        "exp": expire,
        "sub": str(to_encode["email"])
        })
    return jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)


def verify_access_token(token: str):
    """
    Verifica y decodifica un JWT
    
    Args:
        token: JWT a validar
    
    Returns:
        dict: Payload decodificado
    
    Raises:
        TokenValidationError: Si el token es inválido o está expirado
    """
    try:
        payload = jwt.decode(
            token, 
            SECRET_KEY, 
            algorithms = [ALGORITHM],
            options = {"require_sub": True}
        )                
        if not payload.get("sub"):
            raise TokenValidationError("Subject (sub) no encontrado en el token")
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise TokenValidationError("Token expirado")
    except jwt.JWTClaimsError:
        raise TokenValidationError("Claim inválido en el token")
    except Exception as e:
        raise TokenValidationError(f"Error validando token: {str(e)}")


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