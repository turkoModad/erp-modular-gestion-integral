# import re

# def validar_contraseña_fuerte(password: str) -> bool:
#     password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,25}$"
#     return re.match(password_regex, password) is not None

from pydantic import BeforeValidator
from typing import Annotated
import re
from pydantic import Field

def validar_contraseña_fuerte(password: str) -> str:
    """Valida: 8+ chars, 1 mayúscula, 1 minúscula, 1 número, 1 símbolo"""
    if not re.fullmatch(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$", password):
        raise ValueError(
            "La contraseña debe tener al menos 8 caracteres, "
            "1 mayúscula, 1 minúscula, 1 número y 1 símbolo (@$!%*?&#)"
        )
    return password


PasswordStr = Annotated[
    str,
    Field(
        min_length=8,
        max_length=30,
        examples=["MySecurePass123!"],
        description="Contraseña segura con requisitos complejos"
    ),
    BeforeValidator(validar_contraseña_fuerte)
]