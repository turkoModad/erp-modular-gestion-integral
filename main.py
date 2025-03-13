import uvicorn
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from app.db.modelos import Usuario
from app.db.config import settings
from app.db.database import get_db, Base, engine, check_tables_exist


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación"""
    logger.info("Inicializando aplicación...")
    await initialize_database()
    yield
    logger.info("Cerrando aplicación...")

app = FastAPI(lifespan=lifespan)

async def initialize_database():
    """Inicialización asíncrona de la base de datos"""
    try:
        if not await asyncio.to_thread(check_tables_exist):
            logger.info("Creando tablas...")
            await asyncio.to_thread(Base.metadata.create_all, bind=engine)
            logger.info("Tablas creadas exitosamente")
        else:
            logger.info("Las tablas ya existen en la base de datos")
    except Exception as e:
        logger.error(f"Error crítico durante la inicialización: {str(e)}")
        raise RuntimeError("Error en inicialización de base de datos")


def consultar_usuarios(db: Session):
    usuarios = db.query(Usuario).all()
    return usuarios


@app.get("/", response_class=JSONResponse)
def obtener_usuarios(db: Session = Depends(get_db)):
    resultado = consultar_usuarios(db)
    if not resultado:
        return {"mensaje": "No hay usuarios en la base de datos."} 
    else:
        usuarios = []
        for usuario in resultado:
            usuarios.append(usuario.nombre)
        return usuarios
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)       