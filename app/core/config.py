from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_URL_SYNC: str = Field(..., env="DATABASE_URL_SYNC")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # JWT
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(..., env="OPENAI_API_KEY")
    AI_MODEL: str = Field(default="gpt-3.5-turbo", env="AI_MODEL")
    AI_TEMPERATURE: float = Field(default=0.7, env="AI_TEMPERATURE")
    AI_MAX_TOKENS: int = Field(default=500, env="AI_MAX_TOKENS")
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = Field(..., env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(..., env="TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER: str = Field(..., env="TWILIO_PHONE_NUMBER")
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: str = Field(..., env="TELEGRAM_WEBHOOK_URL")
    
    # WhatsApp
    WHATSAPP_ACCESS_TOKEN: str = Field(..., env="WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(..., env="WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_VERIFY_TOKEN: str = Field(..., env="WHATSAPP_VERIFY_TOKEN")
    
    # Instagram
    INSTAGRAM_CLIENT_ID: str = Field(..., env="INSTAGRAM_CLIENT_ID")
    INSTAGRAM_CLIENT_SECRET: str = Field(..., env="INSTAGRAM_CLIENT_SECRET")
    INSTAGRAM_REDIRECT_URI: str = Field(..., env="INSTAGRAM_REDIRECT_URI")
    
    # Email
    SMTP_HOST: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: str = Field(..., env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    
    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING: str = Field(..., env="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_CONTAINER_NAME: str = Field(default="cake-crm-files", env="AZURE_CONTAINER_NAME")
    
    # Application
    APP_NAME: str = Field(default="Cake CRM", env="APP_NAME")
    APP_VERSION: str = Field(default="1.0.0", env="APP_VERSION")
    DEBUG: bool = Field(default=True, env="DEBUG")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # Business
    BUSINESS_NAME: str = Field(default="Your Cake Shop", env="BUSINESS_NAME")
    BUSINESS_PHONE: str = Field(..., env="BUSINESS_PHONE")
    BUSINESS_EMAIL: str = Field(..., env="BUSINESS_EMAIL")
    BUSINESS_ADDRESS: str = Field(..., env="BUSINESS_ADDRESS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings() 