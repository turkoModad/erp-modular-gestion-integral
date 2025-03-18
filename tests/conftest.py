import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.config import settings
from app.db.models import Usuario
from app.security.hashing import hash_password
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configuración completa de la base de datos de pruebas"""
    print("\n[1/3] Creando estructura de base de datos...")
    Base.metadata.create_all(engine)
    
    # Verificación de tablas creadas
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"[2/3] Tablas detectadas: {tables}")
    
    yield 
    
    print("\n[3/3] Limpiando base de datos...")
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session():
    """Sesión de base de datos con transacción aislada"""
    connection = engine.connect()
    transaction = connection.begin_nested()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


def test_login_exitoso(db_session):
    """Crear usuario con contraseña HASHED"""
    password = "validpassword123"
    hashed_password = hash_password(password)
    user = Usuario(
        first_name = "Login User",
        last_name = "Test",
        email = "login@test.com",
        password = hashed_password,
        date_of_birth = "2005-03-17 17:26:17.680282"
    )
    db_session.add(user)
    db_session.commit()
    
    login_data = {
        "email": "login@test.com",
        "password": password
    }    
    response = client.post("/auth/login", data = login_data)
    assert response.status_code == 200


@pytest.fixture(autouse=True)
def limpiar_db(db_session):
    """Limpiar la base de datos antes de cada test"""
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()