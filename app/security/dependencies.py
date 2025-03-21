from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Form, Depends, HTTPException, status, Request
from typing import Optional
from app.db.models.models import Usuario
from app.security.jwt import get_current_user
from app.enums import Role
import logging


logger = logging.getLogger(__name__)


class OAuth2EmailRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        username: str = Form(..., alias="username", description="Ingresa tu EMAIL"),  # Swagger espera username
        password: str = Form(...),
        grant_type: str = Form("password"),
        scope: str = Form(""),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        """ Mapeamos username a email internamente """
        self.email = username
        super().__init__(
            username=username,
            password=password,
            scope=scope,
            grant_type=grant_type,
            client_id=client_id,
            client_secret=client_secret,
        )
    @property
    def email(self):
        return self.username
    @email.setter
    def email(self, value):
        self.username = value


def require_admin(user: Usuario = Depends(get_current_user)):
    """Verifica si el usuario es administrador"""
    if user.role != Role.ADMIN:
        logger.warning(f"El usuario {user.email} intentó acceder a un recurso restringido sin ser administrador.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido solo para administradores",
        )
    logger.info(f"El usuario {user.email} tiene permisos de administrador y está accediendo a un recurso restringido.")
    return user    