# Database Schema Documentation

## Overview

The AI Web Builder platform uses PostgreSQL 15+ as the primary database with the following key features:
- **UUID primary keys** for all entities
- **JSONB columns** for flexible metadata storage
- **Full-text search** capabilities for campaigns and components
- **Comprehensive indexing** for performance
- **Automatic timestamps** with triggers
- **Cost tracking** for AI usage monitoring

## Core Tables

### Users & Authentication

#### `users`
Main user account table with subscription management.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `email` | VARCHAR(255) | Unique email address |
| `password_hash` | VARCHAR(255) | Bcrypt hashed password |
| `name` | VARCHAR(255) | User's full name |
| `avatar_url` | TEXT | Profile picture URL |
| `subscription_tier` | VARCHAR(20) | freemium, creator, business, agency |
| `subscription_status` | VARCHAR(20) | active, canceled, past_due, trial |
| `subscription_ends_at` | TIMESTAMPTZ | Subscription expiry |
| `settings` | JSONB | User preferences and configuration |
| `created_at` | TIMESTAMPTZ | Account creation time |
| `updated_at` | TIMESTAMPTZ | Last profile update |
| `last_active_at` | TIMESTAMPTZ | Last login/activity |
| `is_active` | BOOLEAN | Account status |

**Indexes:**
- `idx_users_email` - Email lookup
- `idx_users_subscription_tier` - Subscription filtering
- `idx_users_active` - Active users only

#### `user_usage`
Monthly usage tracking for subscription limits.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | References users.id |
| `month` | DATE | First day of month |
| `campaigns_generated` | INTEGER | Campaigns created this month |
| `ai_credits_used` | INTEGER | AI generation credits consumed |
| `storage_bytes_used` | BIGINT | Storage space used |
| `api_calls_made` | INTEGER | API calls made |

**Constraints:**
- Unique constraint on (user_id, month)

### Platform Integrations

#### `platform_integrations`
Connections to external platforms (GoHighLevel, Simvoly, WordPress).

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | References users.id |
| `platform_type` | VARCHAR(50) | gohighlevel, simvoly, wordpress, custom |
| `connection_status` | VARCHAR(20) | connected, disconnected, error, pending |
| `account_name` | VARCHAR(255) | Platform account name |
| `account_email` | VARCHAR(255) | Platform account email |
| `encrypted_credentials` | TEXT | Encrypted API keys/tokens |
| `platform_metadata` | JSONB | Platform-specific data |
| `last_sync_at` | TIMESTAMPTZ | Last successful sync |
| `sync_status` | VARCHAR(20) | idle, syncing, error, completed |
| `sync_error_message` | TEXT | Error details |

**Constraints:**
- Unique constraint on (user_id, platform_type)

#### `platform_analyses`
AI analysis results for external platform content.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `integration_id` | UUID | References platform_integrations.id |
| `analysis_type` | VARCHAR(50) | full_audit, campaign_analysis, migration_assessment |
| `summary` | JSONB | Analysis summary |
| `campaigns_analyzed` | JSONB | Array of analyzed campaigns |
| `recommendations` | JSONB | Array of improvement suggestions |
| `migration_assessment` | JSONB | Migration complexity and plan |
| `ai_model_used` | VARCHAR(100) | AI model for analysis |
| `ai_cost` | DECIMAL(10,4) | Cost of AI analysis |
| `processing_time_seconds` | INTEGER | Time taken |

### Campaigns & Components

#### `campaigns`
Main marketing campaign container.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | References users.id |
| `name` | VARCHAR(255) | Campaign name |
| `description` | TEXT | Campaign description |
| `status` | VARCHAR(20) | draft, generating, ready, launched, paused, archived |
| `type` | VARCHAR(30) | landing_page, funnel, email_sequence, complete_campaign, component_enhancement |
| `platform_source` | VARCHAR(50) | Source platform for enhancements |
| `platform_source_id` | VARCHAR(255) | Original platform ID |
| `target_audience` | TEXT | Target audience description |
| `business_type` | VARCHAR(100) | Business category |
| `goals` | JSONB | Array of campaign goals |
| `brand_guidelines` | TEXT | Brand guidelines text |
| `performance_requirements` | JSONB | Performance criteria |
| `views` | INTEGER | Total campaign views |
| `conversions` | INTEGER | Total conversions |
| `revenue_generated` | DECIMAL(12,2) | Revenue attributed |
| `launched_at` | TIMESTAMPTZ | Launch time |
| `search_vector` | TSVECTOR | Full-text search index |

**Indexes:**
- `idx_campaigns_user_id` - User's campaigns
- `idx_campaigns_status` - Status filtering
- `idx_campaigns_created_at` - Chronological ordering
- `idx_campaigns_search` - Full-text search

#### `campaign_components`
Individual UI components within campaigns.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `campaign_id` | UUID | References campaigns.id |
| `name` | VARCHAR(255) | Component name |
| `component_type` | VARCHAR(50) | landing_page, form, header, footer, hero_section, testimonials, pricing, email_template, popup, navigation, custom |
| `code` | TEXT | Generated component code |
| `props` | JSONB | Component properties |
| `css_styles` | TEXT | Additional CSS |
| `preview_url` | TEXT | Preview image/URL |
| `export_formats` | JSONB | Available export formats |
| `views` | INTEGER | Component views |
| `clicks` | INTEGER | Component clicks |
| `conversions` | INTEGER | Component conversions |
| `engagement_score` | DECIMAL(5,2) | Engagement metric |
| `ai_generation_metadata` | JSONB | AI generation details |
| `version` | INTEGER | Component version |
| `parent_component_id` | UUID | Parent component reference |
| `sort_order` | INTEGER | Order within campaign |

**Indexes:**
- `idx_components_campaign_id` - Campaign's components
- `idx_components_type` - Component type filtering
- `idx_components_sort_order` - Ordering within campaigns

### AI Usage & Cost Tracking

#### `ai_generations`
Individual AI generation requests and results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | References users.id |
| `campaign_id` | UUID | References campaigns.id (nullable) |
| `component_id` | UUID | References campaign_components.id (nullable) |
| `generation_type` | VARCHAR(50) | campaign, component, enhancement, analysis, migration_plan |
| `prompt_text` | TEXT | User's prompt |
| `reference_images` | TEXT[] | Array of image URLs |
| `model_used` | VARCHAR(100) | AI model name |
| `prompt_tokens` | INTEGER | Input tokens |
| `completion_tokens` | INTEGER | Output tokens |
| `cost` | DECIMAL(8,4) | Generation cost |
| `status` | VARCHAR(20) | processing, completed, failed, cancelled |
| `result_data` | JSONB | Generated content |
| `error_message` | TEXT | Error details |
| `generation_time_seconds` | INTEGER | Processing time |
| `iterations` | INTEGER | Number of iterations |
| `user_rating` | INTEGER | User rating (1-5) |
| `user_feedback` | TEXT | User feedback |
| `accepted` | BOOLEAN | User acceptance |
| `completed_at` | TIMESTAMPTZ | Completion time |

**Indexes:**
- `idx_ai_generations_user_id` - User's generations
- `idx_ai_generations_created_at` - Chronological ordering
- `idx_ai_generations_cost` - Cost analysis

#### `ai_cost_tracking`
Daily cost aggregation per user.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | References users.id |
| `date` | DATE | Tracking date |
| `openai_cost` | DECIMAL(8,4) | OpenAI costs |
| `anthropic_cost` | DECIMAL(8,4) | Anthropic costs |
| `total_cost` | DECIMAL(8,4) | Total daily cost |
| `generations_count` | INTEGER | Number of generations |
| `tokens_used` | INTEGER | Total tokens |

**Constraints:**
- Unique constraint on (user_id, date)

### Component Library & Marketplace

#### `component_library`
User's saved and shareable components.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID | References users.id |
| `name` | VARCHAR(255) | Component name |
| `description` | TEXT | Component description |
| `category` | VARCHAR(100) | Component category |
| `tags` | TEXT[] | Search tags |
| `component_type` | VARCHAR(50) | Component type |
| `code` | TEXT | Component code |
| `props_schema` | JSONB | Props definition |
| `preview_image_url` | TEXT | Preview image |
| `is_public` | BOOLEAN | Public visibility |
| `is_marketplace_item` | BOOLEAN | Marketplace availability |
| `price` | DECIMAL(8,2) | Marketplace price |
| `downloads` | INTEGER | Download count |
| `likes` | INTEGER | Like count |
| `search_vector` | TSVECTOR | Full-text search |

**Indexes:**
- `idx_component_library_user_id` - User's components
- `idx_component_library_public` - Public components
- `idx_component_library_marketplace` - Marketplace items
- `idx_component_library_search` - Full-text search

### Analytics & Tracking

#### `campaign_events`
Detailed event tracking for campaigns.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `campaign_id` | UUID | References campaigns.id |
| `component_id` | UUID | References campaign_components.id (nullable) |
| `event_type` | VARCHAR(50) | view, click, conversion, form_submit, email_open, email_click |
| `event_data` | JSONB | Event-specific data |
| `session_id` | VARCHAR(255) | User session |
| `user_agent` | TEXT | Browser information |
| `ip_address` | INET | User IP |
| `referrer` | TEXT | Referring URL |
| `country` | VARCHAR(2) | Country code |
| `region` | VARCHAR(100) | Region name |
| `city` | VARCHAR(100) | City name |

**Indexes:**
- `idx_campaign_events_campaign_id` - Campaign events
- `idx_campaign_events_created_at` - Time-based queries
- `idx_campaign_events_type` - Event type filtering

#### `conversions`
Conversion tracking with attribution.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `campaign_id` | UUID | References campaigns.id |
| `component_id` | UUID | References campaign_components.id (nullable) |
| `conversion_type` | VARCHAR(50) | Conversion category |
| `value` | DECIMAL(12,2) | Conversion value |
| `currency` | VARCHAR(3) | Currency code |
| `session_id` | VARCHAR(255) | User session |
| `source` | VARCHAR(100) | Traffic source |
| `medium` | VARCHAR(100) | Traffic medium |

### System Tables

#### `app_settings`
Application configuration and feature flags.

| Column | Type | Description |
|--------|------|-------------|
| `key` | VARCHAR(100) | Setting key (primary key) |
| `value` | JSONB | Setting value |
| `description` | TEXT | Setting description |
| `updated_at` | TIMESTAMPTZ | Last update |

#### `job_queue`
Background job processing queue.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `job_type` | VARCHAR(100) | Job type |
| `payload` | JSONB | Job data |
| `status` | VARCHAR(20) | pending, processing, completed, failed, retrying |
| `attempts` | INTEGER | Retry attempts |
| `max_attempts` | INTEGER | Maximum retries |
| `error_message` | TEXT | Error details |
| `scheduled_at` | TIMESTAMPTZ | Scheduled time |
| `started_at` | TIMESTAMPTZ | Start time |
| `completed_at` | TIMESTAMPTZ | Completion time |

## Database Features

### Automatic Triggers

1. **Updated At Triggers**: Automatically update `updated_at` timestamps
2. **Search Vector Updates**: Maintain full-text search indexes
3. **Audit Logging**: Track changes to critical tables

### Performance Optimizations

1. **Strategic Indexing**: Optimized for common query patterns
2. **Partial Indexes**: Index only active/relevant records
3. **GIN Indexes**: For JSONB and array columns
4. **Connection Pooling**: Async connection management

### Cost Management

1. **AI Cost Tracking**: Real-time cost monitoring
2. **Usage Limits**: Subscription-based restrictions
3. **Alert Thresholds**: Automated cost alerts
4. **Emergency Shutoffs**: Prevent cost overruns

### Security Features

1. **Encrypted Credentials**: Application-level encryption
2. **Audit Trails**: Comprehensive logging
3. **Input Validation**: Database-level constraints
4. **Role-Based Access**: User permission system

## Migration Strategy

The database uses Alembic for schema migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Backup & Recovery

1. **Automated Backups**: Daily PostgreSQL dumps
2. **Point-in-Time Recovery**: WAL archiving
3. **Cross-Region Replication**: Disaster recovery
4. **Backup Testing**: Regular restore verification