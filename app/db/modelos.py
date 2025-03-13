from sqlalchemy import Column, Integer, String, Boolean
from app.db.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    es_admin = Column(Boolean, default=False)