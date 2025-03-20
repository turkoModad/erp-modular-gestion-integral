from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from fastapi import Form
from typing import Optional
from app.security.utils import validar_contraseña_fuerte
from app.enums import AccountStatus, Role
from datetime import datetime


class Usuario(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: datetime
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    account_status: AccountStatus = AccountStatus.pending
    role: Role = Role.CLIENT
    two_factor_enabled: Optional[bool] = False
    is_email_verified: Optional[bool] = False


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
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: datetime
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    account_status: str
    role: str
    two_factor_enabled: bool
    is_email_verified: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None    

    model_config = ConfigDict(from_attributes=True)


class OAuth2EmailPasswordRequestForm:
    def __init__(
        self,
        username: str = Form(..., description="Ingresa tu EMAIL"), 
        password: str = Form(...)
    ):
        self.email = username 
        self.password = password


class ActivacionRequest(BaseModel):
    token: str = Form(...)
    email: EmailStr = Form(...)   