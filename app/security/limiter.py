from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI

def create_limiter(app: FastAPI):
    limiter = Limiter(key_func=get_remote_address)
    app.limiter = limiter
    return limiter