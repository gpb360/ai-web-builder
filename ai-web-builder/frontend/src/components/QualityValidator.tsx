'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  Zap, 
  Eye, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Clock,
  Target,
  Code,
  Accessibility,
  Settings,
  TrendingUp
} from 'lucide-react';

interface QualityScore {
  overall: number;
  syntax: number;
  security: number;
  performance: number;
  accessibility: number;
  best_practices: number;
  functionality: number;
}

interface ValidationIssue {
  category: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  line_number?: number;
  suggestion?: string;
  code_snippet?: string;
}

interface ValidationResult {
  is_valid: boolean;
  quality_score: QualityScore;
  issues: ValidationIssue[];
  suggestions: string[];
  estimated_fix_time: number;
  confidence: number;
}

interface QualityValidatorProps {
  code: string;
  componentType: string;
  complexity: number;
  onValidationComplete?: (result: ValidationResult) => void;
  className?: string;
}

export function QualityValidator({ 
  code, 
  componentType, 
  complexity, 
  onValidationComplete,
  className = '' 
}: QualityValidatorProps) {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateCode = async () => {
    if (!code.trim()) {
      setError('No code to validate');
      return;
    }

    setIsValidating(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('code', code);
      formData.append('component_type', componentType);
      formData.append('complexity', complexity.toString());
      formData.append('validation_level', 'standard');

      const response = await fetch('/api/ai/validate-code', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });

      if (!response.ok) {
        throw new Error(`Validation failed: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data.success) {
        setValidationResult(data.validation_result);
        if (onValidationComplete) {
          onValidationComplete(data.validation_result);
        }
      } else {
        throw new Error('Validation failed on server');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Validation failed';
      setError(errorMessage);
    } finally {
      setIsValidating(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 80) return 'text-blue-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score: number) => {
    if (score >= 90) return 'bg-green-100';
    if (score >= 80) return 'bg-blue-100';
    if (score >= 70) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      default:
        return <CheckCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'syntax':
        return <Code className="w-4 h-4" />;
      case 'security':
        return <Shield className="w-4 h-4" />;
      case 'performance':
        return <Zap className="w-4 h-4" />;
      case 'accessibility':
        return <Accessibility className="w-4 h-4" />;
      case 'best_practices':
        return <Settings className="w-4 h-4" />;
      case 'functionality':
        return <Target className="w-4 h-4" />;
      default:
        return <CheckCircle className="w-4 h-4" />;
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 shadow-sm ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
            <Shield className="w-4 h-4 text-green-600" />
          </div>
          <h4 className="font-semibold text-gray-800">Code Quality Validation</h4>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={validateCode}
          disabled={isValidating || !code.trim()}
          className="px-4 py-2 bg-green-500 text-white rounded-lg font-medium hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
        >
          {isValidating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Validating...
            </>
          ) : (
            <>
              <Shield className="w-4 h-4" />
              Validate Code
            </>
          )}
        </motion.button>
      </div>

      <AnimatePresence mode="wait">
        {error && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg"
          >
            <div className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Validation Error</p>
                <p className="text-sm text-red-600">{error}</p>
              </div>
            </div>
          </motion.div>
        )}

        {validationResult && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-6"
          >
            {/* Overall Score */}
            <div className={`p-6 rounded-xl ${getScoreBackground(validationResult.quality_score.overall)}`}>
              <div className="flex items-center justify-between mb-4">
                <h5 className="font-semibold text-gray-800">Overall Quality Score</h5>
                <div className={`text-3xl font-bold ${getScoreColor(validationResult.quality_score.overall)}`}>
                  {validationResult.quality_score.overall}%
                </div>
              </div>
              
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  {validationResult.is_valid ? (
                    <CheckCircle className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className={validationResult.is_valid ? 'text-green-700' : 'text-red-700'}>
                    {validationResult.is_valid ? 'Valid' : 'Needs Fixes'}
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-600">
                    ~{validationResult.estimated_fix_time}min to fix
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-gray-500" />
                  <span className="text-gray-600">
                    {Math.round(validationResult.confidence * 100)}% confidence
                  </span>
                </div>
              </div>
            </div>

            {/* Category Scores */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { key: 'syntax', label: 'Syntax', icon: 'code' },
                { key: 'security', label: 'Security', icon: 'security' },
                { key: 'performance', label: 'Performance', icon: 'performance' },
                { key: 'accessibility', label: 'Accessibility', icon: 'accessibility' },
                { key: 'best_practices', label: 'Best Practices', icon: 'best_practices' },
                { key: 'functionality', label: 'Functionality', icon: 'functionality' }
              ].map((category) => {
                const score = validationResult.quality_score[category.key as keyof QualityScore];
                return (
                  <div key={category.key} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      {getCategoryIcon(category.icon)}
                      <span className="text-sm font-medium text-gray-700">{category.label}</span>
                    </div>
                    <div className={`text-xl font-bold ${getScoreColor(score)}`}>
                      {score}%
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Issues */}
            {validationResult.issues.length > 0 && (
              <div className="space-y-4">
                <h6 className="font-semibold text-gray-800">Issues Found ({validationResult.issues.length})</h6>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {validationResult.issues.map((issue, index) => (
                    <div key={index} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-start gap-3">
                        {getSeverityIcon(issue.severity)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-gray-800">{issue.message}</span>
                            <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-md">
                              {issue.category}
                            </span>
                            {issue.line_number && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-600 text-xs rounded-md">
                                Line {issue.line_number}
                              </span>
                            )}
                          </div>
                          {issue.suggestion && (
                            <p className="text-sm text-gray-600 mt-2">
                              💡 {issue.suggestion}
                            </p>
                          )}
                          {issue.code_snippet && (
                            <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-x-auto">
                              <code>{issue.code_snippet}</code>
                            </pre>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {validationResult.suggestions.length > 0 && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h6 className="font-semibold text-blue-800 mb-3">Improvement Suggestions</h6>
                <ul className="space-y-2">
                  {validationResult.suggestions.map((suggestion, index) => (
                    <li key={index} className="flex items-start gap-2 text-blue-700">
                      <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-sm">{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {!validationResult && !error && !isValidating && (
        <div className="text-center py-8 text-gray-500">
          <Shield className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className="text-lg font-medium mb-2">Ready to Validate</p>
          <p className="text-sm">Click "Validate Code" to check quality, security, and best practices</p>
        </div>
      )}
    </div>
  );
}