import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    WEBHOOK_SECRET_TOKEN: str = os.getenv("WEBHOOK_SECRET_TOKEN", "")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./webhook_service.db")
    
    # Security settings
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 30))
    MAX_REQUEST_SIZE: int = int(os.getenv("MAX_REQUEST_SIZE", 1024 * 1024))  # 1MB
    
    # Rate limiting
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", 100))  # requests per minute
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", 60))  # seconds
    
    @classmethod
    def validate(cls) -> tuple[bool, list[str]]:
        """Validate configuration and return (is_valid, error_messages)"""
        errors = []
        
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
            
        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append("PORT must be between 1 and 65535")
            
        return len(errors) == 0, errors

# Create config instance
config = Config()