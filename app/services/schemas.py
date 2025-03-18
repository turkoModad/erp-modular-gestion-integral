from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UsuarioActivacion(BaseModel):
    email: EmailStr
    email_verification_token: str
    email_verification_expiration: datetime

    model_config = ConfigDict(from_attributes=True)