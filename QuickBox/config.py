from pydantic_settings import BaseSettings

ip_address = "192.168.1.33"


class Settings(BaseSettings):
    class Config:
        env_file = '../.env'
        case_sensitive = True

    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_NAME: str
    DATABASE_USER: str
    DATABASE_PASSWORD: str


settings = Settings()
