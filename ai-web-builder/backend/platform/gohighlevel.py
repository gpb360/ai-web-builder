"""
GoHighLevel API Integration for Campaign Analysis
"""
import aiohttp
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import logging
from dataclasses import dataclass
from config import settings

logger = logging.getLogger(__name__)

@dataclass
class GoHighLevelCredentials:
    """GoHighLevel API credentials"""
    api_key: str
    location_id: str
    agency_id: Optional[str] = None

@dataclass
class CampaignData:
    """Structured campaign data from GoHighLevel"""
    id: str
    name: str
    type: str  # funnel, website, email_sequence
    status: str
    created_at: datetime
    updated_at: datetime
    pages: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    workflows: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    raw_data: Dict[str, Any]

class GoHighLevelAPI:
    """GoHighLevel API client for campaign analysis"""
    
    BASE_URL = "https://services.leadconnectorhq.com"
    
    def __init__(self, credentials: GoHighLevelCredentials):
        self.credentials = credentials
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.credentials.api_key}",
                "Version": "2021-07-28",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return account info"""
        try:
            async with self.session.get(f"{self.BASE_URL}/locations/{self.credentials.location_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "location": data.get("location", {}),
                        "permissions": data.get("permissions", [])
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API Error {response.status}: {error_text}"
                    }
        except Exception as e:
            logger.error(f"GoHighLevel connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_funnels(self) -> List[Dict[str, Any]]:
        """Retrieve all funnels from GoHighLevel"""
        try:
            url = f"{self.BASE_URL}/funnels/"
            params = {"locationId": self.credentials.location_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("funnels", [])
                else:
                    logger.error(f"Failed to get funnels: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching funnels: {e}")
            return []
    
    async def get_funnel_pages(self, funnel_id: str) -> List[Dict[str, Any]]:
        """Get all pages for a specific funnel"""
        try:
            url = f"{self.BASE_URL}/funnels/{funnel_id}/pages"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("pages", [])
                else:
                    logger.error(f"Failed to get funnel pages: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching funnel pages: {e}")
            return []
    
    async def get_forms(self) -> List[Dict[str, Any]]:
        """Retrieve all forms from GoHighLevel"""
        try:
            url = f"{self.BASE_URL}/forms/"
            params = {"locationId": self.credentials.location_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("forms", [])
                else:
                    logger.error(f"Failed to get forms: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching forms: {e}")
            return []
    
    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Retrieve all workflows from GoHighLevel"""
        try:
            url = f"{self.BASE_URL}/workflows/"
            params = {"locationId": self.credentials.location_id}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("workflows", [])
                else:
                    logger.error(f"Failed to get workflows: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching workflows: {e}")
            return []
    
    async def get_campaign_analytics(self, campaign_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get analytics data for a campaign"""
        try:
            url = f"{self.BASE_URL}/reports/funnels/{campaign_id}"
            params = {
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "locationId": self.credentials.location_id
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get campaign analytics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching campaign analytics: {e}")
            return {}
    
    async def analyze_campaign_structure(self, funnel_id: str) -> CampaignData:
        """Comprehensive analysis of a campaign structure"""
        try:
            # Get funnel details
            funnel_url = f"{self.BASE_URL}/funnels/{funnel_id}"
            async with self.session.get(funnel_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to get funnel details: {response.status}")
                funnel_data = await response.json()
            
            # Get all related data in parallel
            pages_task = self.get_funnel_pages(funnel_id)
            forms_task = self.get_forms()
            workflows_task = self.get_workflows()
            
            pages, all_forms, all_workflows = await asyncio.gather(
                pages_task, forms_task, workflows_task, return_exceptions=True
            )
            
            # Filter forms and workflows related to this funnel
            related_forms = [f for f in all_forms if f.get("funnelId") == funnel_id] if isinstance(all_forms, list) else []
            related_workflows = [w for w in all_workflows if funnel_id in w.get("triggers", {}).get("funnels", [])] if isinstance(all_workflows, list) else []
            
            # Get recent analytics (last 30 days)
            end_date = datetime.now(timezone.utc)
            start_date = end_date.replace(day=1)  # Start of current month
            analytics = await self.get_campaign_analytics(funnel_id, start_date, end_date)
            
            return CampaignData(
                id=funnel_data.get("id", funnel_id),
                name=funnel_data.get("name", "Unknown"),
                type="funnel",
                status=funnel_data.get("status", "unknown"),
                created_at=datetime.fromisoformat(funnel_data.get("dateAdded", "2024-01-01").replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(funnel_data.get("dateUpdated", "2024-01-01").replace("Z", "+00:00")),
                pages=pages if isinstance(pages, list) else [],
                forms=related_forms,
                workflows=related_workflows,
                analytics=analytics,
                raw_data=funnel_data
            )
            
        except Exception as e:
            logger.error(f"Error analyzing campaign structure: {e}")
            raise
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get detailed content for a specific page"""
        try:
            url = f"{self.BASE_URL}/funnels/page/{page_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get page content: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching page content: {e}")
            return {}

class GoHighLevelAnalyzer:
    """Analyze GoHighLevel campaigns for improvement opportunities"""
    
    def __init__(self, api_client: GoHighLevelAPI):
        self.api = api_client
    
    async def audit_campaign(self, campaign_data: CampaignData) -> Dict[str, Any]:
        """Comprehensive campaign audit"""
        audit_results = {
            "campaign_id": campaign_data.id,
            "campaign_name": campaign_data.name,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": 0,
            "issues": [],
            "opportunities": [],
            "recommendations": [],
            "technical_analysis": {},
            "performance_analysis": {},
            "conversion_analysis": {}
        }
        
        # Analyze campaign structure
        structure_analysis = await self._analyze_structure(campaign_data)
        audit_results["technical_analysis"] = structure_analysis
        
        # Analyze performance metrics
        performance_analysis = await self._analyze_performance(campaign_data)
        audit_results["performance_analysis"] = performance_analysis
        
        # Analyze conversion optimization
        conversion_analysis = await self._analyze_conversions(campaign_data)
        audit_results["conversion_analysis"] = conversion_analysis
        
        # Generate overall score and recommendations
        audit_results["overall_score"] = self._calculate_overall_score(
            structure_analysis, performance_analysis, conversion_analysis
        )
        audit_results["recommendations"] = self._generate_recommendations(
            structure_analysis, performance_analysis, conversion_analysis
        )
        
        return audit_results
    
    async def _analyze_structure(self, campaign_data: CampaignData) -> Dict[str, Any]:
        """Analyze campaign technical structure"""
        analysis = {
            "page_count": len(campaign_data.pages),
            "form_count": len(campaign_data.forms),
            "workflow_count": len(campaign_data.workflows),
            "structure_issues": [],
            "structure_score": 0
        }
        
        # Check for common structural issues
        if analysis["page_count"] == 0:
            analysis["structure_issues"].append("No pages found in campaign")
        elif analysis["page_count"] > 10:
            analysis["structure_issues"].append("Campaign has too many pages - may confuse users")
        
        if analysis["form_count"] == 0:
            analysis["structure_issues"].append("No forms found - missing lead capture")
        elif analysis["form_count"] > 5:
            analysis["structure_issues"].append("Too many forms - may cause decision fatigue")
        
        if analysis["workflow_count"] == 0:
            analysis["structure_issues"].append("No automation workflows - missing follow-up")
        
        # Calculate structure score (0-100)
        score = 100
        score -= len(analysis["structure_issues"]) * 15
        score = max(0, min(100, score))
        analysis["structure_score"] = score
        
        return analysis
    
    async def _analyze_performance(self, campaign_data: CampaignData) -> Dict[str, Any]:
        """Analyze campaign performance metrics"""
        analytics = campaign_data.analytics
        
        analysis = {
            "views": analytics.get("totalViews", 0),
            "conversions": analytics.get("totalConversions", 0),
            "conversion_rate": 0,
            "performance_issues": [],
            "performance_score": 0
        }
        
        # Calculate conversion rate
        if analysis["views"] > 0:
            analysis["conversion_rate"] = (analysis["conversions"] / analysis["views"]) * 100
        
        # Identify performance issues
        if analysis["conversion_rate"] < 1:
            analysis["performance_issues"].append("Very low conversion rate (< 1%)")
        elif analysis["conversion_rate"] < 2:
            analysis["performance_issues"].append("Low conversion rate (< 2%)")
        
        if analysis["views"] < 100:
            analysis["performance_issues"].append("Low traffic volume")
        
        # Calculate performance score
        score = 50  # Base score
        if analysis["conversion_rate"] > 5:
            score += 30
        elif analysis["conversion_rate"] > 2:
            score += 20
        elif analysis["conversion_rate"] > 1:
            score += 10
        
        if analysis["views"] > 1000:
            score += 20
        elif analysis["views"] > 500:
            score += 10
        
        score -= len(analysis["performance_issues"]) * 10
        analysis["performance_score"] = max(0, min(100, score))
        
        return analysis
    
    async def _analyze_conversions(self, campaign_data: CampaignData) -> Dict[str, Any]:
        """Analyze conversion optimization opportunities"""
        analysis = {
            "form_analysis": [],
            "page_analysis": [],
            "conversion_issues": [],
            "conversion_score": 0
        }
        
        # Analyze forms for conversion optimization
        for form in campaign_data.forms:
            form_analysis = {
                "form_id": form.get("id"),
                "field_count": len(form.get("fields", [])),
                "issues": []
            }
            
            if form_analysis["field_count"] > 5:
                form_analysis["issues"].append("Too many form fields - may reduce conversions")
            
            # Check for required phone/address fields
            fields = form.get("fields", [])
            phone_required = any(f.get("type") == "phone" and f.get("required") for f in fields)
            if phone_required:
                form_analysis["issues"].append("Required phone field may reduce conversions")
            
            analysis["form_analysis"].append(form_analysis)
        
        # Analyze pages for conversion elements
        for page in campaign_data.pages:
            page_analysis = {
                "page_id": page.get("id"),
                "page_name": page.get("name"),
                "issues": []
            }
            
            # This would require actual page content analysis
            # For now, placeholder analysis
            page_analysis["issues"].append("Page content analysis requires detailed HTML parsing")
            analysis["page_analysis"].append(page_analysis)
        
        # Calculate conversion score
        total_issues = sum(len(fa["issues"]) for fa in analysis["form_analysis"])
        total_issues += sum(len(pa["issues"]) for pa in analysis["page_analysis"])
        
        score = 100 - (total_issues * 10)
        analysis["conversion_score"] = max(0, min(100, score))
        
        return analysis
    
    def _calculate_overall_score(self, structure: Dict, performance: Dict, conversion: Dict) -> int:
        """Calculate overall campaign score"""
        weights = {
            "structure": 0.3,
            "performance": 0.4,
            "conversion": 0.3
        }
        
        weighted_score = (
            structure["structure_score"] * weights["structure"] +
            performance["performance_score"] * weights["performance"] +
            conversion["conversion_score"] * weights["conversion"]
        )
        
        return int(weighted_score)
    
    def _generate_recommendations(self, structure: Dict, performance: Dict, conversion: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Structure recommendations
        if structure["structure_score"] < 70:
            recommendations.append({
                "category": "Structure",
                "priority": "high",
                "title": "Simplify Campaign Structure",
                "description": "Reduce complexity to improve user experience",
                "impact": "Medium"
            })
        
        # Performance recommendations
        if performance["conversion_rate"] < 2:
            recommendations.append({
                "category": "Performance",
                "priority": "high",
                "title": "Improve Conversion Rate",
                "description": "Optimize forms and page content to increase conversions",
                "impact": "High"
            })
        
        # Conversion recommendations
        if conversion["conversion_score"] < 70:
            recommendations.append({
                "category": "Conversion",
                "priority": "medium",
                "title": "Optimize Lead Capture",
                "description": "Reduce form friction and improve value proposition",
                "impact": "High"
            })
        
        return recommendations