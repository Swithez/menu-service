from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://warehouse_user:warehouse_password@localhost:5433/warehouse_db"
    menu_service_url: str = "http://localhost:8001"
    service_host: str = "0.0.0.0"
    service_port: int = 8002
    app_name: str = "Warehouse Service"
    debug: bool = False


settings = Settings()
