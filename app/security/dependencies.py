from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Form
from typing import Optional


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
    