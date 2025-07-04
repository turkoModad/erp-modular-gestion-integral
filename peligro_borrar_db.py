import asyncio
import logging
from app.db.database import Base, engine
from app.db.models.models import Usuario, OTP, FailedLoginAttempt


logger = logging.getLogger(__name__)


async def reset_database():
    try:
        logger.info("Borrando todas las tablas...")
        await asyncio.to_thread(Base.metadata.drop_all, bind=engine)
        logger.info("Tablas borradas.")
        
    except Exception as e:
        logger.error(f"Error durante reset de la base: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(reset_database())