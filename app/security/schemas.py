from pydantic import BaseModel


class Usuario(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True


class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str

    class Config:
        from_attributes = True


class UsuarioLogin(BaseModel):
    email: str
    password: str

    class Config:
        from_attributes = True


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: str
    es_admin: bool

    class Config:
        from_attributes = True
