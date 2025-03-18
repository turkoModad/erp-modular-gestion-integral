import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base, get_db
from app.db.config import settings
from app.db.models import Usuario
from app.security.hashing import hash_password
from main import app
from datetime import datetime


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
        "email": "test@example.com",
        "password": "pasSword$123",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "1234567890",
        "date_of_birth": "1990-01-01",
        "shipping_address": "123 Main St",
        "shipping_city": "Springfield",
        "shipping_country": "USA",
        "shipping_zip_code": "12345",
        "two_factor_enabled": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"


def test_login_exitoso(client, db_session):
    # Crear usuario con contraseña hasheada
    password = "23secur#Password"
    password_hash = hash_password(password)
    hoy = datetime.today()
    hace_20_anios = hoy.replace(year=hoy.year - 20)

    user = Usuario(
        email="user@example.com", 
        password_hash = password_hash, 
        first_name="Test",
        last_name="User", 
        date_of_birth=hace_20_anios
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post("/auth/login", 
        data={"username": "user@example.com", "password": password}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_fallido(client):
    response = client.post("/auth/login", 
        data={"username": "wrong@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_perfil_usuario(client, db_session):
    password = "09secur#Password"
    password_hash = hash_password(password)
    hoy = datetime.today()
    hace_20_anios = hoy.replace(year=hoy.year - 20)
    user = Usuario(
        first_name="Profile12", 
        last_name="profile12", 
        email="profile@example.com", 
        password_hash=password_hash, 
        date_of_birth=hace_20_anios
    )
    db_session.add(user)
    db_session.commit()
    
    login_response = client.post("/auth/login", data={"username": "profile@example.com", "password": password})
    token = login_response.json()["access_token"]
    
    response = client.post("/auth/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "profile@example.com"


def test_registro_usuario_duplicado(client, db_session):
    # Crear usuario inicial
    password = "23secur?Password"
    password_hash = hash_password(password)
    hoy = datetime.today()
    hace_20_anios = hoy.replace(year=hoy.year - 20)
    
    user = Usuario(
        first_name="Test User",
        last_name="test user",
        email="duplicate@example.com",
        password_hash=password_hash,
        date_of_birth=hace_20_anios  
    )
    db_session.add(user)
    db_session.commit()
    
    request_data = {
        "first_name": "Test User",
        "last_name": "test user",
        "email": "duplicate@example.com", 
        "password": "23secur?Password",
        "date_of_birth": hace_20_anios.isoformat() 
    }
    
    response = client.post("/auth/registro/", json=request_data)
    print("Error details:", response.json())  # Debug
    
    assert response.status_code == 400
    assert response.json()["detail"] == "El usuario ya existe"


def test_login_usuario_inexistente(client):
    response = client.post("/auth/login", 
        data={"username": "nonexistent@example.com", "password": "anyPassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"


def test_acceso_ruta_protegida_con_usuario_inexistente(client):
    response = client.post("/auth/users/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    assert response.json()["detail"] in ["No se pudo validar las credenciales", "Not authenticated"]



def test_acceso_ruta_protegida_sin_autenticacion(client):
    response = client.post("/auth/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] in ["No se pudo validar las credenciales", "Not authenticated"]


def test_acceso_ruta_protegida_con_token_valido(client, db_session):
    password = "valiD@password"
    password_hash = hash_password(password)
    hoy = datetime.today()
    hace_20_anios = hoy.replace(year=hoy.year - 20)
    user = Usuario(
        first_name="Protected User", 
        last_name = "protected user", 
        email="protected@example.com", 
        password_hash=password_hash, 
        date_of_birth=hace_20_anios
    )
    db_session.add(user)
    db_session.commit()
    
    login_response = client.post("/auth/login", 
        data={"username": "protected@example.com", "password": password})
    token = login_response.json()["access_token"]
    
    response = client.post("/auth/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "protected@example.com"