from typing import Optional
from pydantic import BaseModel
from pydantic import ConfigDict
from app.security.utils import PasswordStr


class UsuarioUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    two_factor_enabled: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioUpdatePassword(BaseModel):
    current_password: str
    new_password: PasswordStr
