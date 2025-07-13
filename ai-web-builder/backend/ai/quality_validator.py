"""
AI Response Quality Validator
Validates AI-generated code for quality, security, and functionality
"""
import re
import ast
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"

class ValidationCategory(Enum):
    SYNTAX = "syntax"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ACCESSIBILITY = "accessibility"
    BEST_PRACTICES = "best_practices"
    FUNCTIONALITY = "functionality"

@dataclass
class ValidationIssue:
    category: ValidationCategory
    severity: str  # "error", "warning", "info"
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class QualityScore:
    overall: float  # 0-100
    syntax: float
    security: float
    performance: float
    accessibility: float
    best_practices: float
    functionality: float

@dataclass
class ValidationResult:
    is_valid: bool
    quality_score: QualityScore
    issues: List[ValidationIssue]
    suggestions: List[str]
    estimated_fix_time: int  # minutes
    confidence: float  # 0-1

class AIQualityValidator:
    """
    Validates AI-generated code for quality, security, and best practices
    """
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.security_patterns = self._load_security_patterns()
        self.performance_patterns = self._load_performance_patterns()
        self.accessibility_patterns = self._load_accessibility_patterns()
    
    async def validate_code(
        self, 
        code: str, 
        component_type: str, 
        complexity: int = 3
    ) -> ValidationResult:
        """
        Validate AI-generated code comprehensively
        
        Args:
            code: The generated code to validate
            component_type: Type of component ('react', 'html', 'vue')
            complexity: Expected complexity level (1-5)
            
        Returns:
            ValidationResult with scores, issues, and suggestions
        """
        issues = []
        
        try:
            # Syntax validation
            syntax_issues = await self._validate_syntax(code, component_type)
            issues.extend(syntax_issues)
            
            # Security validation
            security_issues = await self._validate_security(code, component_type)
            issues.extend(security_issues)
            
            # Performance validation
            performance_issues = await self._validate_performance(code, component_type)
            issues.extend(performance_issues)
            
            # Accessibility validation
            accessibility_issues = await self._validate_accessibility(code, component_type)
            issues.extend(accessibility_issues)
            
            # Best practices validation
            best_practices_issues = await self._validate_best_practices(code, component_type, complexity)
            issues.extend(best_practices_issues)
            
            # Functionality validation
            functionality_issues = await self._validate_functionality(code, component_type, complexity)
            issues.extend(functionality_issues)
            
            # Calculate quality scores
            quality_score = self._calculate_quality_score(issues, complexity)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(issues, quality_score)
            
            # Determine if code is valid
            error_count = len([i for i in issues if i.severity == "error"])
            is_valid = error_count == 0 and quality_score.overall >= 70
            
            # Estimate fix time
            fix_time = self._estimate_fix_time(issues)
            
            # Calculate confidence
            confidence = self._calculate_confidence(quality_score, issues)
            
            logger.info(f"Code validation completed: {quality_score.overall:.1f}% quality, {len(issues)} issues")
            
            return ValidationResult(
                is_valid=is_valid,
                quality_score=quality_score,
                issues=issues,
                suggestions=suggestions,
                estimated_fix_time=fix_time,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                quality_score=QualityScore(0, 0, 0, 0, 0, 0, 0),
                issues=[ValidationIssue(
                    category=ValidationCategory.SYNTAX,
                    severity="error",
                    message=f"Validation failed: {str(e)}"
                )],
                suggestions=["Code validation failed - manual review required"],
                estimated_fix_time=30,
                confidence=0.0
            )
    
    async def _validate_syntax(self, code: str, component_type: str) -> List[ValidationIssue]:
        """Validate syntax and basic structure"""
        issues = []
        
        if component_type == "react":
            issues.extend(await self._validate_react_syntax(code))
        elif component_type == "html":
            issues.extend(await self._validate_html_syntax(code))
        elif component_type == "vue":
            issues.extend(await self._validate_vue_syntax(code))
        
        return issues
    
    async def _validate_react_syntax(self, code: str) -> List[ValidationIssue]:
        """Validate React component syntax"""
        issues = []
        
        # Check for basic React structure
        if not re.search(r'import.*React', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="warning",
                message="Missing React import statement",
                suggestion="Add 'import React from 'react';' at the top"
            ))
        
        # Check for component export
        if not re.search(r'export\s+(default\s+)?', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="error",
                message="Component must be exported",
                suggestion="Add 'export default ComponentName;' or 'export { ComponentName };'"
            ))
        
        # Check for proper JSX structure
        if 'return' in code and not re.search(r'return\s*\([\s\S]*<', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="warning",
                message="JSX should be wrapped in parentheses for multi-line returns",
                suggestion="Wrap JSX in parentheses: return (JSX here)"
            ))
        
        # Check for TypeScript interfaces if using TS
        if 'interface' in code and not re.search(r'interface\s+\w+Props', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.BEST_PRACTICES,
                severity="warning",
                message="Interface name should follow 'ComponentNameProps' convention",
                suggestion="Name interfaces with 'Props' suffix (e.g., ButtonProps)"
            ))
        
        return issues
    
    async def _validate_html_syntax(self, code: str) -> List[ValidationIssue]:
        """Validate HTML syntax"""
        issues = []
        
        # Check for DOCTYPE
        if not re.search(r'<!DOCTYPE\s+html>', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="warning",
                message="Missing DOCTYPE declaration",
                suggestion="Add '<!DOCTYPE html>' at the beginning"
            ))
        
        # Check for basic HTML structure
        if not re.search(r'<html[^>]*>', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="error",
                message="Missing <html> tag",
                suggestion="Wrap content in <html> tags"
            ))
        
        # Check for head section
        if not re.search(r'<head[^>]*>', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="warning",
                message="Missing <head> section",
                suggestion="Add <head> section with meta tags"
            ))
        
        # Check for viewport meta tag
        if not re.search(r'<meta[^>]*viewport', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.BEST_PRACTICES,
                severity="warning",
                message="Missing viewport meta tag",
                suggestion="Add <meta name='viewport' content='width=device-width, initial-scale=1.0'>"
            ))
        
        return issues
    
    async def _validate_vue_syntax(self, code: str) -> List[ValidationIssue]:
        """Validate Vue component syntax"""
        issues = []
        
        # Check for template section
        if not re.search(r'<template[^>]*>', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="error",
                message="Vue component must have <template> section",
                suggestion="Add <template> section with component HTML"
            ))
        
        # Check for script section
        if not re.search(r'<script[^>]*>', code, re.IGNORECASE):
            issues.append(ValidationIssue(
                category=ValidationCategory.SYNTAX,
                severity="warning",
                message="Missing <script> section",
                suggestion="Add <script setup> section for component logic"
            ))
        
        # Check for Composition API usage
        if '<script' in code and not re.search(r'<script[^>]*setup', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.BEST_PRACTICES,
                severity="info",
                message="Consider using Composition API with <script setup>",
                suggestion="Use <script setup> for modern Vue 3 components"
            ))
        
        return issues
    
    async def _validate_security(self, code: str, component_type: str) -> List[ValidationIssue]:
        """Validate security aspects"""
        issues = []
        
        # Check for dangerous patterns
        for pattern, issue_info in self.security_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    severity=issue_info["severity"],
                    message=issue_info["message"],
                    suggestion=issue_info["suggestion"]
                ))
        
        # Check for XSS vulnerabilities
        if component_type == "react":
            if re.search(r'dangerouslySetInnerHTML', code):
                issues.append(ValidationIssue(
                    category=ValidationCategory.SECURITY,
                    severity="warning",
                    message="dangerouslySetInnerHTML can lead to XSS attacks",
                    suggestion="Sanitize HTML content or use safe alternatives"
                ))
        
        # Check for eval usage
        if re.search(r'\beval\s*\(', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.SECURITY,
                severity="error",
                message="eval() is dangerous and should be avoided",
                suggestion="Use safer alternatives like JSON.parse() or Function constructor"
            ))
        
        return issues
    
    async def _validate_performance(self, code: str, component_type: str) -> List[ValidationIssue]:
        """Validate performance aspects"""
        issues = []
        
        # Check for performance anti-patterns
        for pattern, issue_info in self.performance_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(ValidationIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity=issue_info["severity"],
                    message=issue_info["message"],
                    suggestion=issue_info["suggestion"]
                ))
        
        # React-specific performance checks
        if component_type == "react":
            # Check for inline functions in JSX
            if re.search(r'onClick=\{[^}]*=>', code):
                issues.append(ValidationIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity="warning",
                    message="Inline arrow functions can cause unnecessary re-renders",
                    suggestion="Define functions outside JSX or use useCallback"
                ))
            
            # Check for missing key props in lists
            if re.search(r'\.map\s*\([^}]*<\w+(?![^>]*key=)', code):
                issues.append(ValidationIssue(
                    category=ValidationCategory.PERFORMANCE,
                    severity="warning",
                    message="Missing 'key' prop in list items",
                    suggestion="Add unique 'key' prop to each list item"
                ))
        
        return issues
    
    async def _validate_accessibility(self, code: str, component_type: str) -> List[ValidationIssue]:
        """Validate accessibility aspects"""
        issues = []
        
        # Check for accessibility patterns
        for pattern, issue_info in self.accessibility_patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(ValidationIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity=issue_info["severity"],
                    message=issue_info["message"],
                    suggestion=issue_info["suggestion"]
                ))
        
        # Check for missing alt text on images
        if re.search(r'<img(?![^>]*alt=)', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.ACCESSIBILITY,
                severity="warning",
                message="Images should have alt text for accessibility",
                suggestion="Add alt attribute to all img tags"
            ))
        
        # Check for missing ARIA labels on interactive elements
        if re.search(r'<button(?![^>]*aria-label)(?![^>]*aria-labelledby)', code):
            if not re.search(r'<button[^>]*>[^<]+</button>', code):
                issues.append(ValidationIssue(
                    category=ValidationCategory.ACCESSIBILITY,
                    severity="warning",
                    message="Buttons without visible text should have aria-label",
                    suggestion="Add aria-label or ensure button has visible text content"
                ))
        
        return issues
    
    async def _validate_best_practices(self, code: str, component_type: str, complexity: int) -> List[ValidationIssue]:
        """Validate coding best practices"""
        issues = []
        
        # Check for proper naming conventions
        if component_type == "react":
            # Component should start with capital letter
            component_match = re.search(r'(?:function|const)\s+(\w+)', code)
            if component_match and not component_match.group(1)[0].isupper():
                issues.append(ValidationIssue(
                    category=ValidationCategory.BEST_PRACTICES,
                    severity="warning",
                    message="React components should start with capital letter",
                    suggestion="Rename component to start with uppercase letter"
                ))
        
        # Check for proper error handling
        if complexity >= 3 and not re.search(r'try\s*\{|catch\s*\(', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.BEST_PRACTICES,
                severity="info",
                message="Consider adding error handling for complex components",
                suggestion="Add try-catch blocks for error-prone operations"
            ))
        
        # Check for proper TypeScript usage
        if 'interface' in code and not re.search(r':\s*\w+(\[\])?[;\}]', code):
            issues.append(ValidationIssue(
                category=ValidationCategory.BEST_PRACTICES,
                severity="warning",
                message="TypeScript types should be properly defined",
                suggestion="Ensure all interface properties have proper types"
            ))
        
        return issues
    
    async def _validate_functionality(self, code: str, component_type: str, complexity: int) -> List[ValidationIssue]:
        """Validate functional aspects"""
        issues = []
        
        # Check for basic functionality requirements based on complexity
        if complexity >= 3:
            # Should have some form of interactivity
            has_events = re.search(r'on\w+\s*=|addEventListener', code, re.IGNORECASE)
            has_state = re.search(r'useState|ref\(|data\(\)', code)
            
            if not has_events and not has_state:
                issues.append(ValidationIssue(
                    category=ValidationCategory.FUNCTIONALITY,
                    severity="info",
                    message="Complex components should have interactive elements or state",
                    suggestion="Add event handlers or state management for complexity level 3+"
                ))
        
        if complexity >= 4:
            # Should have proper validation or error states
            has_validation = re.search(r'validation|error|isValid', code, re.IGNORECASE)
            if not has_validation:
                issues.append(ValidationIssue(
                    category=ValidationCategory.FUNCTIONALITY,
                    severity="info",
                    message="Advanced components should include validation logic",
                    suggestion="Add input validation and error handling"
                ))
        
        return issues
    
    def _calculate_quality_score(self, issues: List[ValidationIssue], complexity: int) -> QualityScore:
        """Calculate quality scores based on issues found"""
        # Base scores
        base_score = 100
        
        # Category scores
        category_scores = {
            ValidationCategory.SYNTAX: 100,
            ValidationCategory.SECURITY: 100,
            ValidationCategory.PERFORMANCE: 100,
            ValidationCategory.ACCESSIBILITY: 100,
            ValidationCategory.BEST_PRACTICES: 100,
            ValidationCategory.FUNCTIONALITY: 100
        }
        
        # Deduct points based on issues
        severity_penalties = {
            "error": 25,
            "warning": 10,
            "info": 5
        }
        
        for issue in issues:
            penalty = severity_penalties.get(issue.severity, 5)
            category_scores[issue.category] = max(0, category_scores[issue.category] - penalty)
        
        # Calculate overall score (weighted)
        weights = {
            ValidationCategory.SYNTAX: 0.25,
            ValidationCategory.SECURITY: 0.20,
            ValidationCategory.PERFORMANCE: 0.15,
            ValidationCategory.ACCESSIBILITY: 0.15,
            ValidationCategory.BEST_PRACTICES: 0.15,
            ValidationCategory.FUNCTIONALITY: 0.10
        }
        
        overall = sum(category_scores[cat] * weight for cat, weight in weights.items())
        
        return QualityScore(
            overall=round(overall, 1),
            syntax=round(category_scores[ValidationCategory.SYNTAX], 1),
            security=round(category_scores[ValidationCategory.SECURITY], 1),
            performance=round(category_scores[ValidationCategory.PERFORMANCE], 1),
            accessibility=round(category_scores[ValidationCategory.ACCESSIBILITY], 1),
            best_practices=round(category_scores[ValidationCategory.BEST_PRACTICES], 1),
            functionality=round(category_scores[ValidationCategory.FUNCTIONALITY], 1)
        )
    
    def _generate_suggestions(self, issues: List[ValidationIssue], quality_score: QualityScore) -> List[str]:
        """Generate improvement suggestions based on validation results"""
        suggestions = []
        
        # Add specific suggestions from issues
        for issue in issues:
            if issue.suggestion and issue.suggestion not in suggestions:
                suggestions.append(issue.suggestion)
        
        # Add general suggestions based on scores
        if quality_score.security < 80:
            suggestions.append("Review security practices and sanitize user inputs")
        
        if quality_score.accessibility < 70:
            suggestions.append("Improve accessibility with ARIA labels and semantic HTML")
        
        if quality_score.performance < 75:
            suggestions.append("Optimize performance by avoiding inline functions and adding keys to lists")
        
        if quality_score.overall < 70:
            suggestions.append("Consider regenerating the component with more specific requirements")
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _estimate_fix_time(self, issues: List[ValidationIssue]) -> int:
        """Estimate time needed to fix issues (in minutes)"""
        time_estimates = {
            "error": 15,
            "warning": 8,
            "info": 3
        }
        
        total_time = sum(time_estimates.get(issue.severity, 5) for issue in issues)
        return min(total_time, 120)  # Cap at 2 hours
    
    def _calculate_confidence(self, quality_score: QualityScore, issues: List[ValidationIssue]) -> float:
        """Calculate confidence in the validation result"""
        base_confidence = quality_score.overall / 100
        
        # Reduce confidence for critical issues
        error_count = len([i for i in issues if i.severity == "error"])
        if error_count > 0:
            base_confidence *= 0.7
        
        return round(base_confidence, 2)
    
    def _load_security_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load security validation patterns"""
        return {
            r'innerHTML\s*=': {
                "severity": "warning",
                "message": "innerHTML can be vulnerable to XSS attacks",
                "suggestion": "Use textContent or DOM manipulation methods"
            },
            r'document\.write': {
                "severity": "error",
                "message": "document.write is deprecated and dangerous",
                "suggestion": "Use modern DOM manipulation methods"
            },
            r'javascript:': {
                "severity": "error",
                "message": "javascript: protocol is dangerous",
                "suggestion": "Use event handlers instead of javascript: links"
            }
        }
    
    def _load_performance_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load performance validation patterns"""
        return {
            r'for\s*\([^{]*{[^}]*document\.': {
                "severity": "warning",
                "message": "DOM queries in loops can be slow",
                "suggestion": "Cache DOM elements outside the loop"
            },
            r'setInterval\s*\([^,]*,\s*[0-9]{1,2}[^0-9]': {
                "severity": "warning",
                "message": "Very frequent intervals can impact performance",
                "suggestion": "Consider using longer intervals or requestAnimationFrame"
            }
        }
    
    def _load_accessibility_patterns(self) -> Dict[str, Dict[str, str]]:
        """Load accessibility validation patterns"""
        return {
            r'<div[^>]*onClick': {
                "severity": "warning",
                "message": "Clickable divs should be buttons or have proper ARIA roles",
                "suggestion": "Use <button> or add role='button' and keyboard handlers"
            },
            r'<input(?![^>]*aria-label)(?![^>]*aria-labelledby)(?![^>]*<label)': {
                "severity": "warning",
                "message": "Form inputs should have associated labels",
                "suggestion": "Add <label> or aria-label to form inputs"
            }
        }