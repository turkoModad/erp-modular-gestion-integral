import uvicorn
from fastapi import FastAPI
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from app.db.database import Base, engine, check_tables_exist
from app.security import auth
from app.users import routes as users
from app.admin import routes as admin
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


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

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


security_schemes = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT"
    }
}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Mi API",
        version="1.0",
        description="Autenticación JWT con OTP",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = security_schemes
    openapi_schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi


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



@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("frontend/static/favicon.ico")
    

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8010))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)       