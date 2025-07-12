from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str
    redis_url: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    
    # AI Services
    openai_api_key: str
    anthropic_api_key: str
    deepseek_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # AI Cost Management
    openai_cost_limit_daily: float = 100.0
    anthropic_cost_limit_daily: float = 100.0
    ai_usage_alert_threshold: float = 80.0
    
    # Platform Integrations
    gohighlevel_client_id: Optional[str] = None
    gohighlevel_client_secret: Optional[str] = None
    gohighlevel_redirect_uri: Optional[str] = None
    
    simvoly_api_key: Optional[str] = None
    simvoly_api_secret: Optional[str] = None
    
    # Email Configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    
    # File Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # Payment Processing
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # Monitoring & Analytics
    sentry_dsn: Optional[str] = None
    datadog_api_key: Optional[str] = None
    
    # Development
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Feature Flags
    enable_platform_integrations: bool = True
    enable_ai_cost_tracking: bool = True
    enable_migration_tools: bool = True
    enable_beta_features: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# Database URL for SQLAlchemy
DATABASE_URL = settings.database_url
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# AI Service Configuration
AI_MODELS = {
    "claude": {
        "model": "claude-3-5-sonnet-20241022",
        "cost_per_input_token": 0.000003,
        "cost_per_output_token": 0.000015,
        "max_tokens": 8192
    },
    "gpt4": {
        "model": "gpt-4-turbo-preview", 
        "cost_per_input_token": 0.00001,
        "cost_per_output_token": 0.00003,
        "max_tokens": 4096
    },
    "gpt4v": {
        "model": "gpt-4-vision-preview",
        "cost_per_input_token": 0.00001,
        "cost_per_output_token": 0.00003,
        "cost_per_image": 0.00765,
        "max_tokens": 4096
    }
}

# Subscription Limits
SUBSCRIPTION_LIMITS = {
    "freemium": {
        "campaigns_per_month": 3,
        "ai_credits": 10,
        "storage_gb": 1,
        "team_members": 1
    },
    "creator": {
        "campaigns_per_month": 25,
        "ai_credits": 100,
        "storage_gb": 10,
        "team_members": 1
    },
    "business": {
        "campaigns_per_month": 100,
        "ai_credits": 500,
        "storage_gb": 50,
        "team_members": 10
    },
    "agency": {
        "campaigns_per_month": 500,
        "ai_credits": 2500,
        "storage_gb": 200,
        "team_members": -1  # unlimited
    }
}