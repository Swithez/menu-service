from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://menu_user:menu_password@localhost:5432/menu_db"
    service_host: str = "0.0.0.0"
    service_port: int = 8001
    app_name: str = "Menu Service"
    debug: bool = False


settings = Settings()
