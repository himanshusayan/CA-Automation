from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database Configuration
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1234"
    MYSQL_DATABASE: str = "ca_email_system"
    
    # Gmail API Configuration
    GMAIL_CREDENTIALS_PATH: str = "credentials.json"
    GMAIL_TOKEN_PATH: str = "token.json"
    
    # Perplexity AI Configuration
    PERPLEXITY_API_KEY: str
    
    # Application Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DEBUG: bool = False
    
    # Email Processing Configuration
    EMAIL_FETCH_INTERVAL: int = 10
    MAX_EMAILS_PER_FETCH: int = 50
    MAX_RETRY_ATTEMPTS: int = 3
    
    # File Storage Configuration
    STORAGE_BASE_PATH: str
    GST_ROOT_FOLDER: str = "Gmail_Automation"
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_SIZE: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    
    class Config:
        env_file = ".env"

settings = Settings()
