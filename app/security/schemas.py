from pydantic import BaseModel, ConfigDict, EmailStr
from fastapi import Form
from typing import Optional
from app.enums import AccountStatus, Role
from datetime import datetime, date
from app.security.utils import PasswordStr


class Usuario(BaseModel):
    email: str
    password: str

    model_config = ConfigDict(from_attributes=True)


class UsuarioCreate(BaseModel):
    email: EmailStr
    password: PasswordStr
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    account_status: AccountStatus = AccountStatus.pending
    role: Role = Role.CLIENT
    two_factor_enabled: Optional[bool] = False
    is_email_verified: Optional[bool] = False

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
    date_of_birth: date
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

    model_config = ConfigDict(from_attributes=True)


class ActivacionRequest(BaseModel):
    token: str = Form(...)
    email: EmailStr = Form(...)   

    model_config = ConfigDict(from_attributes=True)
