"""
Google Gemini API client implementation
"""
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ..models import AIRequest, AIResponse, ModelType
from config import settings

logger = logging.getLogger(__name__)

class GeminiError(Exception):
    """Gemini API specific errors"""
    pass

class GeminiClient:
    """
    Google Gemini API client for fast and cost-effective AI generation
    """
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'GEMINI_API_KEY', None)
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        self.session = None
        self._rate_limit_remaining = 60  # Gemini has 60 requests per minute
        self._rate_limit_reset_time = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_completion(
        self, 
        request: AIRequest,
        model_variant: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AIResponse:
        """
        Generate completion using Google Gemini
        
        Args:
            request: AI request object
            model_variant: Gemini model variant (flash or pro)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            AIResponse with generated content
        """
        start_time = datetime.utcnow()
        
        try:
            # Check rate limits
            await self._check_rate_limits()
            
            # Prepare the request
            payload = self._prepare_payload(request, temperature, max_tokens)
            
            # Construct URL with API key
            url = f"{self.BASE_URL}/models/{model_variant}:generateContent"
            params = {"key": self.api_key}
            
            # Make API call
            async with self.session.post(url, json=payload, params=params) as response:
                
                # Update rate limit info
                self._update_rate_limits(response.headers)
                
                if response.status == 200:
                    data = await response.json()
                    model_type = ModelType.GEMINI_FLASH if "flash" in model_variant else ModelType.GEMINI_PRO
                    return self._parse_response(data, request, model_type, start_time)
                
                elif response.status == 429:
                    # Rate limit exceeded
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise GeminiError(f"Rate limit exceeded. Retry after {retry_after} seconds")
                
                elif response.status == 401:
                    raise GeminiError("Invalid API key")
                
                elif response.status == 400:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Bad request')
                    raise GeminiError(f"Bad request: {error_msg}")
                
                else:
                    error_text = await response.text()
                    raise GeminiError(f"API error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Gemini API client error: {e}")
            raise GeminiError(f"Network error: {e}")
        
        except asyncio.TimeoutError:
            logger.error("Gemini API timeout")
            raise GeminiError("Request timeout")
        
        except Exception as e:
            logger.error(f"Unexpected error in Gemini API call: {e}")
            raise GeminiError(f"Unexpected error: {e}")
    
    def _prepare_payload(
        self, 
        request: AIRequest, 
        temperature: float, 
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Prepare API request payload"""
        
        # Create optimized prompt based on task type
        optimized_prompt = self._create_optimized_prompt(request)
        
        # Prepare contents
        contents = [
            {
                "parts": [
                    {"text": optimized_prompt}
                ]
            }
        ]
        
        # Generation config
        generation_config = {
            "temperature": temperature,
            "topP": 0.95,
            "topK": 40,
            "candidateCount": 1
        }
        
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens
        
        # Safety settings - moderate filtering for business use
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        payload = {
            "contents": contents,
            "generationConfig": generation_config,
            "safetySettings": safety_settings
        }
        
        return payload
    
    def _create_optimized_prompt(self, request: AIRequest) -> str:
        """Create optimized prompt combining system context with user request"""
        
        system_context = self._get_system_context(request.task_type)
        
        # Combine system context with user request
        optimized_prompt = f"""{system_context}

User Request: {request.content}

Please provide a comprehensive response that directly addresses the user's request while following the guidelines above."""
        
        return optimized_prompt
    
    def _get_system_context(self, task_type: str) -> str:
        """Get optimized system context for task type"""
        
        contexts = {
            "code_generation": """You are an expert React and TypeScript developer. When generating code:
- Use modern React functional components with hooks
- Include proper TypeScript types and interfaces  
- Use Tailwind CSS for styling
- Ensure code is accessible (ARIA labels, semantic HTML)
- Follow React best practices and performance optimization
- Include helpful comments for complex logic
- Make components reusable and well-structured""",
            
            "component_generation": """You are a senior frontend architect specializing in React component design. Create components that are:
- Reusable and composable
- Properly typed with TypeScript
- Styled with Tailwind CSS utility classes
- Accessible and keyboard navigable
- Responsive across all device sizes
- Performant and optimized
- Well-documented with clear prop interfaces""",
            
            "content_writing": """You are a professional content writer specializing in marketing and technical communication. Create content that is:
- Clear, engaging, and well-structured
- Optimized for the target audience
- Actionable and valuable
- Professional yet approachable
- SEO-friendly when appropriate
- Grammatically correct and well-formatted""",
            
            "analysis": """You are a senior business analyst with expertise in digital marketing and technical systems. Provide analysis that is:
- Data-driven and objective
- Structured with clear findings and recommendations
- Actionable with specific next steps
- Comprehensive yet concise
- Focused on measurable outcomes
- Supported by logical reasoning""",
            
            "optimization": """You are a performance optimization expert for web applications and marketing campaigns. Focus on:
- Identifying specific bottlenecks and inefficiencies
- Providing measurable improvement recommendations
- Considering both technical and business impact
- Prioritizing changes by effort vs. impact
- Including implementation guidance
- Quantifying expected improvements""",
            
            "campaign_analysis": """You are a digital marketing strategist with deep expertise in campaign optimization. Analyze campaigns by:
- Evaluating conversion funnel performance
- Identifying optimization opportunities
- Providing specific, actionable recommendations
- Estimating potential impact of changes
- Considering user experience and business goals
- Benchmarking against industry best practices""",
            
            "summarization": """You are an expert at distilling complex information into clear, actionable summaries. Create summaries that:
- Capture the most important points
- Maintain logical flow and structure
- Use clear, professional language
- Include key insights and implications
- Are appropriately detailed for the context
- Enable quick decision-making""",
            
            "translation": """You are a professional translator with expertise in technical and business content. Ensure translations are:
- Accurate and contextually appropriate
- Natural-sounding in the target language
- Culturally sensitive and appropriate
- Technically precise for specialized terms
- Consistent in terminology and style
- Professional and business-ready"""
        }
        
        return contexts.get(task_type, 
            "You are a helpful AI assistant. Provide accurate, professional responses that directly address the user's needs.")
    
    def _parse_response(
        self, 
        data: Dict[str, Any], 
        request: AIRequest, 
        model_type: ModelType,
        start_time: datetime
    ) -> AIResponse:
        """Parse Gemini API response into AIResponse"""
        
        try:
            # Extract content from candidates
            candidates = data.get("candidates", [])
            if not candidates:
                raise GeminiError("No candidates in response")
            
            candidate = candidates[0]
            content_parts = candidate.get("content", {}).get("parts", [])
            
            if not content_parts:
                raise GeminiError("No content parts in response")
            
            content = content_parts[0].get("text", "")
            
            if not content:
                raise GeminiError("Empty content in response")
            
            # Extract usage metadata if available
            usage_metadata = data.get("usageMetadata", {})
            input_tokens = usage_metadata.get("promptTokenCount", 0)
            output_tokens = usage_metadata.get("candidatesTokenCount", 0)
            
            # If usage not provided, estimate based on content
            if input_tokens == 0:
                input_tokens = len(request.content.split()) * 1.3
            if output_tokens == 0:
                output_tokens = len(content.split()) * 1.3
            
            # Calculate cost
            from ..models import MODEL_COSTS
            model_costs = MODEL_COSTS[model_type]
            cost = model_costs.calculate_cost(int(input_tokens), int(output_tokens))
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Assess quality
            quality_score = self._assess_response_quality(content, request.task_type)
            
            # Check for safety issues
            finish_reason = candidate.get("finishReason", "STOP")
            if finish_reason == "SAFETY":
                logger.warning("Response blocked by safety filters")
                quality_score *= 0.5  # Reduce quality score for safety blocks
            
            return AIResponse(
                content=content,
                model_used=model_type,
                input_tokens=int(input_tokens),
                output_tokens=int(output_tokens),
                cost=cost,
                quality_score=quality_score,
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
            
        except KeyError as e:
            logger.error(f"Unexpected response format from Gemini: {e}")
            raise GeminiError(f"Unexpected response format: {e}")
    
    def _assess_response_quality(self, content: str, task_type: str) -> float:
        """Assess response quality based on content and task type"""
        
        if not content or len(content.strip()) < 10:
            return 0.1
        
        quality_score = 0.75  # Base score for Gemini
        
        # Task-specific quality checks
        if task_type in ["code_generation", "component_generation"]:
            # Check for React/TypeScript patterns
            if any(pattern in content for pattern in ["import", "export", "function", "const", "=>"]):
                quality_score += 0.1
            if "TypeScript" in content or "interface" in content or ": " in content:
                quality_score += 0.05
            if "Tailwind" in content or "className" in content:
                quality_score += 0.05
            
        elif task_type == "content_writing":
            # Check for good structure
            if content.count('\n\n') > 1:  # Multiple paragraphs
                quality_score += 0.1
            if any(marker in content for marker in ["##", "**", "1.", "-"]):  # Formatting
                quality_score += 0.05
                
        elif task_type == "analysis":
            # Check for analytical structure
            if any(word in content.lower() for word in ["analysis", "findings", "recommendation", "conclusion"]):
                quality_score += 0.1
            if content.count('\n') > 5:  # Well-structured
                quality_score += 0.05
        
        # General quality indicators
        if len(content) > 200:
            quality_score += 0.05
        if len(content) > 1000:
            quality_score += 0.05
        
        # Check for completeness (not cut off)
        if content.endswith(('.', '!', '?', '```', '}', ');')):
            quality_score += 0.05
        
        return min(1.0, quality_score)
    
    async def _check_rate_limits(self):
        """Check and handle rate limits"""
        if self._rate_limit_remaining <= 3:
            if self._rate_limit_reset_time and datetime.utcnow() < self._rate_limit_reset_time:
                wait_time = (self._rate_limit_reset_time - datetime.utcnow()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Gemini rate limit approaching, waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(min(wait_time, 60))  # Cap wait time at 60 seconds
    
    def _update_rate_limits(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        try:
            # Gemini doesn't provide detailed rate limit headers
            # So we conservatively estimate
            self._rate_limit_remaining = max(0, self._rate_limit_remaining - 1)
            
            # Reset counter every minute
            if not self._rate_limit_reset_time or datetime.utcnow() >= self._rate_limit_reset_time:
                from datetime import timedelta
                self._rate_limit_reset_time = datetime.utcnow() + timedelta(minutes=1)
                self._rate_limit_remaining = 60
                
        except Exception as e:
            logger.warning(f"Failed to update rate limits: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status"""
        try:
            test_request = AIRequest(
                task_type="content_writing",
                complexity=1,
                content="Say hello and introduce yourself briefly",
                user_tier="free"
            )
            
            response = await self.generate_completion(
                test_request, 
                model_variant="gemini-1.5-flash",
                temperature=0.1
            )
            
            return {
                "success": True,
                "model": "gemini-1.5-flash",
                "response_time": response.processing_time,
                "cost": response.cost,
                "rate_limit_remaining": self._rate_limit_remaining,
                "content_preview": response.content[:100] + "..." if len(response.content) > 100 else response.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def estimate_cost(self, content: str, task_type: str, model_variant: str = "gemini-1.5-flash") -> Dict[str, Any]:
        """Estimate cost for a request without making the API call"""
        
        # Estimate token counts
        input_tokens = len(content.split()) * 1.3  # Rough estimation
        
        # Output estimation based on task type
        output_multipliers = {
            "code_generation": 2.5,
            "component_generation": 3.0,
            "content_writing": 2.0,
            "analysis": 1.8,
            "optimization": 1.6,
            "campaign_analysis": 2.2,
            "summarization": 0.8,
            "translation": 1.2
        }
        
        output_multiplier = output_multipliers.get(task_type, 1.5)
        output_tokens = input_tokens * output_multiplier
        
        # Calculate cost based on model variant
        model_type = ModelType.GEMINI_FLASH if "flash" in model_variant else ModelType.GEMINI_PRO
        
        from ..models import MODEL_COSTS
        model_costs = MODEL_COSTS[model_type]
        cost = model_costs.calculate_cost(int(input_tokens), int(output_tokens))
        
        return {
            "estimated_input_tokens": int(input_tokens),
            "estimated_output_tokens": int(output_tokens),
            "estimated_cost": cost,
            "model": model_variant,
            "model_type": model_type.value
        }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available Gemini models"""
        try:
            url = f"{self.BASE_URL}/models"
            params = {"key": self.api_key}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", [])
                    
                    # Filter for generative models
                    generative_models = [
                        {
                            "name": model.get("name", ""),
                            "display_name": model.get("displayName", ""),
                            "description": model.get("description", ""),
                            "supported_methods": model.get("supportedGenerationMethods", [])
                        }
                        for model in models
                        if "generateContent" in model.get("supportedGenerationMethods", [])
                    ]
                    
                    return generative_models
                else:
                    logger.error(f"Failed to list models: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []