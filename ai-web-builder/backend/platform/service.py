"""
Platform Integration Service - Orchestrates multiple platform integrations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, PlatformIntegration, CampaignAnalysis
from platform.gohighlevel import GoHighLevelAPI, GoHighLevelAnalyzer, GoHighLevelCredentials
from platform.simvoly import SimvolyAPI, SimvolyAnalyzer, SimvolyCredentials
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
import json
import uuid
import asyncio

logger = logging.getLogger(__name__)

class PlatformIntegrationService:
    """Service for managing platform integrations and campaign analysis"""
    
    def __init__(self, db: AsyncSession, redis_client=None):
        self.db = db
        self.redis = redis_client
    
    async def add_platform_integration(
        self,
        user: User,
        platform_type: str,
        credentials: Dict[str, str],
        integration_name: str
    ) -> PlatformIntegration:
        """Add a platform integration for a user"""
        
        if platform_type == "gohighlevel":
            return await self.add_gohighlevel_integration(user, credentials, integration_name)
        elif platform_type == "simvoly":
            return await self.add_simvoly_integration(user, credentials, integration_name)
        else:
            raise ValueError(f"Unsupported platform type: {platform_type}")

    async def add_gohighlevel_integration(
        self, 
        user: User, 
        credentials: Dict[str, str],
        integration_name: str = "GoHighLevel Account"
    ) -> PlatformIntegration:
        """Add GoHighLevel integration for a user"""
        
        # Test connection first
        ghl_creds = GoHighLevelCredentials(
            api_key=credentials["api_key"],
            location_id=credentials["location_id"],
            agency_id=credentials.get("agency_id")
        )
        
        async with GoHighLevelAPI(ghl_creds) as api:
            connection_test = await api.test_connection()
            
            if not connection_test["success"]:
                raise ValueError(f"GoHighLevel connection failed: {connection_test['error']}")
        
        # Create integration record
        integration = PlatformIntegration(
            user_id=user.id,
            platform_type="gohighlevel",
            integration_name=integration_name,
            credentials={
                "api_key": credentials["api_key"],
                "location_id": credentials["location_id"],
                "agency_id": credentials.get("agency_id")
            },
            connection_status="active",
            last_sync_at=datetime.now(timezone.utc),
            metadata={
                "location_name": connection_test.get("location", {}).get("name", "Unknown"),
                "permissions": connection_test.get("permissions", [])
            }
        )
        
        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        
        logger.info(f"Added GoHighLevel integration for user {user.email}")
        return integration
    
    async def add_simvoly_integration(
        self, 
        user: User, 
        credentials: Dict[str, str],
        integration_name: str = "Simvoly Account"
    ) -> PlatformIntegration:
        """Add Simvoly integration for a user"""
        
        # Test connection first
        simvoly_creds = SimvolyCredentials(
            api_key=credentials["api_key"],
            workspace_id=credentials.get("workspace_id")
        )
        
        async with SimvolyAPI(simvoly_creds) as api:
            connection_test = await api.test_connection()
            
            if not connection_test["success"]:
                raise ValueError(f"Simvoly connection failed: {connection_test['error']}")
        
        # Create integration record
        integration = PlatformIntegration(
            user_id=user.id,
            platform_type="simvoly",
            integration_name=integration_name,
            credentials={
                "api_key": credentials["api_key"],
                "workspace_id": credentials.get("workspace_id")
            },
            connection_status="active",
            last_sync_at=datetime.now(timezone.utc),
            metadata={
                "user_name": connection_test.get("user", {}).get("name", "Unknown"),
                "workspace_name": connection_test.get("workspace", {}).get("name", "Default"),
                "plan": connection_test.get("plan", {}).get("name", "Unknown")
            }
        )
        
        self.db.add(integration)
        await self.db.commit()
        await self.db.refresh(integration)
        
        logger.info(f"Added Simvoly integration for user {user.email}")
        return integration
    
    async def get_user_integrations(self, user: User) -> List[PlatformIntegration]:
        """Get all platform integrations for a user"""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(PlatformIntegration).where(
                PlatformIntegration.user_id == user.id,
                PlatformIntegration.is_active == True
            ).order_by(PlatformIntegration.created_at.desc())
        )
        
        return result.scalars().all()
    
    async def analyze_gohighlevel_campaign(
        self, 
        integration: PlatformIntegration, 
        campaign_id: str
    ) -> CampaignAnalysis:
        """Analyze a specific GoHighLevel campaign"""
        
        if integration.platform_type != "gohighlevel":
            raise ValueError("Integration is not for GoHighLevel")
        
        # Get credentials
        credentials = GoHighLevelCredentials(
            api_key=integration.credentials["api_key"],
            location_id=integration.credentials["location_id"],
            agency_id=integration.credentials.get("agency_id")
        )
        
        async with GoHighLevelAPI(credentials) as api:
            analyzer = GoHighLevelAnalyzer(api)
            
            # Get campaign structure
            campaign_data = await api.analyze_campaign_structure(campaign_id)
            
            # Perform comprehensive audit
            audit_results = await analyzer.audit_campaign(campaign_data)
            
            # Save analysis results
            analysis = CampaignAnalysis(
                user_id=integration.user_id,
                integration_id=integration.id,
                platform_type="gohighlevel",
                campaign_id=campaign_id,
                campaign_name=campaign_data.name,
                analysis_type="comprehensive_audit",
                analysis_results=audit_results,
                ai_recommendations=audit_results["recommendations"],
                campaign_metadata={
                    "pages_count": len(campaign_data.pages),
                    "forms_count": len(campaign_data.forms),
                    "workflows_count": len(campaign_data.workflows),
                    "status": campaign_data.status,
                    "created_at": campaign_data.created_at.isoformat(),
                    "updated_at": campaign_data.updated_at.isoformat()
                }
            )
            
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            
            logger.info(f"Analyzed GoHighLevel campaign {campaign_id} for user {integration.user_id}")
            return analysis
    
    async def analyze_simvoly_campaign(
        self, 
        integration: PlatformIntegration, 
        campaign_id: str,
        campaign_type: str = "website"
    ) -> CampaignAnalysis:
        """Analyze a specific Simvoly campaign"""
        
        if integration.platform_type != "simvoly":
            raise ValueError("Integration is not for Simvoly")
        
        # Get credentials
        credentials = SimvolyCredentials(
            api_key=integration.credentials["api_key"],
            workspace_id=integration.credentials.get("workspace_id")
        )
        
        async with SimvolyAPI(credentials) as api:
            analyzer = SimvolyAnalyzer(api)
            
            # Get campaign structure
            campaign_data = await api.analyze_campaign_structure(campaign_id, campaign_type)
            
            # Perform comprehensive audit
            audit_results = await analyzer.audit_campaign(campaign_data)
            
            # Save analysis results
            analysis = CampaignAnalysis(
                user_id=integration.user_id,
                integration_id=integration.id,
                platform_type="simvoly",
                campaign_id=campaign_id,
                campaign_name=campaign_data.name,
                analysis_type="comprehensive_audit",
                analysis_results=audit_results,
                ai_recommendations=audit_results["recommendations"],
                campaign_metadata={
                    "campaign_type": campaign_data.type,
                    "pages_count": len(campaign_data.pages),
                    "forms_count": len(campaign_data.forms),
                    "products_count": len(campaign_data.products),
                    "status": campaign_data.status,
                    "created_at": campaign_data.created_at.isoformat(),
                    "updated_at": campaign_data.updated_at.isoformat()
                }
            )
            
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
            
            logger.info(f"Analyzed Simvoly campaign {campaign_id} for user {integration.user_id}")
            return analysis
    
    async def get_user_campaign_analyses(
        self, 
        user: User, 
        platform_type: Optional[str] = None
    ) -> List[CampaignAnalysis]:
        """Get all campaign analyses for a user"""
        from sqlalchemy import select
        
        query = select(CampaignAnalysis).where(CampaignAnalysis.user_id == user.id)
        
        if platform_type:
            query = query.where(CampaignAnalysis.platform_type == platform_type)
        
        query = query.order_by(CampaignAnalysis.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def discover_gohighlevel_campaigns(
        self, 
        integration: PlatformIntegration
    ) -> List[Dict[str, Any]]:
        """Discover all campaigns in a GoHighLevel account"""
        
        if integration.platform_type != "gohighlevel":
            raise ValueError("Integration is not for GoHighLevel")
        
        credentials = GoHighLevelCredentials(
            api_key=integration.credentials["api_key"],
            location_id=integration.credentials["location_id"],
            agency_id=integration.credentials.get("agency_id")
        )
        
        async with GoHighLevelAPI(credentials) as api:
            # Get all funnels (campaigns)
            funnels = await api.get_funnels()
            
            campaign_list = []
            for funnel in funnels:
                campaign_info = {
                    "id": funnel.get("id"),
                    "name": funnel.get("name", "Unnamed Campaign"),
                    "status": funnel.get("status", "unknown"),
                    "type": "funnel",
                    "created_at": funnel.get("dateAdded"),
                    "updated_at": funnel.get("dateUpdated"),
                    "page_count": len(funnel.get("pages", [])),
                    "has_been_analyzed": await self._check_if_analyzed(
                        integration.user_id, funnel.get("id")
                    )
                }
                campaign_list.append(campaign_info)
            
            # Update integration metadata
            integration.metadata = {
                **integration.metadata,
                "last_discovery": datetime.now(timezone.utc).isoformat(),
                "total_campaigns": len(campaign_list),
                "active_campaigns": len([c for c in campaign_list if c["status"] == "active"])
            }
            await self.db.commit()
            
            return campaign_list
    
    async def discover_simvoly_campaigns(
        self, 
        integration: PlatformIntegration
    ) -> List[Dict[str, Any]]:
        """Discover all campaigns in a Simvoly account"""
        
        if integration.platform_type != "simvoly":
            raise ValueError("Integration is not for Simvoly")
        
        credentials = SimvolyCredentials(
            api_key=integration.credentials["api_key"],
            workspace_id=integration.credentials.get("workspace_id")
        )
        
        async with SimvolyAPI(credentials) as api:
            # Get all websites and funnels
            websites_task = api.get_websites()
            funnels_task = api.get_funnels()
            
            websites, funnels = await asyncio.gather(
                websites_task, funnels_task, return_exceptions=True
            )
            
            campaign_list = []
            
            # Process websites
            if isinstance(websites, list):
                for website in websites:
                    campaign_info = {
                        "id": website.get("id"),
                        "name": website.get("name", "Unnamed Website"),
                        "status": website.get("status", "unknown"),
                        "type": "website",
                        "created_at": website.get("created_at"),
                        "updated_at": website.get("updated_at"),
                        "page_count": len(website.get("pages", [])),
                        "has_been_analyzed": await self._check_if_analyzed(
                            integration.user_id, website.get("id")
                        )
                    }
                    campaign_list.append(campaign_info)
            
            # Process funnels
            if isinstance(funnels, list):
                for funnel in funnels:
                    campaign_info = {
                        "id": funnel.get("id"),
                        "name": funnel.get("name", "Unnamed Funnel"),
                        "status": funnel.get("status", "unknown"),
                        "type": "funnel",
                        "created_at": funnel.get("created_at"),
                        "updated_at": funnel.get("updated_at"),
                        "page_count": len(funnel.get("pages", [])),
                        "has_been_analyzed": await self._check_if_analyzed(
                            integration.user_id, funnel.get("id")
                        )
                    }
                    campaign_list.append(campaign_info)
            
            # Update integration metadata
            integration.metadata = {
                **integration.metadata,
                "last_discovery": datetime.now(timezone.utc).isoformat(),
                "total_campaigns": len(campaign_list),
                "websites_count": len(websites) if isinstance(websites, list) else 0,
                "funnels_count": len(funnels) if isinstance(funnels, list) else 0,
                "active_campaigns": len([c for c in campaign_list if c["status"] == "active"])
            }
            await self.db.commit()
            
            return campaign_list
    
    async def _check_if_analyzed(self, user_id: uuid.UUID, campaign_id: str) -> bool:
        """Check if a campaign has already been analyzed"""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(CampaignAnalysis).where(
                CampaignAnalysis.user_id == user_id,
                CampaignAnalysis.campaign_id == campaign_id
            ).limit(1)
        )
        
        return result.scalar_one_or_none() is not None
    
    async def test_integration_connection(self, integration: PlatformIntegration) -> Dict[str, Any]:
        """Test if an integration connection is still valid"""
        
        if integration.platform_type == "gohighlevel":
            credentials = GoHighLevelCredentials(
                api_key=integration.credentials["api_key"],
                location_id=integration.credentials["location_id"],
                agency_id=integration.credentials.get("agency_id")
            )
            
            async with GoHighLevelAPI(credentials) as api:
                result = await api.test_connection()
                
                # Update integration status
                if result["success"]:
                    integration.connection_status = "active"
                    integration.last_sync_at = datetime.now(timezone.utc)
                else:
                    integration.connection_status = "error"
                    integration.error_message = result.get("error")
                
                await self.db.commit()
                return result
        
        elif integration.platform_type == "simvoly":
            credentials = SimvolyCredentials(
                api_key=integration.credentials["api_key"],
                workspace_id=integration.credentials.get("workspace_id")
            )
            
            async with SimvolyAPI(credentials) as api:
                result = await api.test_connection()
                
                # Update integration status
                if result["success"]:
                    integration.connection_status = "active"
                    integration.last_sync_at = datetime.now(timezone.utc)
                else:
                    integration.connection_status = "error"
                    integration.error_message = result.get("error")
                
                await self.db.commit()
                return result
        
        else:
            return {"success": False, "error": "Unsupported platform type"}
    
    async def generate_ai_improvement_suggestions(
        self, 
        analysis: CampaignAnalysis
    ) -> Dict[str, Any]:
        """Generate AI-powered improvement suggestions for a campaign"""
        
        # This would integrate with our AI service
        # For now, return enhanced recommendations based on analysis
        
        base_recommendations = analysis.ai_recommendations or []
        
        enhanced_suggestions = {
            "priority_improvements": [],
            "quick_wins": [],
            "advanced_optimizations": [],
            "estimated_impact": {}
        }
        
        # Categorize recommendations by priority and effort
        for rec in base_recommendations:
            if rec.get("priority") == "high":
                enhanced_suggestions["priority_improvements"].append({
                    **rec,
                    "implementation_effort": "medium",
                    "expected_lift": "15-30%"
                })
            elif rec.get("impact") == "High" and rec.get("priority") != "high":
                enhanced_suggestions["quick_wins"].append({
                    **rec,
                    "implementation_effort": "low",
                    "expected_lift": "5-15%"
                })
            else:
                enhanced_suggestions["advanced_optimizations"].append({
                    **rec,
                    "implementation_effort": "high",
                    "expected_lift": "10-25%"
                })
        
        # Calculate estimated impact
        analysis_results = analysis.analysis_results or {}
        current_score = analysis_results.get("overall_score", 50)
        
        enhanced_suggestions["estimated_impact"] = {
            "current_score": current_score,
            "potential_score": min(100, current_score + 25),
            "conversion_improvement": "20-40%",
            "implementation_timeline": "2-4 weeks"
        }
        
        return enhanced_suggestions
    
    async def sync_integration_data(self, integration: PlatformIntegration) -> Dict[str, Any]:
        """Sync latest data from platform integration"""
        
        try:
            if integration.platform_type == "gohighlevel":
                # Test connection
                connection_test = await self.test_integration_connection(integration)
                
                if not connection_test["success"]:
                    return {
                        "success": False,
                        "error": connection_test["error"]
                    }
                
                # Discover campaigns
                campaigns = await self.discover_gohighlevel_campaigns(integration)
                
                integration.last_sync_at = datetime.now(timezone.utc)
                await self.db.commit()
                
                return {
                    "success": True,
                    "campaigns_found": len(campaigns),
                    "last_sync": integration.last_sync_at.isoformat()
                }
            
            elif integration.platform_type == "simvoly":
                # Test connection
                connection_test = await self.test_integration_connection(integration)
                
                if not connection_test["success"]:
                    return {
                        "success": False,
                        "error": connection_test["error"]
                    }
                
                # Discover campaigns
                campaigns = await self.discover_simvoly_campaigns(integration)
                
                integration.last_sync_at = datetime.now(timezone.utc)
                await self.db.commit()
                
                return {
                    "success": True,
                    "campaigns_found": len(campaigns),
                    "last_sync": integration.last_sync_at.isoformat()
                }
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported platform type"
                }
                
        except Exception as e:
            logger.error(f"Error syncing integration {integration.id}: {e}")
            integration.connection_status = "error"
            integration.error_message = str(e)
            await self.db.commit()
            
            return {
                "success": False,
                "error": str(e)
            }