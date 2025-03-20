from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.enums import AccountStatus, Role
from datetime import date



class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key = True, autoincrement = True)
    email = Column(String(100), unique = True, nullable = False)
    password_hash = Column(String(255), nullable = False)
    first_name = Column(String(100), nullable = False)
    last_name = Column(String(100), nullable = False)
    date_of_birth = Column(Date, nullable = False) 
    phone_number = Column(String(20), nullable = True)       
    shipping_address = Column(String(255), nullable = True)
    shipping_city = Column(String(100), nullable = True)
    shipping_country = Column(String(100), nullable = True)
    shipping_zip_code = Column(String(10), nullable = True)
    account_status = Column(Enum(AccountStatus), default = AccountStatus.pending)
    role = Column(Enum(Role), default=Role.CLIENT) 
    created_at = Column(DateTime, default = func.now())
    updated_at = Column(DateTime, server_default = func.now(), onupdate = func.now(), nullable = True)
    last_login = Column(DateTime, nullable = True)
    two_factor_enabled = Column(Boolean, default = False)
    is_email_verified = Column(Boolean, default = False)
    email_verification_token = Column(String(100), nullable = True) 
    email_verification_expiration = Column(DateTime, nullable = True)

    otps = relationship("OTP", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Usuario(email={self.email}, account_status={self.account_status})>"



class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"))
    code = Column(String(6), nullable=False)
    expiration = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)

    user = relationship("Usuario", back_populates="otps")
    
    def __init__(self, user_id: int, code: str, expiration: DateTime, is_used: bool = False):
        self.user_id = user_id
        self.code = code
        self.expiration = expiration
        self.is_used = is_used