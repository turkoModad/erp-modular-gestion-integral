import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configuración completa de la base de datos de pruebas"""
    print("\n[1/3] 🔨 Creando estructura de base de datos...")
    Base.metadata.create_all(engine)
    
    # Verificación de tablas creadas
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[2/3] 🔍 Tablas detectadas: {tables}")
    
    yield  # Ejecución de pruebas
    
    print("\n[3/3] Limpiando base de datos...")
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session():
    """Sesión de base de datos con transacción aislada"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()