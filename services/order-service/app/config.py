import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://order_user:order_password@localhost:5434/order_db"
    menu_service_url: str = "http://localhost:8001"
    warehouse_service_url: str = "http://localhost:8002"
    service_host: str = "0.0.0.0"
    service_port: int = 8003
    app_name: str = "Order Service"
    debug: bool = False
    testing: bool = False


settings = Settings()
