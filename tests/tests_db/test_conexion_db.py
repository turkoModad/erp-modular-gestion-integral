from sqlalchemy import inspect
from app.db.database import engine
from sqlalchemy import text


def test_conexion_bd():
    """Verifica la conexión a la base de datos"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
    except Exception as e:
        assert False, f"❌ Fallo de conexión: {e}"

def test_estructura_tablas():
    """Valida la existencia de todas las tablas requeridas"""
    inspector = inspect(engine)
    tablas_esperadas = {"usuarios"}
    tablas_existentes = set(inspector.get_table_names())
    
    faltantes = tablas_esperadas - tablas_existentes
    assert not faltantes, f"❌ Tablas faltantes: {faltantes}"