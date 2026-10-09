from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "mysql+pymysql://inventory_user:change_me@localhost:3306/smart_inventory"
    jwt_secret_key: str = "CHANGE_THIS_DEVELOPMENT_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = "lqes nfpr vnmv ofrq"
    smtp_from: str = "pothuluri33@gmail.com"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

settings = Settings()
