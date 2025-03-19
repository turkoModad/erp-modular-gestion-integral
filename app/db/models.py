from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from app.db.database import Base
from sqlalchemy.sql import func
from app.enums import AccountStatus, Role


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key = True, autoincrement = True)
    email = Column(String(100), unique = True, nullable = False)
    password_hash = Column(String(255), nullable = False)
    first_name = Column(String(100), nullable = False)
    last_name = Column(String(100), nullable = False)
    date_of_birth = Column(DateTime, nullable = False) 
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