from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, 
    ForeignKey, DECIMAL, ARRAY, CheckConstraint, UniqueConstraint,
    Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    avatar_url = Column(Text)
    subscription_tier = Column(
        String(20), 
        nullable=False, 
        default='freemium',
        index=True
    )
    subscription_status = Column(String(20), nullable=False, default='active')
    subscription_ends_at = Column(DateTime(timezone=True))
    settings = Column(JSONB, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    last_active_at = Column(DateTime(timezone=True), default=func.now())
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    
    # Relationships
    campaigns = relationship("Campaign", back_populates="user", cascade="all, delete-orphan")
    platform_integrations = relationship("PlatformIntegration", back_populates="user", cascade="all, delete-orphan")
    ai_usage = relationship("AIUsage", back_populates="user", cascade="all, delete-orphan")
    ai_generations = relationship("AIGeneration", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UserUsage", back_populates="user", cascade="all, delete-orphan")
    component_library = relationship("ComponentLibraryItem", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            subscription_tier.in_(['freemium', 'creator', 'business', 'agency']),
            name='check_subscription_tier'
        ),
        CheckConstraint(
            subscription_status.in_(['active', 'canceled', 'past_due', 'trial']),
            name='check_subscription_status'
        ),
    )

class UserUsage(Base):
    __tablename__ = "user_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month = Column(DateTime(timezone=True), nullable=False)  # First day of month
    campaigns_generated = Column(Integer, nullable=False, default=0)
    ai_credits_used = Column(Integer, nullable=False, default=0)
    storage_bytes_used = Column(Integer, nullable=False, default=0)
    api_calls_made = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_records")
    
    __table_args__ = (
        UniqueConstraint("user_id", "month", name="uq_user_usage_month"),
        Index("idx_user_usage_user_month", "user_id", "month"),
    )

class PlatformIntegration(Base):
    __tablename__ = "platform_integrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform_type = Column(String(50), nullable=False, index=True)
    connection_status = Column(String(20), nullable=False, default='pending')
    account_name = Column(String(255))
    account_email = Column(String(255))
    encrypted_credentials = Column(Text)
    platform_metadata = Column(JSONB, nullable=False, default={})
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(String(20), default='idle')
    sync_error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="platform_integrations")
    analyses = relationship("PlatformAnalysis", back_populates="integration", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("user_id", "platform_type", name="uq_user_platform"),
        CheckConstraint(
            platform_type.in_(['gohighlevel', 'simvoly', 'wordpress', 'custom']),
            name='check_platform_type'
        ),
        CheckConstraint(
            connection_status.in_(['connected', 'disconnected', 'error', 'pending']),
            name='check_connection_status'
        ),
        CheckConstraint(
            sync_status.in_(['idle', 'syncing', 'error', 'completed']),
            name='check_sync_status'
        ),
    )

class PlatformAnalysis(Base):
    __tablename__ = "platform_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("platform_integrations.id", ondelete="CASCADE"), nullable=False)
    analysis_type = Column(String(50), nullable=False, default='full_audit')
    summary = Column(JSONB, nullable=False, default={})
    campaigns_analyzed = Column(JSONB, nullable=False, default=[])
    recommendations = Column(JSONB, nullable=False, default=[])
    migration_assessment = Column(JSONB)
    ai_model_used = Column(String(100))
    ai_cost = Column(DECIMAL(10, 4))
    processing_time_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    integration = relationship("PlatformIntegration", back_populates="analyses")
    
    __table_args__ = (
        CheckConstraint(
            analysis_type.in_(['full_audit', 'campaign_analysis', 'migration_assessment']),
            name='check_analysis_type'
        ),
    )

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, default='draft', index=True)
    type = Column(String(30), nullable=False, default='complete_campaign')
    platform_source = Column(String(50))
    platform_source_id = Column(String(255))
    target_audience = Column(Text)
    business_type = Column(String(100))
    goals = Column(JSONB, nullable=False, default=[])
    brand_guidelines = Column(Text)
    performance_requirements = Column(JSONB, nullable=False, default={})
    views = Column(Integer, nullable=False, default=0)
    conversions = Column(Integer, nullable=False, default=0)
    revenue_generated = Column(DECIMAL(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    launched_at = Column(DateTime(timezone=True))
    
    # Full-text search
    search_vector = Column(Text)  # tsvector in actual DB
    
    # Relationships
    user = relationship("User", back_populates="campaigns")
    components = relationship("CampaignComponent", back_populates="campaign", cascade="all, delete-orphan")
    ai_generations = relationship("AIGeneration", back_populates="campaign")
    events = relationship("CampaignEvent", back_populates="campaign", cascade="all, delete-orphan")
    conversions = relationship("Conversion", back_populates="campaign", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint(
            status.in_(['draft', 'generating', 'ready', 'launched', 'paused', 'archived']),
            name='check_campaign_status'
        ),
        CheckConstraint(
            type.in_(['landing_page', 'funnel', 'email_sequence', 'complete_campaign', 'component_enhancement']),
            name='check_campaign_type'
        ),
        CheckConstraint(
            platform_source.in_(['gohighlevel', 'simvoly', 'wordpress', 'custom']),
            name='check_platform_source'
        ),
    )

class CampaignComponent(Base):
    __tablename__ = "campaign_components"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    component_type = Column(String(50), nullable=False, index=True)
    code = Column(Text, nullable=False)
    props = Column(JSONB, nullable=False, default={})
    css_styles = Column(Text)
    preview_url = Column(Text)
    export_formats = Column(JSONB, nullable=False, default=[])
    views = Column(Integer, nullable=False, default=0)
    clicks = Column(Integer, nullable=False, default=0)
    conversions = Column(Integer, nullable=False, default=0)
    engagement_score = Column(DECIMAL(5, 2), nullable=False, default=0)
    ai_generation_metadata = Column(JSONB, nullable=False, default={})
    version = Column(Integer, nullable=False, default=1)
    parent_component_id = Column(UUID(as_uuid=True), ForeignKey("campaign_components.id"))
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="components")
    parent_component = relationship("CampaignComponent", remote_side=[id])
    ai_generations = relationship("AIGeneration", back_populates="component")
    events = relationship("CampaignEvent", back_populates="component")
    conversions = relationship("Conversion", back_populates="component")
    
    __table_args__ = (
        CheckConstraint(
            component_type.in_(['landing_page', 'form', 'header', 'footer', 'hero_section', 
                               'testimonials', 'pricing', 'email_template', 'popup', 'navigation', 'custom']),
            name='check_component_type'
        ),
        Index("idx_components_sort_order", "campaign_id", "sort_order"),
    )

class AIGeneration(Base):
    __tablename__ = "ai_generations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="SET NULL"))
    component_id = Column(UUID(as_uuid=True), ForeignKey("campaign_components.id", ondelete="SET NULL"))
    generation_type = Column(String(50), nullable=False)
    prompt_text = Column(Text, nullable=False)
    reference_images = Column(ARRAY(Text))
    model_used = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    cost = Column(DECIMAL(8, 4), nullable=False, default=0, index=True)
    status = Column(String(20), nullable=False, default='processing')
    result_data = Column(JSONB)
    error_message = Column(Text)
    generation_time_seconds = Column(Integer)
    iterations = Column(Integer, nullable=False, default=1)
    user_rating = Column(Integer)
    user_feedback = Column(Text)
    accepted = Column(Boolean)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="ai_generations")
    campaign = relationship("Campaign", back_populates="ai_generations")
    component = relationship("CampaignComponent", back_populates="ai_generations")
    
    __table_args__ = (
        CheckConstraint(
            generation_type.in_(['campaign', 'component', 'enhancement', 'analysis', 'migration_plan']),
            name='check_generation_type'
        ),
        CheckConstraint(
            status.in_(['processing', 'completed', 'failed', 'cancelled']),
            name='check_generation_status'
        ),
        CheckConstraint(
            user_rating >= 1,
            name='check_user_rating_min'
        ),
        CheckConstraint(
            user_rating <= 5,
            name='check_user_rating_max'
        ),
    )

class AICostTracking(Base):
    __tablename__ = "ai_cost_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    openai_cost = Column(DECIMAL(8, 4), nullable=False, default=0)
    anthropic_cost = Column(DECIMAL(8, 4), nullable=False, default=0)
    total_cost = Column(DECIMAL(8, 4), nullable=False, default=0)
    generations_count = Column(Integer, nullable=False, default=0)
    tokens_used = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_cost_date"),
        Index("idx_ai_cost_tracking_user_date", "user_id", "date"),
    )

class ComponentLibraryItem(Base):
    __tablename__ = "component_library"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    tags = Column(ARRAY(Text), nullable=False, default=[])
    component_type = Column(String(50), nullable=False)
    code = Column(Text, nullable=False)
    props_schema = Column(JSONB, nullable=False, default={})
    preview_image_url = Column(Text)
    is_public = Column(Boolean, nullable=False, default=False, index=True)
    is_marketplace_item = Column(Boolean, nullable=False, default=False, index=True)
    price = Column(DECIMAL(8, 2))
    downloads = Column(Integer, nullable=False, default=0)
    likes = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Full-text search
    search_vector = Column(Text)  # tsvector in actual DB
    
    # Relationships
    user = relationship("User", back_populates="component_library")

class CampaignEvent(Base):
    __tablename__ = "campaign_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id = Column(UUID(as_uuid=True), ForeignKey("campaign_components.id", ondelete="SET NULL"))
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=False, default={})
    session_id = Column(String(255))
    user_agent = Column(Text)
    ip_address = Column(INET)
    referrer = Column(Text)
    country = Column(String(2))
    region = Column(String(100))
    city = Column(String(100))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Relationships
    campaign = relationship("Campaign", back_populates="events")
    component = relationship("CampaignComponent", back_populates="events")
    
    __table_args__ = (
        CheckConstraint(
            event_type.in_(['view', 'click', 'conversion', 'form_submit', 'email_open', 'email_click']),
            name='check_event_type'
        ),
    )

class Conversion(Base):
    __tablename__ = "conversions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    component_id = Column(UUID(as_uuid=True), ForeignKey("campaign_components.id", ondelete="SET NULL"))
    conversion_type = Column(String(50), nullable=False)
    value = Column(DECIMAL(12, 2))
    currency = Column(String(3), default='USD')
    session_id = Column(String(255))
    source = Column(String(100))
    medium = Column(String(100))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    campaign = relationship("Campaign", back_populates="conversions")
    component = relationship("CampaignComponent", back_populates="conversions")

class AppSetting(Base):
    __tablename__ = "app_settings"
    
    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class JobQueue(Base):
    __tablename__ = "job_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(100), nullable=False)
    payload = Column(JSONB, nullable=False, default={})
    status = Column(String(20), nullable=False, default='pending')
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error_message = Column(Text)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        CheckConstraint(
            status.in_(['pending', 'processing', 'completed', 'failed', 'retrying']),
            name='check_job_status'
        ),
    )

class AIUsage(Base):
    __tablename__ = "ai_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    model_used = Column(String(50), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost = Column(Numeric(10, 6), nullable=False, default=0)
    processing_time = Column(Float)  # Processing time in seconds
    quality_score = Column(Float)  # AI output quality score (0-1)
    user_tier = Column(String(50), nullable=False, index=True)
    metadata = Column(JSONB, nullable=False, default={})  # Additional tracking data
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="ai_usage")
    
    __table_args__ = (
        CheckConstraint(
            model_used.in_(['deepseek-v3', 'gemini-1.5-flash', 'gemini-1.5-pro', 'claude-3.5-sonnet', 'gpt-4-turbo', 'gpt-4-vision']),
            name='check_ai_model'
        ),
        CheckConstraint(
            task_type.in_(['code_generation', 'content_writing', 'analysis', 'optimization', 'translation', 'summarization', 'component_generation', 'campaign_analysis', 'design_review']),
            name='check_task_type'
        ),
        CheckConstraint(
            user_tier.in_(['free', 'creator', 'business', 'agency']),
            name='check_user_tier'
        ),
        CheckConstraint(cost >= 0, name='check_positive_cost'),
        CheckConstraint(input_tokens >= 0, name='check_positive_input_tokens'),
        CheckConstraint(output_tokens >= 0, name='check_positive_output_tokens'),
        Index('idx_ai_usage_user_created', 'user_id', 'created_at'),
        Index('idx_ai_usage_model_task', 'model_used', 'task_type'),
    )