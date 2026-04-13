from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://auth_user:auth_password@localhost:5435/auth_db"
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480   # 8 hours
    app_name: str = "Auth Service"
    debug: bool = False

    # Initial admin credentials (used only on first launch if no users exist)
    admin_email: str = "admin@restaurant.com"
    admin_password: str = "admin123"
    admin_full_name: str = "Администратор"


settings = Settings()
