<<<<<<< HEAD
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Agent API"
    admin_email: str
    database_url: str

    class Config:
        env_file = ".env"

=======
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Agent API"
    admin_email: str
    database_url: str

    class Config:
        env_file = ".env"

>>>>>>> 6decf83 (Memory & Logging Layer)
settings = Settings()