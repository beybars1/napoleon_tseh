from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # GreenAPI
    GREEN_API_ID_INSTANCE: str
    GREEN_API_TOKEN: str
    
    # Chat IDs
    MAIN_GROUP_CHAT_ID: Optional[str] = None
    OPERATIONAL_GROUP_CHAT_ID: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # App Settings
    MESSAGE_CHECK_INTERVAL: int = 30  # seconds
    DAILY_ORDERS_HOUR: int = 8  # 8 AM
    MAX_MESSAGES_PER_REQUEST: int = 1000
    TESTING_MODE: bool = False  # Added testing mode flag
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # Allow case-insensitive env vars

settings = Settings()