"""
AI Model definitions and cost structures
"""
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

class AIProvider(Enum):
    """Supported AI providers"""
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    CLAUDE = "claude"
    OPENAI = "openai"

class ModelType(Enum):
    """AI model types by capability"""
    DEEPSEEK_V3 = "deepseek-v3"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"
    CLAUDE_SONNET = "claude-3.5-sonnet"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4_VISION = "gpt-4-vision"

@dataclass
class ModelCosts:
    """Cost structure for AI models (per 1M tokens)"""
    input_cost: float  # Cost per 1M input tokens
    output_cost: float  # Cost per 1M output tokens
    image_cost: Optional[float] = None  # Cost per image (for vision models)
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, images: int = 0) -> float:
        """Calculate total cost for a request"""
        input_cost = (input_tokens / 1_000_000) * self.input_cost
        output_cost = (output_tokens / 1_000_000) * self.output_cost
        image_cost = (images * self.image_cost) if self.image_cost and images > 0 else 0
        return input_cost + output_cost + image_cost

# Model cost configurations (updated prices as of December 2024)
MODEL_COSTS: Dict[ModelType, ModelCosts] = {
    # Ultra-low cost models
    ModelType.DEEPSEEK_V3: ModelCosts(
        input_cost=0.14,    # $0.14 per 1M tokens
        output_cost=0.28    # $0.28 per 1M tokens
    ),
    ModelType.GEMINI_FLASH: ModelCosts(
        input_cost=0.075,   # $0.075 per 1M tokens
        output_cost=0.30    # $0.30 per 1M tokens
    ),
    
    # Balanced performance models
    ModelType.GEMINI_PRO: ModelCosts(
        input_cost=1.25,    # $1.25 per 1M tokens
        output_cost=5.00    # $5.00 per 1M tokens
    ),
    ModelType.CLAUDE_SONNET: ModelCosts(
        input_cost=3.00,    # $3.00 per 1M tokens
        output_cost=15.00   # $15.00 per 1M tokens
    ),
    
    # Premium models
    ModelType.GPT4_TURBO: ModelCosts(
        input_cost=10.00,   # $10.00 per 1M tokens
        output_cost=30.00   # $30.00 per 1M tokens
    ),
    ModelType.GPT4_VISION: ModelCosts(
        input_cost=10.00,   # $10.00 per 1M tokens
        output_cost=30.00,  # $30.00 per 1M tokens
        image_cost=0.00765  # $0.00765 per image
    )
}

@dataclass
class AIRequest:
    """AI request structure"""
    task_type: str
    complexity: int  # 1-10 scale
    content: str
    user_tier: str
    max_cost: Optional[float] = None
    requires_vision: bool = False
    context_length: Optional[int] = None

@dataclass
class AIResponse:
    """AI response structure"""
    content: str
    model_used: ModelType
    input_tokens: int
    output_tokens: int
    cost: float
    quality_score: Optional[float] = None
    processing_time: Optional[float] = None
    timestamp: datetime = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class TaskType(Enum):
    """Different types of AI tasks"""
    CODE_GENERATION = "code_generation"
    CONTENT_WRITING = "content_writing"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    COMPONENT_GENERATION = "component_generation"
    CAMPAIGN_ANALYSIS = "campaign_analysis"
    DESIGN_REVIEW = "design_review"
    
class ComplexityLevel(Enum):
    """Task complexity levels"""
    SIMPLE = 1      # Basic tasks, single step
    EASY = 2        # Simple multi-step tasks
    MODERATE = 3    # Standard complexity
    MEDIUM = 4      # Requires some reasoning
    COMPLEX = 5     # Multi-step reasoning
    ADVANCED = 6    # Complex reasoning, multiple domains
    EXPERT = 7      # Expert-level tasks
    PREMIUM = 8     # Premium features, high quality needed
    ENTERPRISE = 9  # Enterprise-level complexity
    CRITICAL = 10   # Mission-critical, highest quality

class UserTier(Enum):
    """User subscription tiers"""
    FREE = "free"
    CREATOR = "creator"
    BUSINESS = "business" 
    AGENCY = "agency"

# Model capabilities matrix
MODEL_CAPABILITIES = {
    ModelType.DEEPSEEK_V3: {
        "strengths": ["code_generation", "analysis", "optimization"],
        "max_complexity": ComplexityLevel.MEDIUM.value,
        "context_limit": 32000,
        "quality_tier": "basic"
    },
    ModelType.GEMINI_FLASH: {
        "strengths": ["summarization", "translation", "content_writing"],
        "max_complexity": ComplexityLevel.MODERATE.value,
        "context_limit": 32000,
        "quality_tier": "good"
    },
    ModelType.GEMINI_PRO: {
        "strengths": ["analysis", "optimization", "component_generation"],
        "max_complexity": ComplexityLevel.ADVANCED.value,
        "context_limit": 128000,
        "quality_tier": "high"
    },
    ModelType.CLAUDE_SONNET: {
        "strengths": ["content_writing", "campaign_analysis", "design_review"],
        "max_complexity": ComplexityLevel.PREMIUM.value,
        "context_limit": 200000,
        "quality_tier": "premium"
    },
    ModelType.GPT4_TURBO: {
        "strengths": ["complex_reasoning", "expert_analysis", "enterprise_tasks"],
        "max_complexity": ComplexityLevel.CRITICAL.value,
        "context_limit": 128000,
        "quality_tier": "enterprise"
    },
    ModelType.GPT4_VISION: {
        "strengths": ["design_review", "image_analysis", "visual_tasks"],
        "max_complexity": ComplexityLevel.CRITICAL.value,
        "context_limit": 128000,
        "quality_tier": "enterprise",
        "vision_capable": True
    }
}