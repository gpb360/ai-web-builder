"""
Component generation API routes - Core MVP functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from database.connection import get_db
from auth.dependencies import get_current_user
from database.models import User
from ai.simple_service import SimpleAIService

logger = logging.getLogger(__name__)
router = APIRouter()

class ComponentRequest(BaseModel):
    """Request model for component generation"""
    description: str = Field(..., min_length=10, max_length=1000, description="Natural language description of the component")
    component_type: str = Field(default="react", description="Type of component (react, html, vue)")
    complexity: int = Field(default=3, ge=1, le=5, description="Complexity level 1-5")
    style_preferences: Optional[Dict[str, str]] = Field(default=None, description="Style preferences (colors, layout, etc.)")

class ComponentResponse(BaseModel):
    """Response model for generated component"""
    success: bool
    component_code: str
    component_type: str
    estimated_cost: float
    generation_time: float
    model_used: str
    suggestions: Optional[List[str]] = None

class AnalysisRequest(BaseModel):
    """Request model for component analysis"""
    component_code: str = Field(..., min_length=50, description="Component code to analyze")
    focus_areas: Optional[List[str]] = Field(default=None, description="Specific areas to focus on (accessibility, performance, etc.)")

@router.post("/generate", response_model=ComponentResponse)
async def generate_component(
    request: ComponentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a new component based on natural language description
    
    This is the core MVP functionality - turn user descriptions into production-ready components
    """
    try:
        ai_service = SimpleAIService(db)
        
        logger.info(f"Generating component for user {current_user.id}: {request.description[:50]}...")
        
        # Generate component
        response = await ai_service.generate_component(
            user=current_user,
            description=request.description,
            component_type=request.component_type,
            complexity=request.complexity
        )
        
        # Create suggestions based on component type and complexity
        suggestions = _generate_usage_suggestions(request.component_type, request.complexity)
        
        return ComponentResponse(
            success=True,
            component_code=response.content,
            component_type=request.component_type,
            estimated_cost=response.cost,
            generation_time=response.processing_time or 0,
            model_used=response.model_used.value,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Component generation failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Component generation failed: {str(e)}"
        )

@router.post("/analyze")
async def analyze_component(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze existing component code and provide improvement suggestions
    """
    try:
        ai_service = SimpleAIService(db)
        
        logger.info(f"Analyzing component for user {current_user.id}")
        
        # Analyze component
        response = await ai_service.analyze_existing_component(
            user=current_user,
            component_code=request.component_code
        )
        
        return {
            "success": True,
            "analysis": response.content,
            "estimated_cost": response.cost,
            "analysis_time": response.processing_time or 0,
            "model_used": response.model_used.value,
            "quality_score": response.quality_score
        }
        
    except Exception as e:
        logger.error(f"Component analysis failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Component analysis failed: {str(e)}"
        )

@router.get("/examples")
async def get_component_examples(
    component_type: str = "react",
    complexity: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    Get example component descriptions and generated results for inspiration
    """
    examples = {
        "react": {
            1: [
                {"description": "Simple button with text", "use_case": "Basic interactions"},
                {"description": "Loading spinner component", "use_case": "User feedback"},
                {"description": "Text input with label", "use_case": "Form building"}
            ],
            2: [
                {"description": "Button with icon and hover effects", "use_case": "Enhanced UX"},
                {"description": "Card component with image and text", "use_case": "Content display"},
                {"description": "Toggle switch component", "use_case": "Settings UI"}
            ],
            3: [
                {"description": "Modal dialog with backdrop and animations", "use_case": "User interactions"},
                {"description": "Responsive navigation menu", "use_case": "Site navigation"},
                {"description": "Form with validation and error states", "use_case": "Data collection"}
            ],
            4: [
                {"description": "Data table with sorting and filtering", "use_case": "Data management"},
                {"description": "Multi-step wizard component", "use_case": "Complex workflows"},
                {"description": "Drag and drop file uploader", "use_case": "File management"}
            ],
            5: [
                {"description": "Real-time chat interface with emoji picker", "use_case": "Communication"},
                {"description": "Advanced dashboard with charts and widgets", "use_case": "Analytics"},
                {"description": "Code editor with syntax highlighting", "use_case": "Developer tools"}
            ]
        }
    }
    
    component_examples = examples.get(component_type, examples["react"])
    complexity_examples = component_examples.get(complexity, component_examples[3])
    
    return {
        "component_type": component_type,
        "complexity": complexity,
        "examples": complexity_examples,
        "tips": _get_complexity_tips(complexity)
    }

@router.get("/cost-estimate")
async def estimate_generation_cost(
    description: str,
    component_type: str = "react",
    complexity: int = 3,
    current_user: User = Depends(get_current_user)
):
    """
    Estimate cost before generating component
    """
    try:
        # Simple cost estimation based on description length and complexity
        description_length = len(description)
        
        # Base cost calculation (rough estimation)
        base_tokens = description_length * 1.5  # Input tokens
        output_multiplier = {
            1: 1.5,  # Simple components
            2: 2.0,  # Basic components  
            3: 2.5,  # Standard components
            4: 3.5,  # Complex components
            5: 5.0   # Advanced components
        }
        
        estimated_output_tokens = base_tokens * output_multiplier.get(complexity, 2.5)
        
        # Use Gemini Flash pricing (cheapest)
        from ai.models import MODEL_COSTS, ModelType
        model_costs = MODEL_COSTS[ModelType.GEMINI_FLASH]
        estimated_cost = model_costs.calculate_cost(
            int(base_tokens),
            int(estimated_output_tokens)
        )
        
        return {
            "description_length": description_length,
            "estimated_input_tokens": int(base_tokens),
            "estimated_output_tokens": int(estimated_output_tokens),
            "estimated_cost": estimated_cost,
            "component_type": component_type,
            "complexity": complexity,
            "model": "gemini-1.5-flash"
        }
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost estimation failed: {str(e)}"
        )

def _generate_usage_suggestions(component_type: str, complexity: int) -> List[str]:
    """Generate helpful suggestions for using the generated component"""
    base_suggestions = [
        "Test the component in different screen sizes",
        "Add unit tests for component behavior",
        "Consider accessibility requirements"
    ]
    
    if component_type == "react":
        base_suggestions.extend([
            "Add TypeScript types for better development experience",
            "Consider using React.memo for performance optimization",
            "Add prop validation with PropTypes or TypeScript"
        ])
    
    if complexity >= 4:
        base_suggestions.extend([
            "Break down complex components into smaller parts",
            "Add error boundaries for better error handling",
            "Consider performance optimization with useMemo/useCallback"
        ])
    
    return base_suggestions

def _get_complexity_tips(complexity: int) -> List[str]:
    """Get tips for different complexity levels"""
    tips = {
        1: [
            "Keep it simple - focus on core functionality",
            "Minimal styling, basic structure",
            "Perfect for prototyping and MVPs"
        ],
        2: [
            "Add basic interactivity and hover states",
            "Include proper spacing and typography",
            "Good for standard UI elements"
        ],
        3: [
            "Responsive design and good UX patterns",
            "Multiple states (loading, error, success)",
            "Production-ready components"
        ],
        4: [
            "Advanced state management and complex logic",
            "Multiple interaction patterns",
            "Enterprise-level components"
        ],
        5: [
            "Sophisticated features and optimization",
            "Advanced patterns and performance considerations",
            "Highly specialized components"
        ]
    }
    
    return tips.get(complexity, tips[3])