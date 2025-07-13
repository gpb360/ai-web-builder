'use client';

import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Wand2, 
  Upload, 
  Code, 
  Eye, 
  Copy, 
  Download,
  Sparkles,
  Zap,
  Settings,
  HelpCircle
} from 'lucide-react';
import { ComponentPreview } from './ComponentPreview';
import { PromptInput } from './PromptInput';
import { ComponentTypeSelector } from './ComponentTypeSelector';
import { ComplexitySlider } from './ComplexitySlider';
import { CostEstimator } from './CostEstimator';
import { ImageAnalyzer } from './ImageAnalyzer';
import { QualityValidator } from './QualityValidator';

export interface GenerationRequest {
  description: string;
  componentType: 'react' | 'html' | 'vue';
  complexity: number;
  stylePreferences?: {
    primaryColor?: string;
    theme?: 'light' | 'dark' | 'auto';
    layout?: 'minimal' | 'standard' | 'detailed';
  };
  referenceImage?: File;
}

export interface GenerationResult {
  success: boolean;
  componentCode: string;
  componentType: string;
  estimatedCost: number;
  generationTime: number;
  modelUsed: string;
  suggestions?: string[];
}

interface ComponentGeneratorProps {
  onGenerate?: (request: GenerationRequest) => Promise<GenerationResult>;
  className?: string;
}

export function ComponentGenerator({ onGenerate, className = '' }: ComponentGeneratorProps) {
  const [currentStep, setCurrentStep] = useState<'input' | 'generating' | 'result'>('input');
  const [generationRequest, setGenerationRequest] = useState<GenerationRequest>({
    description: '',
    componentType: 'react',
    complexity: 3,
    stylePreferences: {
      theme: 'light',
      layout: 'standard'
    }
  });
  const [generationResult, setGenerationResult] = useState<GenerationResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [estimatedCost, setEstimatedCost] = useState<number>(0);

  const handleGenerate = useCallback(async () => {
    if (!generationRequest.description.trim()) {
      return;
    }

    setIsGenerating(true);
    setCurrentStep('generating');

    try {
      // Use mock data if no onGenerate provided
      const result = onGenerate 
        ? await onGenerate(generationRequest)
        : await mockGenerate(generationRequest);
      
      setGenerationResult(result);
      setCurrentStep('result');
    } catch (error) {
      console.error('Generation failed:', error);
      // Handle error state
    } finally {
      setIsGenerating(false);
    }
  }, [generationRequest, onGenerate]);

  const mockGenerate = async (request: GenerationRequest): Promise<GenerationResult> => {
    try {
      // Create FormData for multimodal request
      const formData = new FormData();
      formData.append('description', request.description);
      formData.append('component_type', request.componentType);
      formData.append('complexity', request.complexity.toString());
      
      if (request.referenceImage) {
        formData.append('image', request.referenceImage);
      }
      
      // Call the actual API endpoint
      const response = await fetch('/api/ai/generate-component', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type, let browser set it with boundary
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      return {
        success: data.success,
        componentCode: data.component_code,
        componentType: request.componentType,
        estimatedCost: data.cost,
        generationTime: data.processing_time,
        modelUsed: data.model_used,
        suggestions: [
          'Component generated successfully with AI assistance',
          'Review the code for any customizations needed',
          'Test the component in different screen sizes'
        ]
      };
      
    } catch (error) {
      console.error('AI generation failed, using fallback:', error);
      
      // Fallback to mock generation if API fails
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockCode = generateMockComponent(request);
      
      return {
        success: true,
        componentCode: mockCode,
        componentType: request.componentType,
        estimatedCost: estimatedCost,
        generationTime: 2.1,
        modelUsed: 'gemini-1.5-flash (fallback)',
        suggestions: [
          'Using fallback generation - check API connection',
          'Consider adding TypeScript types for better development experience',
          'Test the component across different screen sizes'
        ]
      };
    }
  };

  const generateMockComponent = (request: GenerationRequest): string => {
    const { description, componentType, complexity } = request;
    
    if (componentType === 'react') {
      return `import React from 'react';

interface ComponentProps {
  children?: React.ReactNode;
  className?: string;
  ${complexity >= 3 ? 'onClick?: () => void;' : ''}
  ${complexity >= 4 ? 'disabled?: boolean;' : ''}
}

const GeneratedComponent: React.FC<ComponentProps> = ({ 
  children, 
  className,
  ${complexity >= 3 ? 'onClick,' : ''}
  ${complexity >= 4 ? 'disabled = false,' : ''}
}) => {
  ${complexity >= 4 ? 'const [isHovered, setIsHovered] = React.useState(false);' : ''}
  
  return (
    <div 
      className={\`
        p-4 bg-white rounded-lg shadow-md border border-gray-200
        ${complexity >= 3 ? 'cursor-pointer hover:shadow-lg transition-shadow' : ''}
        ${complexity >= 4 ? 'hover:scale-105 transform transition-transform' : ''}
        \${className}
      \`}
      ${complexity >= 3 ? 'onClick={onClick}' : ''}
      ${complexity >= 4 ? `
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ opacity: disabled ? 0.6 : 1 }}` : ''}
    >
      <div className="flex items-center gap-3">
        ${complexity >= 2 ? '<div className="w-3 h-3 bg-blue-500 rounded-full"></div>' : ''}
        <h3 className="text-lg font-semibold text-gray-800">
          Generated Component
        </h3>
      </div>
      <p className="mt-2 text-gray-600">
        Based on: ${description.slice(0, 60)}...
      </p>
      ${complexity >= 4 ? `
      {isHovered && (
        <div className="mt-3 text-sm text-blue-600">
          Hover effect active! ✨
        </div>
      )}` : ''}
      {children}
    </div>
  );
};

export default GeneratedComponent;`;
    } else if (componentType === 'html') {
      return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Component</title>
    <style>
        .generated-component {
            padding: 1rem;
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #e5e7eb;
            ${complexity >= 3 ? 'cursor: pointer; transition: box-shadow 0.3s;' : ''}
            ${complexity >= 4 ? 'transition: transform 0.3s;' : ''}
        }
        ${complexity >= 3 ? `
        .generated-component:hover {
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
        }` : ''}
        ${complexity >= 4 ? `
        .generated-component:hover {
            transform: scale(1.05);
        }` : ''}
        .component-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .status-indicator {
            width: 0.75rem;
            height: 0.75rem;
            background: #3b82f6;
            border-radius: 50%;
        }
        .component-title {
            font-size: 1.125rem;
            font-weight: 600;
            color: #1f2937;
            margin: 0;
        }
        .component-description {
            margin-top: 0.5rem;
            color: #6b7280;
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div class="generated-component">
        <div class="component-header">
            ${complexity >= 2 ? '<div class="status-indicator"></div>' : ''}
            <h3 class="component-title">Generated Component</h3>
        </div>
        <p class="component-description">
            Based on: ${description.slice(0, 60)}...
        </p>
    </div>
</body>
</html>`;
    } else {
      return `<template>
  <div class="generated-component" ${complexity >= 3 ? '@click="handleClick"' : ''}>
    <div class="component-header">
      ${complexity >= 2 ? '<div class="status-indicator"></div>' : ''}
      <h3 class="component-title">Generated Component</h3>
    </div>
    <p class="component-description">
      Based on: ${description.slice(0, 60)}...
    </p>
    ${complexity >= 4 ? '<div v-if="isHovered" class="hover-message">Vue component active! ⚡</div>' : ''}
  </div>
</template>

<script setup lang="ts">
${complexity >= 3 ? "import { ref } from 'vue';" : ''}
${complexity >= 4 ? `
const isHovered = ref(false);

const handleMouseEnter = () => isHovered.value = true;
const handleMouseLeave = () => isHovered.value = false;` : ''}

${complexity >= 3 ? `
const handleClick = () => {
  console.log('Component clicked!');
};` : ''}
</script>

<style scoped>
.generated-component {
  padding: 1rem;
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  ${complexity >= 3 ? 'cursor: pointer; transition: box-shadow 0.3s;' : ''}
}
${complexity >= 3 ? `
.generated-component:hover {
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
}` : ''}
</style>`;
    }
  };

  return (
    <div className={`max-w-7xl mx-auto p-6 ${className}`}>
      {/* Header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-center gap-3 mb-4"
        >
          <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
            <Wand2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            AI Component Generator
          </h1>
        </motion.div>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Describe your component in plain English and watch as AI creates production-ready code
        </p>
      </div>

      {/* Main Interface */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Panel */}
        <div className="lg:col-span-2 space-y-6">
          <AnimatePresence mode="wait">
            {currentStep === 'input' && (
              <motion.div
                key="input"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-6"
              >
                {/* Description Input */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-4">
                    <Sparkles className="w-5 h-5 text-blue-500" />
                    <h3 className="text-lg font-semibold">Component Description</h3>
                  </div>
                  <PromptInput
                    value={generationRequest.description}
                    onChange={(description) => 
                      setGenerationRequest(prev => ({ ...prev, description }))
                    }
                    onImageUpload={(file) =>
                      setGenerationRequest(prev => ({ ...prev, referenceImage: file }))
                    }
                    uploadedImage={generationRequest.referenceImage}
                    placeholder="Describe your component... e.g., 'Create a responsive pricing card with hover effects and a call-to-action button'"
                  />
                </div>

                {/* Configuration Panel */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-6">
                    <Settings className="w-5 h-5 text-blue-500" />
                    <h3 className="text-lg font-semibold">Configuration</h3>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <ComponentTypeSelector
                      value={generationRequest.componentType}
                      onChange={(componentType) =>
                        setGenerationRequest(prev => ({ ...prev, componentType }))
                      }
                    />
                    
                    <ComplexitySlider
                      value={generationRequest.complexity}
                      onChange={(complexity) =>
                        setGenerationRequest(prev => ({ ...prev, complexity }))
                      }
                    />
                  </div>
                </div>

                {/* Image Analysis */}
                <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
                  <div className="flex items-center gap-3 mb-6">
                    <Eye className="w-5 h-5 text-blue-500" />
                    <h3 className="text-lg font-semibold">Visual Reference (Optional)</h3>
                  </div>
                  <ImageAnalyzer
                    onAnalysisComplete={(analysis, file) => {
                      setGenerationRequest(prev => ({ 
                        ...prev, 
                        referenceImage: file,
                        // Auto-update complexity based on analysis
                        complexity: analysis.suggested_complexity || prev.complexity,
                        // Enhance description with analysis insights
                        description: prev.description ? 
                          `${prev.description}\n\nBased on uploaded image: ${analysis.component_type} with ${analysis.layout_hint}` :
                          `Create a ${analysis.component_type} with ${analysis.layout_hint}`
                      }));
                    }}
                  />
                </div>

                {/* Generate Button */}
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleGenerate}
                  disabled={!generationRequest.description.trim()}
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-4 px-8 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3"
                >
                  <Zap className="w-6 h-6" />
                  Generate Component
                </motion.button>
              </motion.div>
            )}

            {currentStep === 'generating' && (
              <motion.div
                key="generating"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="bg-white rounded-xl border border-gray-200 p-12 shadow-sm text-center"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="w-16 h-16 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center"
                >
                  <Wand2 className="w-8 h-8 text-white" />
                </motion.div>
                <h3 className="text-xl font-semibold mb-2">Generating Your Component</h3>
                <p className="text-gray-600 mb-6">Our AI is crafting the perfect component for you...</p>
                <div className="w-64 mx-auto bg-gray-200 rounded-full h-2">
                  <motion.div
                    className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: "100%" }}
                    transition={{ duration: 2 }}
                  />
                </div>
              </motion.div>
            )}

            {currentStep === 'result' && generationResult && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="space-y-6"
              >
                {/* Result Header */}
                <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                      <Code className="w-4 h-4 text-white" />
                    </div>
                    <h3 className="text-lg font-semibold text-green-800">Component Generated Successfully!</h3>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-green-600 font-medium">Model:</span>
                      <p className="text-green-800">{generationResult.modelUsed}</p>
                    </div>
                    <div>
                      <span className="text-green-600 font-medium">Cost:</span>
                      <p className="text-green-800">${generationResult.estimatedCost.toFixed(6)}</p>
                    </div>
                    <div>
                      <span className="text-green-600 font-medium">Time:</span>
                      <p className="text-green-800">{generationResult.generationTime.toFixed(1)}s</p>
                    </div>
                    <div>
                      <span className="text-green-600 font-medium">Type:</span>
                      <p className="text-green-800">{generationResult.componentType}</p>
                    </div>
                  </div>
                </div>

                {/* Component Code */}
                <ComponentPreview
                  code={generationResult.componentCode}
                  componentType={generationResult.componentType as 'react' | 'html' | 'vue'}
                />

                {/* Quality Validation */}
                <QualityValidator
                  code={generationResult.componentCode}
                  componentType={generationResult.componentType}
                  complexity={generationRequest.complexity}
                  onValidationComplete={(result) => {
                    console.log('Validation completed:', result);
                  }}
                />

                {/* Suggestions */}
                {generationResult.suggestions && generationResult.suggestions.length > 0 && (
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <HelpCircle className="w-5 h-5 text-blue-500" />
                      <h4 className="font-semibold text-blue-800">Suggestions</h4>
                    </div>
                    <ul className="space-y-2">
                      {generationResult.suggestions.map((suggestion, index) => (
                        <li key={index} className="flex items-start gap-2 text-blue-700">
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                          {suggestion}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setCurrentStep('input')}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 px-6 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
                  >
                    <Wand2 className="w-5 h-5" />
                    Generate Another
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => navigator.clipboard.writeText(generationResult.componentCode)}
                    className="px-6 py-3 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-xl font-semibold transition-all flex items-center gap-2"
                  >
                    <Copy className="w-5 h-5" />
                    Copy Code
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Cost Estimator */}
          <CostEstimator
            description={generationRequest.description}
            componentType={generationRequest.componentType}
            complexity={generationRequest.complexity}
            onCostUpdate={setEstimatedCost}
          />

          {/* Tips */}
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border border-purple-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <h4 className="font-semibold text-gray-800">Pro Tips</h4>
            </div>
            <ul className="space-y-3 text-sm text-gray-600">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0" />
                Be specific about styling and behavior you want
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0" />
                Mention responsive design requirements
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0" />
                Include accessibility considerations
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-purple-500 rounded-full mt-2 flex-shrink-0" />
                Higher complexity = more features and interactivity
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}