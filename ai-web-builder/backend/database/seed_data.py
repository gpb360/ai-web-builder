"""
Seed data for development and testing
"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, AppSetting
from passlib.context import CryptContext
import json
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_seed_data(session: AsyncSession):
    """Create initial seed data for development"""
    
    # Create development user
    dev_user = User(
        email="dev@aiwebbuilder.com",
        password_hash=pwd_context.hash("devpassword123"),
        name="Development User",
        subscription_tier="agency",
        subscription_status="active",
        settings={
            "theme": "dark",
            "notifications": {
                "email_notifications": True,
                "campaign_updates": True,
                "billing_alerts": True,
                "feature_announcements": True
            },
            "ai_preferences": {
                "preferred_style": "modern",
                "animation_level": "smooth",
                "responsiveness_priority": "mobile",
                "accessibility_mode": True
            },
            "brand_settings": {
                "primary_color": "#3B82F6",
                "secondary_color": "#10B981",
                "accent_color": "#F59E0B",
                "font_family": "Inter"
            }
        }
    )
    session.add(dev_user)
    
    # Create test user
    test_user = User(
        email="test@example.com",
        password_hash=pwd_context.hash("testpassword123"),
        name="Test User",
        subscription_tier="creator",
        subscription_status="active",
        settings={
            "theme": "light",
            "notifications": {
                "email_notifications": False,
                "campaign_updates": True,
                "billing_alerts": True,
                "feature_announcements": False
            },
            "ai_preferences": {
                "preferred_style": "minimal",
                "animation_level": "subtle",
                "responsiveness_priority": "balanced",
                "accessibility_mode": False
            }
        }
    )
    session.add(test_user)
    
    # Create app settings
    app_settings = [
        AppSetting(
            key="ai_model_config",
            value={
                "default_model": "claude",
                "fallback_model": "gpt4",
                "cost_optimization": True,
                "quality_threshold": 0.8
            },
            description="AI model configuration and preferences"
        ),
        AppSetting(
            key="subscription_limits",
            value={
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
                    "team_members": -1
                }
            },
            description="Subscription tier limits and quotas"
        ),
        AppSetting(
            key="feature_flags",
            value={
                "enable_platform_integrations": True,
                "enable_ai_cost_tracking": True,
                "enable_migration_tools": True,
                "enable_beta_features": True,
                "enable_component_marketplace": False,
                "enable_team_collaboration": True
            },
            description="Feature flags for controlling platform functionality"
        ),
        AppSetting(
            key="ai_cost_limits",
            value={
                "daily_limit_per_user": {
                    "freemium": 5.0,
                    "creator": 15.0,
                    "business": 50.0,
                    "agency": 200.0
                },
                "alert_thresholds": {
                    "warning": 0.8,
                    "critical": 0.95
                },
                "emergency_shutdown": True
            },
            description="AI cost management and safety limits"
        ),
        AppSetting(
            key="platform_integrations",
            value={
                "gohighlevel": {
                    "enabled": True,
                    "api_version": "v1",
                    "rate_limit": 100,
                    "supported_features": ["funnel_import", "contact_sync", "automation_export"]
                },
                "simvoly": {
                    "enabled": True,
                    "api_version": "v2",
                    "rate_limit": 50,
                    "supported_features": ["site_import", "page_analysis", "component_export"]
                },
                "wordpress": {
                    "enabled": True,
                    "api_version": "wp/v2",
                    "rate_limit": 200,
                    "supported_features": ["theme_analysis", "plugin_detection", "content_migration"]
                }
            },
            description="Platform integration configurations and capabilities"
        )
    ]
    
    for setting in app_settings:
        session.add(setting)
    
    await session.commit()
    print("✅ Seed data created successfully!")

async def clear_seed_data(session: AsyncSession):
    """Clear all seed data (useful for testing)"""
    
    # Delete users (cascade will handle related records)
    await session.execute("DELETE FROM users WHERE email IN ('dev@aiwebbuilder.com', 'test@example.com')")
    
    # Delete app settings
    await session.execute("DELETE FROM app_settings")
    
    await session.commit()
    print("✅ Seed data cleared successfully!")