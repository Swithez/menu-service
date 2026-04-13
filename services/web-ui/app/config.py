from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    menu_service_url: str = "http://localhost:8001"
    warehouse_service_url: str = "http://localhost:8002"
    order_service_url: str = "http://localhost:8003"
    auth_service_url: str = "http://localhost:8004"
    secret_key: str = "dev-secret-change-in-production"
    jwt_secret: str = "change-me-in-production-use-long-random-string"
    jwt_algorithm: str = "HS256"
    debug: bool = False


settings = Settings()
