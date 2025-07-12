"""
Pydantic schemas for platform integration
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, List, Any
from datetime import datetime

class GoHighLevelCredentials(BaseModel):
    api_key: str = Field(..., min_length=10, description="GoHighLevel API key")
    location_id: str = Field(..., min_length=10, description="GoHighLevel location ID")
    agency_id: Optional[str] = Field(None, description="GoHighLevel agency ID (optional)")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.startswith(('ghl_', 'eyJ', 'pk_')):
            raise ValueError('Invalid GoHighLevel API key format')
        return v

class SimvolyCredentials(BaseModel):
    api_key: str = Field(..., min_length=10, description="Simvoly API key")
    workspace_id: Optional[str] = Field(None, description="Simvoly workspace ID (optional)")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.startswith(('sv_', 'simvoly_', 'Bearer ')):
            # Simvoly API keys typically start with these prefixes
            pass  # Allow any format for now as Simvoly format may vary
        return v

class PlatformIntegrationCreate(BaseModel):
    platform_type: str = Field(..., description="Platform type (gohighlevel, simvoly, wordpress)")
    integration_name: str = Field(..., min_length=1, max_length=255, description="User-friendly name for integration")
    credentials: Dict[str, Any] = Field(..., description="Platform-specific credentials")
    
    @validator('platform_type')
    def validate_platform_type(cls, v):
        allowed_platforms = ['gohighlevel', 'simvoly', 'wordpress']
        if v not in allowed_platforms:
            raise ValueError(f'Platform type must be one of: {", ".join(allowed_platforms)}')
        return v

class PlatformIntegrationResponse(BaseModel):
    id: str
    platform_type: str
    integration_name: str
    connection_status: str
    created_at: datetime
    last_sync_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class CampaignDiscoveryResponse(BaseModel):
    campaigns: List[Dict[str, Any]]
    total_count: int
    last_discovery: datetime
    integration_id: str

class CampaignAnalysisRequest(BaseModel):
    campaign_id: str = Field(..., description="Platform-specific campaign ID")
    analysis_type: Optional[str] = Field("comprehensive_audit", description="Type of analysis to perform")
    campaign_type: Optional[str] = Field("website", description="Campaign type (website, funnel, store) - used for Simvoly")

class CampaignAnalysisResponse(BaseModel):
    id: str
    campaign_id: str
    campaign_name: str
    platform_type: str
    analysis_type: str
    overall_score: int
    created_at: datetime
    analysis_results: Dict[str, Any]
    ai_recommendations: List[Dict[str, Any]]
    campaign_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class AIImprovementSuggestions(BaseModel):
    priority_improvements: List[Dict[str, Any]]
    quick_wins: List[Dict[str, Any]]
    advanced_optimizations: List[Dict[str, Any]]
    estimated_impact: Dict[str, Any]

class ConnectionTestResponse(BaseModel):
    success: bool
    platform_type: str
    integration_name: Optional[str] = None
    location_info: Optional[Dict[str, Any]] = None
    permissions: Optional[List[str]] = None
    error: Optional[str] = None

class SyncIntegrationResponse(BaseModel):
    success: bool
    campaigns_found: Optional[int] = None
    last_sync: Optional[datetime] = None
    error: Optional[str] = None

class CampaignSummary(BaseModel):
    id: str
    name: str
    platform_type: str
    status: str
    type: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    page_count: Optional[int] = 0
    form_count: Optional[int] = 0
    workflow_count: Optional[int] = 0
    has_been_analyzed: bool = False
    last_analysis_score: Optional[int] = None
    last_analysis_date: Optional[datetime] = None

class AnalyticsOverview(BaseModel):
    total_campaigns: int
    analyzed_campaigns: int
    average_score: float
    high_performing_campaigns: int  # Score > 80
    low_performing_campaigns: int   # Score < 50
    recent_analyses: List[CampaignAnalysisResponse]
    top_recommendations: List[Dict[str, Any]]

class PlatformCapabilities(BaseModel):
    platform_type: str
    supported_features: List[str]
    api_endpoints: List[str]
    data_types: List[str]
    analysis_types: List[str]
    export_formats: List[str]

class IntegrationHealth(BaseModel):
    integration_id: str
    platform_type: str
    status: str  # healthy, warning, error
    last_successful_sync: Optional[datetime]
    last_error: Optional[str]
    api_rate_limit_status: Optional[Dict[str, Any]]
    data_freshness: str  # fresh, stale, very_stale
    recommendations: List[str]

# Request/Response schemas for specific operations
class BulkAnalysisRequest(BaseModel):
    integration_id: str
    campaign_ids: List[str] = Field(..., max_items=10, description="Max 10 campaigns per bulk request")
    analysis_type: Optional[str] = "comprehensive_audit"
    
    @validator('campaign_ids')
    def validate_campaign_ids(cls, v):
        if len(v) == 0:
            raise ValueError('At least one campaign ID is required')
        return v

class BulkAnalysisResponse(BaseModel):
    request_id: str
    total_campaigns: int
    successful_analyses: int
    failed_analyses: int
    results: List[CampaignAnalysisResponse]
    errors: List[Dict[str, str]]

class ExportAnalysisRequest(BaseModel):
    analysis_id: str
    export_format: str = Field(..., description="Export format (pdf, excel, json)")
    include_raw_data: bool = False
    
    @validator('export_format')
    def validate_export_format(cls, v):
        allowed_formats = ['pdf', 'excel', 'json', 'csv']
        if v not in allowed_formats:
            raise ValueError(f'Export format must be one of: {", ".join(allowed_formats)}')
        return v

class ExportAnalysisResponse(BaseModel):
    export_id: str
    download_url: str
    expires_at: datetime
    file_size_bytes: int
    export_format: str

# Webhook schemas for real-time updates
class WebhookEvent(BaseModel):
    event_type: str
    platform_type: str
    integration_id: str
    campaign_id: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]

class WebhookSubscription(BaseModel):
    webhook_url: str = Field(..., description="URL to receive webhook events")
    events: List[str] = Field(..., description="List of events to subscribe to")
    secret: Optional[str] = Field(None, description="Secret for webhook verification")
    
    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Webhook URL must start with http:// or https://')
        return v