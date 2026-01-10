from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    POSTGRES_URL: str
    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    CONFIRMATION_SECRET_KEY: str
    ALGORITHM: str = "HS256"  # Algoritmo de codificação padrão
    CONFIRMATION_TOKEN_EXPIRE_MINUTES: int = 15  # Valor padrão caso não esteja no .env
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Valor padrão caso não esteja no .env
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Valor padrão caso não esteja no .env
    RESET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 15  # Valor padrão caso não esteja no .env
    SMTP_SECRET_KEY: str
    RESET_PASSWORD_SECRET_KEY: str

    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = "thales.lps.araujo@gmail.com"
    ADMIN_EMAIL: str = "thales.lps.araujo@gmail.com"
    FRONTEND_URL: str = "http://localhost:3000"
    # Lista de origens permitidas para CORS (separadas por vírgula no .env)
    # Ex.: CORS_ORIGINS=http://localhost:5173,https://minhaapp.com
    CORS_ORIGINS: List[str] = []

    class Config:
        env_file = ".env"  # Arquivo de onde as variáveis serão carregadas
        extra = "ignore"  # Ignora variáveis extras no .env que não estão definidas aqui
        case_sensitive = True


settings: Settings = Settings()
