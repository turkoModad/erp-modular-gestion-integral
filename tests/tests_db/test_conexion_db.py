from sqlalchemy import text
import pytest

def test_conexion_db(db_session):
    """Verifica que la conexión a la base de datos es exitosa ejecutando una consulta simple."""
    try:
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
    except Exception as e:
        pytest.fail(f"Error al conectar con la base de datos: {e}")