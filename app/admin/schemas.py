from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from app.security.utils import PasswordStr
from app.enums import AccountStatus, Role
from datetime import date


class UsersSchema(BaseModel):
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
    account_status: AccountStatus 
    role: Role 
    two_factor_enabled: Optional[bool] = False
    is_email_verified: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    two_factor_enabled: Optional[bool] = None
    password: Optional[PasswordStr] = None
    role: Optional[Role] 

    model_config = ConfigDict(from_attributes=True) 


class UsuarioStatus(BaseModel):
    new_status: Optional[AccountStatus] 

    model_config = ConfigDict(from_attributes=True) 