import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.db.config import settings
from app.db.modelos import Usuario
from app.security.hashing import hash_password
from main import app

# Configuración de la base de datos de pruebas
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Configura la base de datos de pruebas"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de base de datos aislada"""
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Cliente de prueba con base de datos inyectada"""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_registro_usuario(client):
    response = client.post("/auth/registro/", json={
        "nombre": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_login_exitoso(client, db_session):
    # Crear usuario con contraseña hasheada
    password = "securepassword"
    hashed_password = hash_password(password)
    user = Usuario(nombre="User", email="user@example.com", password=hashed_password)
    db_session.add(user)
    db_session.commit()
    
    response = client.post("/auth/login", data={"username": "user@example.com", "password": password})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_fallido(client):
    response = client.post("/auth/login", data={"username": "wrong@example.com", "password": "wrongpassword"})
    assert response.status_code == 401


def test_perfil_usuario(client, db_session):
    password = "userpassword"
    hashed_password = hash_password(password)
    user = Usuario(nombre="Profile User", email="profile@example.com", password=hashed_password)
    db_session.add(user)
    db_session.commit()
    
    login_response = client.post("/auth/login", data={"username": "profile@example.com", "password": password})
    token = login_response.json()["access_token"]
    
    response = client.get("/auth/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "profile@example.com"


def test_registro_usuario_duplicado(client, db_session):
    # Crear usuario inicial
    db_session.add(Usuario(nombre="Test User", email="duplicate@example.com", password=hash_password("password123")))
    db_session.commit()
    
    # Intentar registrar el mismo usuario nuevamente
    response = client.post("/auth/registro/", json={
        "nombre": "Test User",
        "email": "duplicate@example.com",
        "password": "password123"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "El usuario ya existe"

def test_login_usuario_inexistente(client):
    response = client.post("/auth/login", data={"username": "nonexistent@example.com", "password": "anyPassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"


def test_acceso_ruta_protegida_con_usuario_inexistente(client):
    response = client.get("/auth/users/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] in ["No se pudo validar las credenciales", "Not authenticated"]



def test_acceso_ruta_protegida_sin_autenticacion(client):
    response = client.get("/auth/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] in ["No se pudo validar las credenciales", "Not authenticated"]


def test_acceso_ruta_protegida_con_token_valido(client, db_session):
    password = "validpassword"
    hashed_password = hash_password(password)
    user = Usuario(nombre="Protected User", email="protected@example.com", password=hashed_password)
    db_session.add(user)
    db_session.commit()
    
    login_response = client.post("/auth/login", data={"username": "protected@example.com", "password": password})
    token = login_response.json()["access_token"]
    
    response = client.get("/auth/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"