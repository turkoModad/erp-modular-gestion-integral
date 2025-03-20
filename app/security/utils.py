import re

def validar_contraseña_fuerte(password: str) -> bool:
    password_regex = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,25}$"
    return re.match(password_regex, password) is not None