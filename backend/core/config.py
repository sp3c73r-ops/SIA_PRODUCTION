from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    APP_NAME: str = "Système Intégré des Archives Documentaires"

    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str

    SECRET_KEY: str

    ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"


settings = Settings()