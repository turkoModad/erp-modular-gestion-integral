from typing import Optional
from pydantic import BaseModel
from pydantic import ConfigDict, field_validator
from app.security.utils import validar_contraseña_fuerte


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
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, new_password):
        if not validar_contraseña_fuerte(new_password):
            raise ValueError(
                "La nueva contraseña no es segura. Debe incluir al menos 8 caracteres, "
                "una mayúscula, un número y un carácter especial."
            )
        return new_password