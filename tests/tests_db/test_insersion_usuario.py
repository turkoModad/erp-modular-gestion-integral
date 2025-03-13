from app.db.modelos import Usuario


def test_creacion_usuario(db_session):
    """Prueba completa de CRUD para usuario"""
    # Creación
    nuevo_usuario = Usuario(
        nombre="Usuario de Prueba",
        email="test@example.com",
        password="Password123!",
        es_admin=False
    )
    
    db_session.add(nuevo_usuario)
    db_session.commit()
    
    # Lectura
    usuario_db = db_session.query(Usuario).filter_by(email="test@example.com").first()
    assert usuario_db, "❌ Usuario no encontrado después de creación"
    
    # Actualización
    usuario_db.nombre = "Nombre Actualizado"
    db_session.commit()
    usuario_actualizado = db_session.get(Usuario, usuario_db.id)
    assert usuario_actualizado.nombre == "Nombre Actualizado", "❌ Fallo en actualización"
    
    # Eliminación
    db_session.delete(usuario_actualizado)
    db_session.commit()
    usuario_eliminado = db_session.get(Usuario, usuario_db.id)
    assert not usuario_eliminado, "❌ Fallo en eliminación"