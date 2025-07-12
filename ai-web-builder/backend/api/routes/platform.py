"""
Platform integration API routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from auth.dependencies import get_current_user
from database.models import User
from platform.service import PlatformIntegrationService
from platform.schemas import (
    PlatformIntegrationCreate, PlatformIntegrationResponse,
    CampaignDiscoveryResponse, CampaignAnalysisRequest, CampaignAnalysisResponse,
    AIImprovementSuggestions, ConnectionTestResponse, SyncIntegrationResponse,
    GoHighLevelCredentials, SimvolyCredentials, BulkAnalysisRequest, BulkAnalysisResponse,
    AnalyticsOverview
)
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/integrations", response_model=PlatformIntegrationResponse)
async def create_platform_integration(
    integration_data: PlatformIntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new platform integration"""
    try:
        service = PlatformIntegrationService(db)
        
        if integration_data.platform_type == "gohighlevel":
            # Validate GoHighLevel credentials
            ghl_creds = GoHighLevelCredentials(**integration_data.credentials)
            integration = await service.add_gohighlevel_integration(
                current_user,
                ghl_creds.model_dump(),
                integration_data.integration_name
            )
        elif integration_data.platform_type == "simvoly":
            # Validate Simvoly credentials
            simvoly_creds = SimvolyCredentials(**integration_data.credentials)
            integration = await service.add_simvoly_integration(
                current_user,
                simvoly_creds.model_dump(),
                integration_data.integration_name
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Platform type '{integration_data.platform_type}' not yet supported"
            )
        
        return PlatformIntegrationResponse.model_validate(integration)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating platform integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create platform integration"
        )

@router.get("/integrations", response_model=List[PlatformIntegrationResponse])
async def get_user_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all platform integrations for current user"""
    try:
        service = PlatformIntegrationService(db)
        integrations = await service.get_user_integrations(current_user)
        
        return [PlatformIntegrationResponse.model_validate(integration) for integration in integrations]
        
    except Exception as e:
        logger.error(f"Error fetching user integrations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch integrations"
        )

@router.post("/integrations/{integration_id}/test", response_model=ConnectionTestResponse)
async def test_integration_connection(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test if platform integration connection is still valid"""
    try:
        service = PlatformIntegrationService(db)
        integrations = await service.get_user_integrations(current_user)
        
        integration = next((i for i in integrations if str(i.id) == integration_id), None)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        result = await service.test_integration_connection(integration)
        
        return ConnectionTestResponse(
            success=result["success"],
            platform_type=integration.platform_type,
            integration_name=integration.integration_name,
            location_info=result.get("location"),
            permissions=result.get("permissions"),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing integration connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test connection"
        )

@router.post("/integrations/{integration_id}/sync", response_model=SyncIntegrationResponse)
async def sync_integration_data(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Sync latest data from platform integration"""
    try:
        service = PlatformIntegrationService(db)
        integrations = await service.get_user_integrations(current_user)
        
        integration = next((i for i in integrations if str(i.id) == integration_id), None)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        result = await service.sync_integration_data(integration)
        
        return SyncIntegrationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing integration data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync integration data"
        )

@router.get("/integrations/{integration_id}/campaigns")
async def discover_campaigns(
    integration_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Discover all campaigns in a platform integration"""
    try:
        service = PlatformIntegrationService(db)
        integrations = await service.get_user_integrations(current_user)
        
        integration = next((i for i in integrations if str(i.id) == integration_id), None)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        if integration.platform_type == "gohighlevel":
            campaigns = await service.discover_gohighlevel_campaigns(integration)
        elif integration.platform_type == "simvoly":
            campaigns = await service.discover_simvoly_campaigns(integration)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign discovery not supported for {integration.platform_type}"
            )
        
        return CampaignDiscoveryResponse(
            campaigns=campaigns,
            total_count=len(campaigns),
            last_discovery=integration.last_sync_at or integration.created_at,
            integration_id=integration_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering campaigns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to discover campaigns"
        )

@router.post("/integrations/{integration_id}/campaigns/analyze", response_model=CampaignAnalysisResponse)
async def analyze_campaign(
    integration_id: str,
    analysis_request: CampaignAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze a specific campaign"""
    try:
        service = PlatformIntegrationService(db)
        integrations = await service.get_user_integrations(current_user)
        
        integration = next((i for i in integrations if str(i.id) == integration_id), None)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        if integration.platform_type == "gohighlevel":
            analysis = await service.analyze_gohighlevel_campaign(
                integration,
                analysis_request.campaign_id
            )
        elif integration.platform_type == "simvoly":
            # For Simvoly, we need to determine campaign type from metadata or request
            campaign_type = getattr(analysis_request, 'campaign_type', 'website')
            analysis = await service.analyze_simvoly_campaign(
                integration,
                analysis_request.campaign_id,
                campaign_type
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign analysis not supported for {integration.platform_type}"
            )
        
        # Extract overall score from analysis results
        overall_score = analysis.analysis_results.get("overall_score", 0)
        
        return CampaignAnalysisResponse(
            id=str(analysis.id),
            campaign_id=analysis.campaign_id,
            campaign_name=analysis.campaign_name,
            platform_type=analysis.platform_type,
            analysis_type=analysis.analysis_type,
            overall_score=overall_score,
            created_at=analysis.created_at,
            analysis_results=analysis.analysis_results,
            ai_recommendations=analysis.ai_recommendations,
            campaign_metadata=analysis.campaign_metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing campaign: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze campaign"
        )

@router.get("/analyses", response_model=List[CampaignAnalysisResponse])
async def get_user_analyses(
    platform_type: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all campaign analyses for current user"""
    try:
        service = PlatformIntegrationService(db)
        analyses = await service.get_user_campaign_analyses(current_user, platform_type)
        
        # Limit results
        analyses = analyses[:limit]
        
        return [
            CampaignAnalysisResponse(
                id=str(analysis.id),
                campaign_id=analysis.campaign_id,
                campaign_name=analysis.campaign_name,
                platform_type=analysis.platform_type,
                analysis_type=analysis.analysis_type,
                overall_score=analysis.analysis_results.get("overall_score", 0),
                created_at=analysis.created_at,
                analysis_results=analysis.analysis_results,
                ai_recommendations=analysis.ai_recommendations,
                campaign_metadata=analysis.campaign_metadata
            )
            for analysis in analyses
        ]
        
    except Exception as e:
        logger.error(f"Error fetching user analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analyses"
        )

@router.get("/analyses/{analysis_id}/suggestions", response_model=AIImprovementSuggestions)
async def get_ai_improvement_suggestions(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI-powered improvement suggestions for a campaign analysis"""
    try:
        service = PlatformIntegrationService(db)
        analyses = await service.get_user_campaign_analyses(current_user)
        
        analysis = next((a for a in analyses if str(a.id) == analysis_id), None)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        
        suggestions = await service.generate_ai_improvement_suggestions(analysis)
        
        return AIImprovementSuggestions(**suggestions)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI suggestions"
        )

@router.post("/integrations/{integration_id}/campaigns/analyze-bulk", response_model=BulkAnalysisResponse)
async def bulk_analyze_campaigns(
    integration_id: str,
    bulk_request: BulkAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze multiple campaigns in bulk"""
    try:
        service = PlatformIntegrationService(db)
        integrations = await service.get_user_integrations(current_user)
        
        integration = next((i for i in integrations if str(i.id) == integration_id), None)
        if not integration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        results = []
        errors = []
        
        # Process each campaign
        for campaign_id in bulk_request.campaign_ids:
            try:
                if integration.platform_type == "gohighlevel":
                    analysis = await service.analyze_gohighlevel_campaign(
                        integration,
                        campaign_id
                    )
                elif integration.platform_type == "simvoly":
                    # Use default campaign type for bulk analysis
                    analysis = await service.analyze_simvoly_campaign(
                        integration,
                        campaign_id,
                        "website"  # Default to website for bulk analysis
                    )
                else:
                    errors.append({
                        "campaign_id": campaign_id,
                        "error": f"Platform type {integration.platform_type} not supported"
                    })
                    continue
                
                results.append(CampaignAnalysisResponse(
                    id=str(analysis.id),
                    campaign_id=analysis.campaign_id,
                    campaign_name=analysis.campaign_name,
                    platform_type=analysis.platform_type,
                    analysis_type=analysis.analysis_type,
                    overall_score=analysis.analysis_results.get("overall_score", 0),
                    created_at=analysis.created_at,
                    analysis_results=analysis.analysis_results,
                    ai_recommendations=analysis.ai_recommendations,
                    campaign_metadata=analysis.campaign_metadata
                ))
            except Exception as e:
                errors.append({
                    "campaign_id": campaign_id,
                    "error": str(e)
                })
        
        return BulkAnalysisResponse(
            request_id=f"bulk_{integration_id}_{len(bulk_request.campaign_ids)}",
            total_campaigns=len(bulk_request.campaign_ids),
            successful_analyses=len(results),
            failed_analyses=len(errors),
            results=results,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk campaign analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk analysis"
        )

@router.get("/analytics/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics overview for user's campaigns"""
    try:
        service = PlatformIntegrationService(db)
        analyses = await service.get_user_campaign_analyses(current_user)
        
        # Calculate overview statistics
        total_campaigns = len(analyses)
        analyzed_campaigns = total_campaigns
        
        if total_campaigns > 0:
            scores = [a.analysis_results.get("overall_score", 0) for a in analyses]
            average_score = sum(scores) / len(scores)
            high_performing = len([s for s in scores if s > 80])
            low_performing = len([s for s in scores if s < 50])
        else:
            average_score = 0
            high_performing = 0
            low_performing = 0
        
        # Get recent analyses (last 5)
        recent_analyses = analyses[:5]
        
        # Aggregate top recommendations
        all_recommendations = []
        for analysis in analyses:
            all_recommendations.extend(analysis.ai_recommendations or [])
        
        # Count recommendation frequency
        rec_counts = {}
        for rec in all_recommendations:
            title = rec.get("title", "Unknown")
            rec_counts[title] = rec_counts.get(title, 0) + 1
        
        top_recommendations = [
            {"title": title, "frequency": count}
            for title, count in sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return AnalyticsOverview(
            total_campaigns=total_campaigns,
            analyzed_campaigns=analyzed_campaigns,
            average_score=round(average_score, 1),
            high_performing_campaigns=high_performing,
            low_performing_campaigns=low_performing,
            recent_analyses=[
                CampaignAnalysisResponse(
                    id=str(analysis.id),
                    campaign_id=analysis.campaign_id,
                    campaign_name=analysis.campaign_name,
                    platform_type=analysis.platform_type,
                    analysis_type=analysis.analysis_type,
                    overall_score=analysis.analysis_results.get("overall_score", 0),
                    created_at=analysis.created_at,
                    analysis_results=analysis.analysis_results,
                    ai_recommendations=analysis.ai_recommendations,
                    campaign_metadata=analysis.campaign_metadata
                )
                for analysis in recent_analyses
            ],
            top_recommendations=top_recommendations
        )
        
    except Exception as e:
        logger.error(f"Error fetching analytics overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch analytics overview"
        )