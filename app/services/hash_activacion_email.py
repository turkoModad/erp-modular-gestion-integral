import bcrypt
import secrets
import datetime


def generar_token_activacion():
    return secrets.token_bytes(32).hex()


def crear_token(email):
    token = generar_token_activacion()
    hashed_token = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt(rounds=10))
    expiracion = datetime.datetime.now() + datetime.timedelta(hours=6)
    
    return token, hashed_token.decode('utf-8'), expiracion


def verificar_token(token_recibido, hash_almacenado, expiracion_almacenada):
    if datetime.datetime.now() > expiracion_almacenada:
        raise ValueError("Token expirado")
    
    if not bcrypt.checkpw(token_recibido.encode('utf-8'), hash_almacenado.encode('utf-8')):
        raise ValueError("Token inválido")
    
    return True