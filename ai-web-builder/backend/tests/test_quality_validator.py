"""
Tests for AI Quality Validator
"""
import pytest
from ai.quality_validator import (
    AIQualityValidator, 
    ValidationLevel, 
    ValidationCategory,
    ValidationIssue,
    QualityScore
)

@pytest.fixture
def validator():
    return AIQualityValidator(ValidationLevel.STANDARD)

class TestReactValidation:
    """Test React component validation"""
    
    @pytest.mark.asyncio
    async def test_valid_react_component(self, validator):
        """Test validation of a well-formed React component"""
        code = """
        import React from 'react';
        
        interface ButtonProps {
            children: React.ReactNode;
            onClick?: () => void;
            disabled?: boolean;
        }
        
        const Button: React.FC<ButtonProps> = ({ children, onClick, disabled = false }) => {
            return (
                <button 
                    onClick={onClick}
                    disabled={disabled}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                    aria-label="Action button"
                >
                    {children}
                </button>
            );
        };
        
        export default Button;
        """
        
        result = await validator.validate_code(code, "react", 3)
        
        assert result.is_valid
        assert result.quality_score.overall >= 80
        assert result.quality_score.syntax >= 90
        assert result.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_react_missing_export(self, validator):
        """Test React component without export"""
        code = """
        import React from 'react';
        
        const Button = () => {
            return <button>Click me</button>;
        };
        """
        
        result = await validator.validate_code(code, "react", 2)
        
        assert not result.is_valid
        syntax_issues = [i for i in result.issues if i.category == ValidationCategory.SYNTAX]
        assert len(syntax_issues) > 0
        assert any("exported" in issue.message.lower() for issue in syntax_issues)
    
    @pytest.mark.asyncio
    async def test_react_security_issues(self, validator):
        """Test React component with security vulnerabilities"""
        code = """
        import React from 'react';
        
        const DangerousComponent = ({ htmlContent }) => {
            return (
                <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
            );
        };
        
        export default DangerousComponent;
        """
        
        result = await validator.validate_code(code, "react", 3)
        
        security_issues = [i for i in result.issues if i.category == ValidationCategory.SECURITY]
        assert len(security_issues) > 0
        assert any("dangerouslySetInnerHTML" in issue.message for issue in security_issues)
        assert result.quality_score.security < 90

class TestHTMLValidation:
    """Test HTML validation"""
    
    @pytest.mark.asyncio
    async def test_valid_html_document(self, validator):
        """Test validation of a well-formed HTML document"""
        code = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Component</title>
        </head>
        <body>
            <main>
                <h1>Welcome</h1>
                <p>This is a test component with proper structure.</p>
                <button aria-label="Click me">Action</button>
            </main>
        </body>
        </html>
        """
        
        result = await validator.validate_code(code, "html", 2)
        
        assert result.is_valid
        assert result.quality_score.overall >= 80
        assert result.quality_score.syntax >= 90
    
    @pytest.mark.asyncio
    async def test_html_missing_doctype(self, validator):
        """Test HTML without DOCTYPE"""
        code = """
        <html>
        <head><title>Test</title></head>
        <body><h1>Hello</h1></body>
        </html>
        """
        
        result = await validator.validate_code(code, "html", 2)
        
        syntax_issues = [i for i in result.issues if i.category == ValidationCategory.SYNTAX]
        assert any("DOCTYPE" in issue.message for issue in syntax_issues)

class TestVueValidation:
    """Test Vue component validation"""
    
    @pytest.mark.asyncio
    async def test_valid_vue_component(self, validator):
        """Test validation of a well-formed Vue component"""
        code = """
        <template>
            <div class="component">
                <h1>{{ title }}</h1>
                <button @click="handleClick" :disabled="isLoading">
                    {{ buttonText }}
                </button>
            </div>
        </template>
        
        <script setup lang="ts">
        import { ref, computed } from 'vue';
        
        const title = ref('Vue Component');
        const isLoading = ref(false);
        
        const buttonText = computed(() => 
            isLoading.value ? 'Loading...' : 'Click Me'
        );
        
        const handleClick = () => {
            isLoading.value = true;
            setTimeout(() => {
                isLoading.value = false;
            }, 1000);
        };
        </script>
        
        <style scoped>
        .component {
            padding: 1rem;
        }
        </style>
        """
        
        result = await validator.validate_code(code, "vue", 3)
        
        assert result.is_valid
        assert result.quality_score.overall >= 75
        assert result.quality_score.syntax >= 85
    
    @pytest.mark.asyncio
    async def test_vue_missing_template(self, validator):
        """Test Vue component without template"""
        code = """
        <script>
        export default {
            data() {
                return {
                    message: 'Hello'
                };
            }
        }
        </script>
        """
        
        result = await validator.validate_code(code, "vue", 2)
        
        assert not result.is_valid
        syntax_issues = [i for i in result.issues if i.category == ValidationCategory.SYNTAX]
        assert any("template" in issue.message.lower() for issue in syntax_issues)

class TestAccessibilityValidation:
    """Test accessibility validation"""
    
    @pytest.mark.asyncio
    async def test_missing_alt_text(self, validator):
        """Test images without alt text"""
        code = """
        <div>
            <img src="test.jpg" />
            <img src="test2.jpg" alt="Description" />
        </div>
        """
        
        result = await validator.validate_code(code, "html", 2)
        
        accessibility_issues = [i for i in result.issues if i.category == ValidationCategory.ACCESSIBILITY]
        assert len(accessibility_issues) > 0
        assert any("alt" in issue.message.lower() for issue in accessibility_issues)
    
    @pytest.mark.asyncio
    async def test_button_accessibility(self, validator):
        """Test button accessibility"""
        code = """
        <div>
            <button></button>
            <button aria-label="Close">×</button>
            <button>Click me</button>
        </div>
        """
        
        result = await validator.validate_code(code, "html", 2)
        
        accessibility_issues = [i for i in result.issues if i.category == ValidationCategory.ACCESSIBILITY]
        # Should warn about empty button without aria-label
        assert len(accessibility_issues) > 0

class TestPerformanceValidation:
    """Test performance validation"""
    
    @pytest.mark.asyncio
    async def test_react_inline_functions(self, validator):
        """Test React component with inline functions"""
        code = """
        import React from 'react';
        
        const Component = () => {
            return (
                <div>
                    <button onClick={() => console.log('clicked')}>
                        Click me
                    </button>
                </div>
            );
        };
        
        export default Component;
        """
        
        result = await validator.validate_code(code, "react", 3)
        
        performance_issues = [i for i in result.issues if i.category == ValidationCategory.PERFORMANCE]
        assert len(performance_issues) > 0
        assert any("inline" in issue.message.lower() for issue in performance_issues)
    
    @pytest.mark.asyncio
    async def test_react_missing_keys(self, validator):
        """Test React list without keys"""
        code = """
        import React from 'react';
        
        const ListComponent = ({ items }) => {
            return (
                <ul>
                    {items.map(item => (
                        <li>{item.name}</li>
                    ))}
                </ul>
            );
        };
        
        export default ListComponent;
        """
        
        result = await validator.validate_code(code, "react", 3)
        
        performance_issues = [i for i in result.issues if i.category == ValidationCategory.PERFORMANCE]
        assert len(performance_issues) > 0
        assert any("key" in issue.message.lower() for issue in performance_issues)

class TestSecurityValidation:
    """Test security validation"""
    
    @pytest.mark.asyncio
    async def test_eval_usage(self, validator):
        """Test code with eval()"""
        code = """
        const dangerous = (code) => {
            return eval(code);
        };
        """
        
        result = await validator.validate_code(code, "html", 2)
        
        security_issues = [i for i in result.issues if i.category == ValidationCategory.SECURITY]
        assert len(security_issues) > 0
        assert any("eval" in issue.message.lower() for issue in security_issues)
        assert result.quality_score.security < 80
    
    @pytest.mark.asyncio
    async def test_document_write(self, validator):
        """Test code with document.write"""
        code = """
        function writeContent() {
            document.write('<p>Dynamic content</p>');
        }
        """
        
        result = await validator.validate_code(code, "html", 2)
        
        security_issues = [i for i in result.issues if i.category == ValidationCategory.SECURITY]
        assert len(security_issues) > 0
        assert any("document.write" in issue.message for issue in security_issues)

class TestComplexityValidation:
    """Test complexity-based validation"""
    
    @pytest.mark.asyncio
    async def test_low_complexity_requirements(self, validator):
        """Test that low complexity components have appropriate requirements"""
        simple_code = """
        <div>
            <h1>Simple Component</h1>
            <p>No interactivity needed</p>
        </div>
        """
        
        result = await validator.validate_code(simple_code, "html", 1)
        
        # Should not complain about lack of interactivity for simple components
        functionality_issues = [i for i in result.issues if i.category == ValidationCategory.FUNCTIONALITY]
        assert len(functionality_issues) == 0
    
    @pytest.mark.asyncio
    async def test_high_complexity_requirements(self, validator):
        """Test that high complexity components have appropriate features"""
        simple_code = """
        import React from 'react';
        
        const SimpleComponent = () => {
            return <div>No state or interactions</div>;
        };
        
        export default SimpleComponent;
        """
        
        result = await validator.validate_code(simple_code, "react", 5)
        
        # Should suggest adding more features for high complexity
        functionality_issues = [i for i in result.issues if i.category == ValidationCategory.FUNCTIONALITY]
        assert len(functionality_issues) > 0

class TestQualityScoreCalculation:
    """Test quality score calculation"""
    
    @pytest.mark.asyncio
    async def test_score_calculation_with_no_issues(self, validator):
        """Test quality score with perfect code"""
        perfect_code = """
        import React from 'react';
        
        interface Props {
            children: React.ReactNode;
        }
        
        const PerfectComponent: React.FC<Props> = ({ children }) => {
            return (
                <div className="component">
                    {children}
                </div>
            );
        };
        
        export default PerfectComponent;
        """
        
        result = await validator.validate_code(perfect_code, "react", 2)
        
        assert result.quality_score.overall >= 90
        assert result.quality_score.syntax >= 95
        assert result.is_valid
        assert result.confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_score_calculation_with_errors(self, validator):
        """Test quality score with errors"""
        broken_code = """
        // Missing React import
        const BrokenComponent = () => {
            return (
                <div onClick={() => eval('dangerous code')}>
                    <img src="test.jpg" />
                    {items.map(item => <div>{item}</div>)}
                </div>
            );
        };
        // Missing export
        """
        
        result = await validator.validate_code(broken_code, "react", 3)
        
        assert result.quality_score.overall < 70
        assert not result.is_valid
        assert len(result.issues) > 3
        assert result.confidence < 0.8

class TestSuggestions:
    """Test suggestion generation"""
    
    @pytest.mark.asyncio
    async def test_suggestion_generation(self, validator):
        """Test that appropriate suggestions are generated"""
        code_with_issues = """
        const Component = () => {
            return (
                <div onClick={() => alert('clicked')}>
                    <img src="test.jpg" />
                </div>
            );
        };
        """
        
        result = await validator.validate_code(code_with_issues, "react", 3)
        
        assert len(result.suggestions) > 0
        assert len(result.suggestions) <= 5  # Should limit suggestions
        
        # Check that suggestions are helpful
        suggestions_text = " ".join(result.suggestions).lower()
        assert "accessibility" in suggestions_text or "export" in suggestions_text or "import" in suggestions_text