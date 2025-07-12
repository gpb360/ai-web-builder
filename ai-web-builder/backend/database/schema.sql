-- AI Web Builder Database Schema
-- PostgreSQL 15+ with UUID and JSON support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For GIN indexes

-- ============================================================================
-- CORE USER MANAGEMENT
-- ============================================================================

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    subscription_tier VARCHAR(20) NOT NULL DEFAULT 'freemium' 
        CHECK (subscription_tier IN ('freemium', 'creator', 'business', 'agency')),
    subscription_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (subscription_status IN ('active', 'canceled', 'past_due', 'trial')),
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    settings JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Usage tracking for subscription limits
CREATE TABLE user_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    month DATE NOT NULL, -- First day of the month
    campaigns_generated INTEGER NOT NULL DEFAULT 0,
    ai_credits_used INTEGER NOT NULL DEFAULT 0,
    storage_bytes_used BIGINT NOT NULL DEFAULT 0,
    api_calls_made INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, month)
);

-- ============================================================================
-- PLATFORM INTEGRATIONS
-- ============================================================================

-- Platform connections (GoHighLevel, Simvoly, WordPress, etc.)
CREATE TABLE platform_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform_type VARCHAR(50) NOT NULL 
        CHECK (platform_type IN ('gohighlevel', 'simvoly', 'wordpress', 'custom')),
    connection_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (connection_status IN ('connected', 'disconnected', 'error', 'pending')),
    account_name VARCHAR(255),
    account_email VARCHAR(255),
    
    -- Encrypted credentials (use application-level encryption)
    encrypted_credentials TEXT,
    
    -- Platform-specific metadata
    platform_metadata JSONB NOT NULL DEFAULT '{}',
    
    -- Sync information
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(20) DEFAULT 'idle'
        CHECK (sync_status IN ('idle', 'syncing', 'error', 'completed')),
    sync_error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- One integration per platform per user
    UNIQUE(user_id, platform_type)
);

-- Platform analysis results
CREATE TABLE platform_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES platform_integrations(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL DEFAULT 'full_audit'
        CHECK (analysis_type IN ('full_audit', 'campaign_analysis', 'migration_assessment')),
    
    -- Analysis results
    summary JSONB NOT NULL DEFAULT '{}',
    campaigns_analyzed JSONB NOT NULL DEFAULT '[]',
    recommendations JSONB NOT NULL DEFAULT '[]',
    migration_assessment JSONB,
    
    -- AI metadata
    ai_model_used VARCHAR(100),
    ai_cost DECIMAL(10, 4),
    processing_time_seconds INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- CAMPAIGNS AND COMPONENTS
-- ============================================================================

-- Campaigns (main container for marketing projects)
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Campaign status and type
    status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'generating', 'ready', 'launched', 'paused', 'archived')),
    type VARCHAR(30) NOT NULL DEFAULT 'complete_campaign'
        CHECK (type IN ('landing_page', 'funnel', 'email_sequence', 'complete_campaign', 'component_enhancement')),
    
    -- Source platform for enhancements
    platform_source VARCHAR(50) 
        CHECK (platform_source IN ('gohighlevel', 'simvoly', 'wordpress', 'custom')),
    platform_source_id VARCHAR(255), -- Original platform's ID
    
    -- Campaign settings and requirements
    target_audience TEXT,
    business_type VARCHAR(100),
    goals JSONB NOT NULL DEFAULT '[]',
    brand_guidelines TEXT,
    performance_requirements JSONB NOT NULL DEFAULT '{}',
    
    -- Analytics
    views INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    revenue_generated DECIMAL(12, 2) NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    launched_at TIMESTAMP WITH TIME ZONE,
    
    -- Search index for campaign content
    search_vector tsvector
);

-- Campaign components (individual UI elements)
CREATE TABLE campaign_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    component_type VARCHAR(50) NOT NULL
        CHECK (component_type IN ('landing_page', 'form', 'header', 'footer', 'hero_section', 
                                  'testimonials', 'pricing', 'email_template', 'popup', 'navigation', 'custom')),
    
    -- Component code and properties
    code TEXT NOT NULL,
    props JSONB NOT NULL DEFAULT '{}',
    css_styles TEXT,
    
    -- Preview and export
    preview_url TEXT,
    export_formats JSONB NOT NULL DEFAULT '[]', -- ['react', 'html_css', 'gohighlevel']
    
    -- Component analytics
    views INTEGER NOT NULL DEFAULT 0,
    clicks INTEGER NOT NULL DEFAULT 0,
    conversions INTEGER NOT NULL DEFAULT 0,
    engagement_score DECIMAL(5, 2) NOT NULL DEFAULT 0,
    
    -- AI generation metadata
    ai_generation_metadata JSONB NOT NULL DEFAULT '{}',
    
    -- Versioning
    version INTEGER NOT NULL DEFAULT 1,
    parent_component_id UUID REFERENCES campaign_components(id),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Order within campaign
    sort_order INTEGER NOT NULL DEFAULT 0
);

-- ============================================================================
-- AI USAGE AND COST TRACKING
-- ============================================================================

-- AI generation requests and costs
CREATE TABLE ai_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    component_id UUID REFERENCES campaign_components(id) ON DELETE SET NULL,
    
    -- Request details
    generation_type VARCHAR(50) NOT NULL
        CHECK (generation_type IN ('campaign', 'component', 'enhancement', 'analysis', 'migration_plan')),
    prompt_text TEXT NOT NULL,
    reference_images TEXT[], -- Array of image URLs
    
    -- AI model information
    model_used VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    cost DECIMAL(8, 4) NOT NULL DEFAULT 0,
    
    -- Generation results
    status VARCHAR(20) NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'completed', 'failed', 'cancelled')),
    result_data JSONB,
    error_message TEXT,
    
    -- Performance metrics
    generation_time_seconds INTEGER,
    iterations INTEGER NOT NULL DEFAULT 1,
    
    -- User feedback
    user_rating INTEGER CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback TEXT,
    accepted BOOLEAN DEFAULT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Daily AI cost tracking
CREATE TABLE ai_cost_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    
    -- Cost breakdown by model
    openai_cost DECIMAL(8, 4) NOT NULL DEFAULT 0,
    anthropic_cost DECIMAL(8, 4) NOT NULL DEFAULT 0,
    total_cost DECIMAL(8, 4) NOT NULL DEFAULT 0,
    
    -- Usage counts
    generations_count INTEGER NOT NULL DEFAULT 0,
    tokens_used INTEGER NOT NULL DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(user_id, date)
);

-- ============================================================================
-- COMPONENT LIBRARY AND MARKETPLACE
-- ============================================================================

-- User's component library
CREATE TABLE component_library (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    tags TEXT[] NOT NULL DEFAULT '{}',
    
    -- Component definition
    component_type VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    props_schema JSONB NOT NULL DEFAULT '{}',
    preview_image_url TEXT,
    
    -- Sharing and marketplace
    is_public BOOLEAN NOT NULL DEFAULT FALSE,
    is_marketplace_item BOOLEAN NOT NULL DEFAULT FALSE,
    price DECIMAL(8, 2), -- For marketplace items
    
    -- Usage statistics
    downloads INTEGER NOT NULL DEFAULT 0,
    likes INTEGER NOT NULL DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Search index
    search_vector tsvector
);

-- ============================================================================
-- ANALYTICS AND TRACKING
-- ============================================================================

-- Campaign performance events
CREATE TABLE campaign_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    component_id UUID REFERENCES campaign_components(id) ON DELETE SET NULL,
    
    -- Event details
    event_type VARCHAR(50) NOT NULL
        CHECK (event_type IN ('view', 'click', 'conversion', 'form_submit', 'email_open', 'email_click')),
    event_data JSONB NOT NULL DEFAULT '{}',
    
    -- User information (anonymous tracking)
    session_id VARCHAR(255),
    user_agent TEXT,
    ip_address INET,
    referrer TEXT,
    
    -- Geographic data
    country VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Conversion tracking
CREATE TABLE conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    component_id UUID REFERENCES campaign_components(id) ON DELETE SET NULL,
    
    -- Conversion details
    conversion_type VARCHAR(50) NOT NULL,
    value DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Attribution
    session_id VARCHAR(255),
    source VARCHAR(100),
    medium VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- SYSTEM TABLES
-- ============================================================================

-- Application settings and feature flags
CREATE TABLE app_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Background job queue
CREATE TABLE job_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'retrying')),
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- User indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = true;

-- Campaign indexes
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX idx_campaigns_search ON campaigns USING GIN(search_vector);

-- Component indexes
CREATE INDEX idx_components_campaign_id ON campaign_components(campaign_id);
CREATE INDEX idx_components_type ON campaign_components(component_type);
CREATE INDEX idx_components_sort_order ON campaign_components(campaign_id, sort_order);

-- AI generation indexes
CREATE INDEX idx_ai_generations_user_id ON ai_generations(user_id);
CREATE INDEX idx_ai_generations_created_at ON ai_generations(created_at DESC);
CREATE INDEX idx_ai_generations_cost ON ai_generations(cost DESC);

-- Analytics indexes
CREATE INDEX idx_campaign_events_campaign_id ON campaign_events(campaign_id);
CREATE INDEX idx_campaign_events_created_at ON campaign_events(created_at DESC);
CREATE INDEX idx_campaign_events_type ON campaign_events(event_type);

-- Platform integration indexes
CREATE INDEX idx_platform_integrations_user_id ON platform_integrations(user_id);
CREATE INDEX idx_platform_integrations_type ON platform_integrations(platform_type);

-- Usage tracking indexes
CREATE INDEX idx_user_usage_user_month ON user_usage(user_id, month);
CREATE INDEX idx_ai_cost_tracking_user_date ON ai_cost_tracking(user_id, date);

-- Component library indexes
CREATE INDEX idx_component_library_user_id ON component_library(user_id);
CREATE INDEX idx_component_library_public ON component_library(is_public) WHERE is_public = true;
CREATE INDEX idx_component_library_marketplace ON component_library(is_marketplace_item) WHERE is_marketplace_item = true;
CREATE INDEX idx_component_library_search ON component_library USING GIN(search_vector);

-- ============================================================================
-- TRIGGERS FOR AUTO-UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_components_updated_at BEFORE UPDATE ON campaign_components
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_platform_integrations_updated_at BEFORE UPDATE ON platform_integrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_component_library_updated_at BEFORE UPDATE ON component_library
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_usage_updated_at BEFORE UPDATE ON user_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update search vectors
CREATE OR REPLACE FUNCTION update_campaign_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.target_audience, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(NEW.business_type, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_campaigns_search_vector BEFORE INSERT OR UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_campaign_search_vector();

-- Component library search vector
CREATE OR REPLACE FUNCTION update_component_library_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.category, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_component_library_search_vector BEFORE INSERT OR UPDATE ON component_library
    FOR EACH ROW EXECUTE FUNCTION update_component_library_search_vector();