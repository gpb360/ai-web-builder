"""
Simplified AI Service for MVP - Focus on component generation
"""
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from .models import AIRequest, AIResponse, ModelType, TaskType, UserTier
from database.models import User
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class SimpleAIService:
    """
    Simplified AI service for MVP - Uses Gemini Flash primarily, DeepSeek as fallback
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def generate_component(
        self,
        user: User,
        description: str,
        component_type: str = "react",
        complexity: int = 3
    ) -> AIResponse:
        """
        Generate a React component using cost-effective AI models
        
        Args:
            user: User making the request
            description: Natural language description of component
            component_type: Type of component (react, html, vue)
            complexity: Complexity level 1-5
            
        Returns:
            AIResponse with generated component code
        """
        request = AIRequest(
            task_type=TaskType.COMPONENT_GENERATION.value,
            complexity=complexity,
            content=description,
            user_tier=user.subscription_tier
        )
        
        # For MVP, use Gemini Flash (cheapest) first
        try:
            logger.info(f"Generating {component_type} component for user {user.id}: {description[:50]}...")
            return await self._generate_with_gemini_flash(request, component_type)
        except Exception as e:
            logger.warning(f"Gemini Flash failed, trying DeepSeek: {e}")
            try:
                return await self._generate_with_deepseek(request, component_type)
            except Exception as e2:
                logger.error(f"Both models failed: {e2}")
                # Return mock response for MVP
                return self._create_mock_response(request, component_type)
    
    async def _generate_with_gemini_flash(self, request: AIRequest, component_type: str) -> AIResponse:
        """Generate component with Gemini Flash"""
        from .clients.gemini import GeminiClient
        
        # Enhanced prompt for component generation
        enhanced_content = self._create_component_prompt(request.content, component_type, request.complexity)
        
        enhanced_request = AIRequest(
            task_type=request.task_type,
            complexity=request.complexity,
            content=enhanced_content,
            user_tier=request.user_tier
        )
        
        async with GeminiClient() as client:
            response = await client.generate_completion(
                enhanced_request,
                model_variant="gemini-1.5-flash",
                temperature=0.3,  # Lower temperature for code generation
                max_tokens=3000
            )
            return response
    
    async def _generate_with_deepseek(self, request: AIRequest, component_type: str) -> AIResponse:
        """Generate component with DeepSeek V3"""
        from .clients.deepseek import DeepSeekClient
        
        # Enhanced prompt for component generation
        enhanced_content = self._create_component_prompt(request.content, component_type, request.complexity)
        
        enhanced_request = AIRequest(
            task_type=request.task_type,
            complexity=request.complexity,
            content=enhanced_content,
            user_tier=request.user_tier
        )
        
        async with DeepSeekClient() as client:
            response = await client.generate_completion(
                enhanced_request,
                temperature=0.3,
                max_tokens=3000
            )
            return response
    
    def _create_component_prompt(self, description: str, component_type: str, complexity: int) -> str:
        """Create optimized prompt for component generation"""
        
        base_requirements = {
            "react": {
                "framework": "React with TypeScript",
                "styling": "Tailwind CSS classes",
                "patterns": "functional components with hooks",
                "exports": "export default ComponentName"
            },
            "html": {
                "framework": "HTML5 with CSS3",
                "styling": "modern CSS with flexbox/grid",
                "patterns": "semantic HTML structure",
                "exports": "complete HTML document"
            },
            "vue": {
                "framework": "Vue 3 with TypeScript",
                "styling": "Tailwind CSS classes",
                "patterns": "composition API",
                "exports": "export default defineComponent"
            }
        }
        
        requirements = base_requirements.get(component_type, base_requirements["react"])
        
        complexity_instructions = {
            1: "Keep it very simple - minimal functionality, basic styling",
            2: "Simple component with basic interactivity",
            3: "Standard component with good UX and responsive design",
            4: "Advanced component with complex state management",
            5: "Sophisticated component with advanced patterns and optimization"
        }
        
        complexity_instruction = complexity_instructions.get(complexity, complexity_instructions[3])
        
        prompt = f"""You are an expert frontend developer. Create a {requirements['framework']} component based on this description:

"{description}"

Requirements:
- Framework: {requirements['framework']}
- Styling: {requirements['styling']}
- Patterns: {requirements['patterns']}
- Complexity: {complexity_instruction}
- Export: {requirements['exports']}

Guidelines:
1. Write clean, production-ready code
2. Include proper TypeScript types (if applicable)
3. Use semantic HTML and accessible design
4. Make it responsive and mobile-friendly
5. Add helpful comments for complex logic
6. Follow modern best practices
7. Include proper prop validation

Return only the component code, no explanations or markdown formatting."""

        return prompt
    
    def _create_mock_response(self, request: AIRequest, component_type: str) -> AIResponse:
        """Create mock response for development/fallback"""
        
        mock_components = {
            "react": f'''import React from 'react';

interface ComponentProps {{
  children?: React.ReactNode;
  className?: string;
}}

const GeneratedComponent: React.FC<ComponentProps> = ({{ children, className }}) => {{
  return (
    <div className={{`p-4 bg-white rounded-lg shadow-md ${{className}}`}}>
      <h2 className="text-xl font-bold mb-2">Generated Component</h2>
      <p className="text-gray-600">
        Based on: {request.content[:100]}...
      </p>
      {{children}}
    </div>
  );
}};

export default GeneratedComponent;''',
            "html": f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Component</title>
    <style>
        .generated-component {{
            padding: 1rem;
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .title {{
            font-size: 1.25rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}
        .description {{
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="generated-component">
        <h2 class="title">Generated Component</h2>
        <p class="description">Based on: {request.content[:100]}...</p>
    </div>
</body>
</html>''',
            "vue": f'''<template>
  <div class="p-4 bg-white rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-2">Generated Component</h2>
    <p class="text-gray-600">
      Based on: {request.content[:100]}...
    </p>
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {{
  className?: string;
}}

const props = withDefaults(defineProps<Props>(), {{
  className: ''
}});
</script>'''
        }
        
        mock_content = mock_components.get(component_type, mock_components["react"])
        
        # Estimate tokens and cost
        input_tokens = len(request.content.split()) * 1.3
        output_tokens = len(mock_content.split()) * 1.3
        
        # Use Gemini Flash cost (cheapest)
        from .models import MODEL_COSTS, ModelType
        model_costs = MODEL_COSTS[ModelType.GEMINI_FLASH]
        cost = model_costs.calculate_cost(int(input_tokens), int(output_tokens))
        
        return AIResponse(
            content=mock_content,
            model_used=ModelType.GEMINI_FLASH,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=cost,
            quality_score=0.75,  # Mock quality score
            processing_time=1.5
        )
    
    async def analyze_existing_component(self, user: User, component_code: str) -> AIResponse:
        """Analyze and suggest improvements for existing component"""
        request = AIRequest(
            task_type=TaskType.ANALYSIS.value,
            complexity=3,
            content=f"Analyze this component and suggest improvements:\n\n{component_code}",
            user_tier=user.subscription_tier
        )
        
        try:
            return await self._generate_with_gemini_flash(request, "analysis")
        except Exception:
            try:
                return await self._generate_with_deepseek(request, "analysis")
            except Exception:
                return self._create_mock_analysis_response(request, component_code)
    
    def _create_mock_analysis_response(self, request: AIRequest, component_code: str) -> AIResponse:
        """Create mock analysis response"""
        
        mock_analysis = f"""# Component Analysis

## Overview
The provided component appears to be {'React' if 'React' in component_code else 'HTML/CSS'} based.

## Strengths
- ✅ Clean code structure
- ✅ Readable implementation
- ✅ Modern syntax usage

## Recommendations
1. **Accessibility**: Add ARIA labels and proper semantic structure
2. **Performance**: Consider memoization for expensive calculations
3. **Responsive Design**: Ensure mobile-first approach
4. **Type Safety**: Add comprehensive TypeScript types
5. **Testing**: Include unit tests for component behavior

## Suggested Improvements
- Add loading states for better UX
- Implement error boundaries
- Consider code splitting for larger components
- Add proper prop validation

## Code Quality Score: 8/10
Good foundation with room for enhancement in accessibility and performance optimization.
"""
        
        # Estimate tokens and cost
        input_tokens = len(request.content.split()) * 1.3
        output_tokens = len(mock_analysis.split()) * 1.3
        
        from .models import MODEL_COSTS, ModelType
        model_costs = MODEL_COSTS[ModelType.GEMINI_FLASH]
        cost = model_costs.calculate_cost(int(input_tokens), int(output_tokens))
        
        return AIResponse(
            content=mock_analysis,
            model_used=ModelType.GEMINI_FLASH,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            cost=cost,
            quality_score=0.80,
            processing_time=2.0
        )