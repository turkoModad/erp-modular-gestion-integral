from app.db.models.models import Usuario
from app.security.hashing import hash_password
from datetime import date


def test_creacion_usuario(db_session):
    """Prueba completa de CRUD para usuario"""
    password = "Password123!"
    password_hash = hash_password(password)
    hoy = date.today()
    hace_20_anios = hoy.replace(year=hoy.year - 20)
    nuevo_usuario = Usuario(
        first_name="Usuario de Prueba",
        last_name="Apellido de Prueba",
        email="11test@example.com",
        password_hash=password_hash,
        date_of_birth=hace_20_anios
    )
    
    db_session.add(nuevo_usuario)
    db_session.commit()
    
    # Lectura
    usuario_db = db_session.query(Usuario).filter_by(email="11test@example.com").first()
    assert usuario_db, "Usuario no encontrado después de creación"
    
    # Actualización
    usuario_db.nombre = "Nombre Actualizado"
    db_session.commit()
    usuario_actualizado = db_session.get(Usuario, usuario_db.id)
    assert usuario_actualizado.nombre == "Nombre Actualizado", "Fallo en actualización"
    
    # Eliminación
    db_session.delete(usuario_actualizado)
    db_session.commit()
    usuario_eliminado = db_session.get(Usuario, usuario_db.id)
    assert not usuario_eliminado, "Fallo en eliminación"