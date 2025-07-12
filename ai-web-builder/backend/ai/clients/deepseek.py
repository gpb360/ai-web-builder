"""
DeepSeek V3 API client implementation
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

class DeepSeekError(Exception):
    """DeepSeek API specific errors"""
    pass

class DeepSeekClient:
    """
    DeepSeek V3 API client for ultra-low cost code generation and analysis
    """
    
    BASE_URL = "https://api.deepseek.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'DEEPSEEK_API_KEY', None)
        if not self.api_key:
            raise ValueError("DeepSeek API key is required")
        
        self.session = None
        self._rate_limit_remaining = 1000
        self._rate_limit_reset_time = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AI-Web-Builder/1.0"
            },
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
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AIResponse:
        """
        Generate completion using DeepSeek V3
        
        Args:
            request: AI request object
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
            
            # Make API call
            async with self.session.post(f"{self.BASE_URL}/chat/completions", json=payload) as response:
                
                # Update rate limit info
                self._update_rate_limits(response.headers)
                
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data, request, start_time)
                
                elif response.status == 429:
                    # Rate limit exceeded
                    error_data = await response.json()
                    retry_after = int(response.headers.get('Retry-After', 60))
                    raise DeepSeekError(f"Rate limit exceeded. Retry after {retry_after} seconds")
                
                elif response.status == 401:
                    raise DeepSeekError("Invalid API key")
                
                elif response.status == 400:
                    error_data = await response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Bad request')
                    raise DeepSeekError(f"Bad request: {error_msg}")
                
                else:
                    error_text = await response.text()
                    raise DeepSeekError(f"API error {response.status}: {error_text}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"DeepSeek API client error: {e}")
            raise DeepSeekError(f"Network error: {e}")
        
        except asyncio.TimeoutError:
            logger.error("DeepSeek API timeout")
            raise DeepSeekError("Request timeout")
        
        except Exception as e:
            logger.error(f"Unexpected error in DeepSeek API call: {e}")
            raise DeepSeekError(f"Unexpected error: {e}")
    
    def _prepare_payload(
        self, 
        request: AIRequest, 
        temperature: float, 
        max_tokens: Optional[int]
    ) -> Dict[str, Any]:
        """Prepare API request payload"""
        
        # Create system prompt based on task type
        system_prompt = self._get_system_prompt(request.task_type)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.content}
        ]
        
        # Calculate appropriate max_tokens if not specified
        if max_tokens is None:
            input_tokens = len(request.content.split()) * 1.3
            max_tokens = min(4000, int(input_tokens * 2))  # Reasonable default
        
        payload = {
            "model": "deepseek-coder",  # DeepSeek's code model
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stream": False
        }
        
        return payload
    
    def _get_system_prompt(self, task_type: str) -> str:
        """Get optimized system prompt for task type"""
        
        prompts = {
            "code_generation": """You are an expert React and TypeScript developer. Generate clean, production-ready code that follows best practices. Always include proper TypeScript types, use functional components with hooks, and ensure code is accessible and performant.""",
            
            "component_generation": """You are an expert frontend developer specializing in React components. Create reusable, well-structured components with proper TypeScript types, Tailwind CSS styling, and accessibility features. Focus on clean code and modern React patterns.""",
            
            "analysis": """You are a senior technical analyst. Provide clear, actionable insights with specific recommendations. Structure your analysis with key findings, implications, and next steps.""",
            
            "optimization": """You are a performance and code optimization expert. Identify bottlenecks, suggest improvements, and provide specific implementation guidance. Focus on measurable performance gains.""",
            
            "content_writing": """You are a skilled technical writer. Create clear, engaging content that is well-structured and easy to understand. Use proper formatting and maintain a professional tone.""",
            
            "campaign_analysis": """You are a digital marketing expert specializing in campaign optimization. Analyze performance data, identify improvement opportunities, and provide actionable recommendations with expected impact."""
        }
        
        return prompts.get(task_type, 
            "You are a helpful AI assistant. Provide accurate, helpful responses based on the user's request.")
    
    def _parse_response(
        self, 
        data: Dict[str, Any], 
        request: AIRequest, 
        start_time: datetime
    ) -> AIResponse:
        """Parse DeepSeek API response into AIResponse"""
        
        try:
            # Extract content
            choice = data["choices"][0]
            content = choice["message"]["content"]
            
            # Extract usage info
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Calculate cost
            from ..models import MODEL_COSTS
            model_costs = MODEL_COSTS[ModelType.DEEPSEEK_V3]
            cost = model_costs.calculate_cost(input_tokens, output_tokens)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Assess quality (basic heuristics)
            quality_score = self._assess_response_quality(content, request.task_type)
            
            return AIResponse(
                content=content,
                model_used=ModelType.DEEPSEEK_V3,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                quality_score=quality_score,
                processing_time=processing_time,
                timestamp=datetime.utcnow()
            )
            
        except KeyError as e:
            logger.error(f"Unexpected response format from DeepSeek: {e}")
            raise DeepSeekError(f"Unexpected response format: {e}")
    
    def _assess_response_quality(self, content: str, task_type: str) -> float:
        """Basic quality assessment of the response"""
        
        if not content or len(content.strip()) < 10:
            return 0.1
        
        quality_score = 0.7  # Base score
        
        # Task-specific quality checks
        if task_type in ["code_generation", "component_generation"]:
            # Check for code patterns
            if "import" in content or "export" in content:
                quality_score += 0.1
            if "function" in content or "const" in content or "=>" in content:
                quality_score += 0.1
            if "{" in content and "}" in content:
                quality_score += 0.05
            
        elif task_type == "analysis":
            # Check for analysis structure
            if any(word in content.lower() for word in ["findings", "recommendation", "analysis"]):
                quality_score += 0.1
            if content.count('\n') > 3:  # Multi-paragraph
                quality_score += 0.05
        
        # General quality indicators
        if len(content) > 100:
            quality_score += 0.05
        if len(content) > 500:
            quality_score += 0.05
        
        return min(1.0, quality_score)
    
    async def _check_rate_limits(self):
        """Check and handle rate limits"""
        if self._rate_limit_remaining <= 5:
            if self._rate_limit_reset_time and datetime.utcnow() < self._rate_limit_reset_time:
                wait_time = (self._rate_limit_reset_time - datetime.utcnow()).total_seconds()
                if wait_time > 0:
                    logger.warning(f"Rate limit approaching, waiting {wait_time:.1f} seconds")
                    await asyncio.sleep(min(wait_time, 60))  # Cap wait time at 60 seconds
    
    def _update_rate_limits(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        try:
            self._rate_limit_remaining = int(headers.get('x-ratelimit-remaining', 1000))
            
            reset_timestamp = headers.get('x-ratelimit-reset')
            if reset_timestamp:
                self._rate_limit_reset_time = datetime.fromtimestamp(int(reset_timestamp))
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection and return status"""
        try:
            test_request = AIRequest(
                task_type="content_writing",
                complexity=1,
                content="Say hello",
                user_tier="free"
            )
            
            response = await self.generate_completion(test_request, temperature=0.1, max_tokens=50)
            
            return {
                "success": True,
                "model": "deepseek-coder",
                "response_time": response.processing_time,
                "cost": response.cost,
                "rate_limit_remaining": self._rate_limit_remaining
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def estimate_cost(self, content: str, task_type: str) -> Dict[str, Any]:
        """Estimate cost for a request without making the API call"""
        
        # Estimate token counts
        input_tokens = len(content.split()) * 1.3  # Rough estimation
        
        # Output estimation based on task type
        output_multipliers = {
            "code_generation": 2.5,
            "component_generation": 3.0,
            "content_writing": 2.0,
            "analysis": 1.5,
            "optimization": 1.8,
            "campaign_analysis": 2.2
        }
        
        output_multiplier = output_multipliers.get(task_type, 1.5)
        output_tokens = input_tokens * output_multiplier
        
        # Calculate cost
        from ..models import MODEL_COSTS
        model_costs = MODEL_COSTS[ModelType.DEEPSEEK_V3]
        cost = model_costs.calculate_cost(int(input_tokens), int(output_tokens))
        
        return {
            "estimated_input_tokens": int(input_tokens),
            "estimated_output_tokens": int(output_tokens),
            "estimated_cost": cost,
            "model": "deepseek-v3"
        }