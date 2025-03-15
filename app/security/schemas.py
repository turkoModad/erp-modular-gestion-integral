from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from fastapi import Form
from app.security.utils import validar_contraseña_fuerte


class Usuario(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
   
    @field_validator('password')
    def check_password_length(cls, password):
        if len(password) < 8 or len(password) > 25:
            raise ValueError("La contraseña debe tener entre 8 y 25 caracteres.")
        
        if not validar_contraseña_fuerte(password):
            raise ValueError("La contraseña no es suficientemente fuerte. Debe tener al menos 8 caracteres, incluir una mayúscula, un número y un carácter especial.")
        return password

    model_config = ConfigDict(from_attributes=True)  


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True) 


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    es_admin: bool

    model_config = ConfigDict(from_attributes=True)  


class OAuth2EmailPasswordRequestForm:
    def __init__(
        self,
        username: str = Form(..., description="Ingresa tu EMAIL"), 
        password: str = Form(...)
    ):
        self.email = username 
        self.password = password