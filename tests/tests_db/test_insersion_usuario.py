from app.db.modelos import Usuario

def test_insersion_usuario(db_session):
    """Prueba la inserción de un usuario en la base de datos."""
    test_user = Usuario(
        nombre="testuser2", 
        email="test2@example.com",
        password="hashedpass",
        es_admin=False
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)
    
    user = db_session.query(Usuario).filter_by(nombre="testuser2").first()
    assert user is not None
    assert user.email == "test2@example.com"