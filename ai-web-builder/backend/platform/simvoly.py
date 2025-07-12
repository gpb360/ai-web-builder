"""
Simvoly API Integration for Campaign Analysis
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
class SimvolyCredentials:
    """Simvoly API credentials"""
    api_key: str
    workspace_id: Optional[str] = None

@dataclass
class SimvolyCampaignData:
    """Structured campaign data from Simvoly"""
    id: str
    name: str
    type: str  # website, funnel, store
    status: str
    created_at: datetime
    updated_at: datetime
    pages: List[Dict[str, Any]]
    forms: List[Dict[str, Any]]
    products: List[Dict[str, Any]]
    analytics: Dict[str, Any]
    raw_data: Dict[str, Any]

class SimvolyAPI:
    """Simvoly API client for campaign analysis"""
    
    BASE_URL = "https://api.simvoly.com/v1"
    
    def __init__(self, credentials: SimvolyCredentials):
        self.credentials = credentials
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.credentials.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
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
            async with self.session.get(f"{self.BASE_URL}/user/profile") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "user": data.get("user", {}),
                        "workspace": data.get("workspace", {}),
                        "plan": data.get("plan", {})
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"API Error {response.status}: {error_text}"
                    }
        except Exception as e:
            logger.error(f"Simvoly connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_websites(self) -> List[Dict[str, Any]]:
        """Retrieve all websites from Simvoly"""
        try:
            url = f"{self.BASE_URL}/websites"
            params = {}
            if self.credentials.workspace_id:
                params["workspace_id"] = self.credentials.workspace_id
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("websites", [])
                else:
                    logger.error(f"Failed to get websites: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching websites: {e}")
            return []
    
    async def get_funnels(self) -> List[Dict[str, Any]]:
        """Retrieve all funnels from Simvoly"""
        try:
            url = f"{self.BASE_URL}/funnels"
            params = {}
            if self.credentials.workspace_id:
                params["workspace_id"] = self.credentials.workspace_id
            
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
    
    async def get_website_pages(self, website_id: str) -> List[Dict[str, Any]]:
        """Get all pages for a specific website"""
        try:
            url = f"{self.BASE_URL}/websites/{website_id}/pages"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("pages", [])
                else:
                    logger.error(f"Failed to get website pages: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching website pages: {e}")
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
        """Retrieve all forms from Simvoly"""
        try:
            url = f"{self.BASE_URL}/forms"
            params = {}
            if self.credentials.workspace_id:
                params["workspace_id"] = self.credentials.workspace_id
            
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
    
    async def get_products(self) -> List[Dict[str, Any]]:
        """Retrieve all products from Simvoly (e-commerce)"""
        try:
            url = f"{self.BASE_URL}/products"
            params = {}
            if self.credentials.workspace_id:
                params["workspace_id"] = self.credentials.workspace_id
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("products", [])
                else:
                    logger.error(f"Failed to get products: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching products: {e}")
            return []
    
    async def get_analytics(self, website_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get analytics data for a website/funnel"""
        try:
            url = f"{self.BASE_URL}/analytics/{website_id}"
            params = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get analytics: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return {}
    
    async def analyze_campaign_structure(self, campaign_id: str, campaign_type: str) -> SimvolyCampaignData:
        """Comprehensive analysis of a campaign structure"""
        try:
            if campaign_type == "website":
                # Get website details
                website_url = f"{self.BASE_URL}/websites/{campaign_id}"
                async with self.session.get(website_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get website details: {response.status}")
                    campaign_data = await response.json()
                
                # Get website pages
                pages = await self.get_website_pages(campaign_id)
                
            elif campaign_type == "funnel":
                # Get funnel details
                funnel_url = f"{self.BASE_URL}/funnels/{campaign_id}"
                async with self.session.get(funnel_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get funnel details: {response.status}")
                    campaign_data = await response.json()
                
                # Get funnel pages
                pages = await self.get_funnel_pages(campaign_id)
            
            else:
                raise Exception(f"Unsupported campaign type: {campaign_type}")
            
            # Get all related data in parallel
            forms_task = self.get_forms()
            products_task = self.get_products()
            
            all_forms, all_products = await asyncio.gather(
                forms_task, products_task, return_exceptions=True
            )
            
            # Filter forms and products related to this campaign
            related_forms = []
            related_products = []
            
            if isinstance(all_forms, list):
                related_forms = [f for f in all_forms if f.get("website_id") == campaign_id or f.get("funnel_id") == campaign_id]
            
            if isinstance(all_products, list):
                related_products = [p for p in all_products if p.get("website_id") == campaign_id]
            
            # Get analytics (last 30 days)
            end_date = datetime.now(timezone.utc)
            start_date = end_date.replace(day=1)  # Start of current month
            analytics = await self.get_analytics(campaign_id, start_date, end_date)
            
            return SimvolyCampaignData(
                id=campaign_data.get("id", campaign_id),
                name=campaign_data.get("name", "Unknown"),
                type=campaign_type,
                status=campaign_data.get("status", "unknown"),
                created_at=datetime.fromisoformat(campaign_data.get("created_at", "2024-01-01T00:00:00Z").replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(campaign_data.get("updated_at", "2024-01-01T00:00:00Z").replace("Z", "+00:00")),
                pages=pages if isinstance(pages, list) else [],
                forms=related_forms,
                products=related_products,
                analytics=analytics,
                raw_data=campaign_data
            )
            
        except Exception as e:
            logger.error(f"Error analyzing Simvoly campaign structure: {e}")
            raise
    
    async def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get detailed content for a specific page"""
        try:
            url = f"{self.BASE_URL}/pages/{page_id}/content"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get page content: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching page content: {e}")
            return {}

class SimvolyAnalyzer:
    """Analyze Simvoly campaigns for improvement opportunities"""
    
    def __init__(self, api_client: SimvolyAPI):
        self.api = api_client
    
    async def audit_campaign(self, campaign_data: SimvolyCampaignData) -> Dict[str, Any]:
        """Comprehensive campaign audit"""
        audit_results = {
            "campaign_id": campaign_data.id,
            "campaign_name": campaign_data.name,
            "campaign_type": campaign_data.type,
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_score": 0,
            "issues": [],
            "opportunities": [],
            "recommendations": [],
            "technical_analysis": {},
            "performance_analysis": {},
            "conversion_analysis": {},
            "ecommerce_analysis": {}
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
        
        # Analyze e-commerce if applicable
        if campaign_data.products:
            ecommerce_analysis = await self._analyze_ecommerce(campaign_data)
            audit_results["ecommerce_analysis"] = ecommerce_analysis
        
        # Generate overall score and recommendations
        audit_results["overall_score"] = self._calculate_overall_score(
            structure_analysis, performance_analysis, conversion_analysis
        )
        audit_results["recommendations"] = self._generate_recommendations(
            structure_analysis, performance_analysis, conversion_analysis, campaign_data
        )
        
        return audit_results
    
    async def _analyze_structure(self, campaign_data: SimvolyCampaignData) -> Dict[str, Any]:
        """Analyze campaign technical structure"""
        analysis = {
            "page_count": len(campaign_data.pages),
            "form_count": len(campaign_data.forms),
            "product_count": len(campaign_data.products),
            "campaign_type": campaign_data.type,
            "structure_issues": [],
            "structure_score": 0
        }
        
        # Check for common structural issues
        if analysis["page_count"] == 0:
            analysis["structure_issues"].append("No pages found in campaign")
        elif analysis["page_count"] > 15 and campaign_data.type == "funnel":
            analysis["structure_issues"].append("Funnel has too many pages - may cause user drop-off")
        elif analysis["page_count"] > 50 and campaign_data.type == "website":
            analysis["structure_issues"].append("Website has many pages - consider navigation optimization")
        
        if analysis["form_count"] == 0 and campaign_data.type == "funnel":
            analysis["structure_issues"].append("No forms found - missing lead capture")
        elif analysis["form_count"] > 3 and campaign_data.type == "funnel":
            analysis["structure_issues"].append("Too many forms in funnel - may cause decision fatigue")
        
        # E-commerce specific checks
        if campaign_data.type == "website" and analysis["product_count"] > 0:
            if analysis["product_count"] < 5:
                analysis["structure_issues"].append("Limited product catalog - consider expanding")
            elif analysis["product_count"] > 1000:
                analysis["structure_issues"].append("Large product catalog - ensure good search/filtering")
        
        # Calculate structure score (0-100)
        score = 100
        score -= len(analysis["structure_issues"]) * 12
        
        # Bonus points for good structure
        if campaign_data.type == "funnel" and 3 <= analysis["page_count"] <= 7:
            score += 10  # Good funnel length
        if campaign_data.type == "website" and 5 <= analysis["page_count"] <= 20:
            score += 10  # Good website size
        if analysis["form_count"] > 0:
            score += 10  # Has lead capture
        
        analysis["structure_score"] = max(0, min(100, score))
        
        return analysis
    
    async def _analyze_performance(self, campaign_data: SimvolyCampaignData) -> Dict[str, Any]:
        """Analyze campaign performance metrics"""
        analytics = campaign_data.analytics
        
        analysis = {
            "visitors": analytics.get("visitors", 0),
            "page_views": analytics.get("page_views", 0),
            "conversions": analytics.get("conversions", 0),
            "conversion_rate": 0,
            "bounce_rate": analytics.get("bounce_rate", 0),
            "avg_session_duration": analytics.get("avg_session_duration", 0),
            "performance_issues": [],
            "performance_score": 0
        }
        
        # Calculate conversion rate
        if analysis["visitors"] > 0:
            analysis["conversion_rate"] = (analysis["conversions"] / analysis["visitors"]) * 100
        
        # Identify performance issues
        if analysis["conversion_rate"] < 1:
            analysis["performance_issues"].append("Very low conversion rate (< 1%)")
        elif analysis["conversion_rate"] < 2:
            analysis["performance_issues"].append("Low conversion rate (< 2%)")
        
        if analysis["bounce_rate"] > 70:
            analysis["performance_issues"].append("High bounce rate (> 70%)")
        elif analysis["bounce_rate"] > 50:
            analysis["performance_issues"].append("Moderate bounce rate (> 50%)")
        
        if analysis["avg_session_duration"] < 30:
            analysis["performance_issues"].append("Very short session duration (< 30s)")
        elif analysis["avg_session_duration"] < 60:
            analysis["performance_issues"].append("Short session duration (< 1 min)")
        
        if analysis["visitors"] < 50:
            analysis["performance_issues"].append("Low traffic volume")
        
        # Calculate performance score
        score = 50  # Base score
        
        # Conversion rate scoring
        if analysis["conversion_rate"] > 10:
            score += 30
        elif analysis["conversion_rate"] > 5:
            score += 25
        elif analysis["conversion_rate"] > 2:
            score += 15
        elif analysis["conversion_rate"] > 1:
            score += 10
        
        # Engagement scoring
        if analysis["bounce_rate"] < 30:
            score += 15
        elif analysis["bounce_rate"] < 50:
            score += 10
        elif analysis["bounce_rate"] < 70:
            score += 5
        
        if analysis["avg_session_duration"] > 180:
            score += 10
        elif analysis["avg_session_duration"] > 120:
            score += 8
        elif analysis["avg_session_duration"] > 60:
            score += 5
        
        score -= len(analysis["performance_issues"]) * 8
        analysis["performance_score"] = max(0, min(100, score))
        
        return analysis
    
    async def _analyze_conversions(self, campaign_data: SimvolyCampaignData) -> Dict[str, Any]:
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
                "form_name": form.get("name", "Unnamed Form"),
                "field_count": len(form.get("fields", [])),
                "issues": []
            }
            
            if form_analysis["field_count"] > 7:
                form_analysis["issues"].append("Too many form fields - may reduce conversions")
            elif form_analysis["field_count"] < 2:
                form_analysis["issues"].append("Very few form fields - may not capture enough info")
            
            # Check for required fields
            fields = form.get("fields", [])
            required_fields = [f for f in fields if f.get("required", False)]
            
            if len(required_fields) > 5:
                form_analysis["issues"].append("Too many required fields")
            
            # Check for phone/address requirements
            phone_required = any(f.get("type") == "phone" and f.get("required") for f in fields)
            address_required = any(f.get("type") == "address" and f.get("required") for f in fields)
            
            if phone_required:
                form_analysis["issues"].append("Required phone field may reduce conversions")
            if address_required:
                form_analysis["issues"].append("Required address field may reduce conversions")
            
            analysis["form_analysis"].append(form_analysis)
        
        # Analyze pages for conversion elements
        for page in campaign_data.pages:
            page_analysis = {
                "page_id": page.get("id"),
                "page_name": page.get("name", "Unnamed Page"),
                "page_type": page.get("type", "unknown"),
                "issues": []
            }
            
            # Check for landing page best practices
            if page.get("type") == "landing":
                if not page.get("has_headline"):
                    page_analysis["issues"].append("Missing compelling headline")
                if not page.get("has_cta"):
                    page_analysis["issues"].append("Missing clear call-to-action")
                if not page.get("has_social_proof"):
                    page_analysis["issues"].append("Missing social proof/testimonials")
            
            analysis["page_analysis"].append(page_analysis)
        
        # Calculate conversion score
        total_form_issues = sum(len(fa["issues"]) for fa in analysis["form_analysis"])
        total_page_issues = sum(len(pa["issues"]) for pa in analysis["page_analysis"])
        
        score = 100
        score -= total_form_issues * 8
        score -= total_page_issues * 6
        
        # Bonus for having forms
        if len(campaign_data.forms) > 0:
            score += 15
        
        analysis["conversion_score"] = max(0, min(100, score))
        
        return analysis
    
    async def _analyze_ecommerce(self, campaign_data: SimvolyCampaignData) -> Dict[str, Any]:
        """Analyze e-commerce specific features"""
        analysis = {
            "product_count": len(campaign_data.products),
            "product_analysis": [],
            "ecommerce_issues": [],
            "ecommerce_score": 0
        }
        
        # Analyze product catalog
        if analysis["product_count"] == 0:
            analysis["ecommerce_issues"].append("No products found")
            analysis["ecommerce_score"] = 0
            return analysis
        
        # Analyze individual products
        for product in campaign_data.products[:10]:  # Analyze first 10 products
            product_analysis = {
                "product_id": product.get("id"),
                "product_name": product.get("name", "Unnamed Product"),
                "has_images": len(product.get("images", [])) > 0,
                "has_description": bool(product.get("description")),
                "has_price": bool(product.get("price")),
                "issues": []
            }
            
            if not product_analysis["has_images"]:
                product_analysis["issues"].append("Missing product images")
            if not product_analysis["has_description"]:
                product_analysis["issues"].append("Missing product description")
            if not product_analysis["has_price"]:
                product_analysis["issues"].append("Missing product price")
            
            analysis["product_analysis"].append(product_analysis)
        
        # Calculate e-commerce score
        score = 70  # Base score for having products
        
        total_product_issues = sum(len(pa["issues"]) for pa in analysis["product_analysis"])
        products_analyzed = len(analysis["product_analysis"])
        
        if products_analyzed > 0:
            avg_issues_per_product = total_product_issues / products_analyzed
            score -= avg_issues_per_product * 10
        
        analysis["ecommerce_score"] = max(0, min(100, score))
        
        return analysis
    
    def _calculate_overall_score(self, structure: Dict, performance: Dict, conversion: Dict) -> int:
        """Calculate overall campaign score"""
        weights = {
            "structure": 0.25,
            "performance": 0.45,
            "conversion": 0.30
        }
        
        weighted_score = (
            structure["structure_score"] * weights["structure"] +
            performance["performance_score"] * weights["performance"] +
            conversion["conversion_score"] * weights["conversion"]
        )
        
        return int(weighted_score)
    
    def _generate_recommendations(
        self, 
        structure: Dict, 
        performance: Dict, 
        conversion: Dict, 
        campaign_data: SimvolyCampaignData
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Structure recommendations
        if structure["structure_score"] < 70:
            recommendations.append({
                "category": "Structure",
                "priority": "high",
                "title": "Optimize Campaign Structure",
                "description": "Simplify navigation and reduce complexity",
                "impact": "Medium"
            })
        
        # Performance recommendations
        if performance["conversion_rate"] < 2:
            recommendations.append({
                "category": "Performance",
                "priority": "high",
                "title": "Improve Conversion Rate",
                "description": "Optimize landing pages and forms to increase conversions",
                "impact": "High"
            })
        
        if performance["bounce_rate"] > 50:
            recommendations.append({
                "category": "Performance",
                "priority": "medium",
                "title": "Reduce Bounce Rate",
                "description": "Improve page loading speed and content relevance",
                "impact": "Medium"
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
        
        # E-commerce recommendations
        if campaign_data.products and len(campaign_data.products) > 0:
            recommendations.append({
                "category": "E-commerce",
                "priority": "medium",
                "title": "Enhance Product Presentation",
                "description": "Improve product images, descriptions, and pricing display",
                "impact": "Medium"
            })
        
        return recommendations