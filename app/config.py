from pydantic_settings import BaseSettings
from functools import lru_cache
import sys
from pydantic import ConfigDict


class BaseSettingsConfig(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")


class ProdSettings(BaseSettingsConfig):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    SECRET_KEY: str
    
    @property
    def DATABASE_URL(self):        
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    

class BaseSettingsConfig(BaseSettings):
    model_config = ConfigDict(env_file=".env.test", extra="ignore")
    

class TestSettings(BaseSettingsConfig):
    DATABASE_URL: str


@lru_cache
def get_settings():
    if "pytest" in sys.modules:
        print("en testing")
        return TestSettings() 
    else:
        print("en produccion")
        return ProdSettings() 

settings = get_settings()