'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { DollarSign, TrendingDown, Zap, Clock } from 'lucide-react';

interface CostEstimatorProps {
  description: string;
  componentType: 'react' | 'html' | 'vue';
  complexity: number;
  onCostUpdate?: (cost: number) => void;
  className?: string;
}

export function CostEstimator({ 
  description, 
  componentType, 
  complexity, 
  onCostUpdate,
  className = '' 
}: CostEstimatorProps) {
  const [estimatedCost, setEstimatedCost] = useState(0);
  const [breakdown, setBreakdown] = useState({
    inputTokens: 0,
    outputTokens: 0,
    processingTime: 0
  });

  useEffect(() => {
    const calculateCost = async () => {
      try {
        // Create FormData for cost estimation API
        const formData = new FormData();
        formData.append('description', description);
        formData.append('component_type', componentType);
        formData.append('complexity', complexity.toString());
        formData.append('has_image', 'false'); // TODO: detect if image is present
        
        const response = await fetch('/api/ai/estimate-multimodal-cost', {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          const totalCost = data.cost_breakdown.total_cost;
          const processingTime = parseFloat(data.processing_time_estimate);
          
          setEstimatedCost(totalCost);
          setBreakdown({
            inputTokens: Math.round(data.estimated_tokens.input),
            outputTokens: Math.round(data.estimated_tokens.output),
            processingTime: processingTime
          });
          
          if (onCostUpdate) {
            onCostUpdate(totalCost);
          }
          return;
        }
      } catch (error) {
        console.error('Cost estimation API failed, using fallback:', error);
      }
      
      // Fallback to local calculation if API fails
      const descriptionLength = description.length;
      const baseTokens = Math.max(descriptionLength * 1.5, 50); // Minimum 50 tokens
      
      // Output multipliers based on complexity and component type
      const complexityMultipliers = {
        1: 1.5,
        2: 2.0,
        3: 2.5,
        4: 3.5,
        5: 5.0
      };
      
      const typeMultipliers = {
        'react': 1.2, // More complex with TypeScript
        'html': 1.0,  // Simpler
        'vue': 1.1    // Moderate complexity
      };
      
      const outputTokens = baseTokens * 
        complexityMultipliers[complexity as keyof typeof complexityMultipliers] * 
        typeMultipliers[componentType];
      
      // Gemini Flash pricing: $0.075 input, $0.30 output per 1M tokens
      const inputCost = (baseTokens / 1_000_000) * 0.075;
      const outputCost = (outputTokens / 1_000_000) * 0.30;
      const totalCost = inputCost + outputCost;
      
      // Processing time estimate
      const processingTime = Math.max(1, complexity * 0.5 + (outputTokens / 1000));
      
      setEstimatedCost(totalCost);
      setBreakdown({
        inputTokens: Math.round(baseTokens),
        outputTokens: Math.round(outputTokens),
        processingTime: Math.round(processingTime * 10) / 10
      });
      
      if (onCostUpdate) {
        onCostUpdate(totalCost);
      }
    };

    calculateCost();
  }, [description, componentType, complexity, onCostUpdate]);

  // Calculate savings vs competitors
  const competitorCost = estimatedCost * 50; // Assume 50x more expensive
  const savingsPercent = competitorCost > 0 ? ((competitorCost - estimatedCost) / competitorCost * 100) : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white rounded-xl border border-gray-200 p-6 shadow-sm ${className}`}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
          <DollarSign className="w-4 h-4 text-green-600" />
        </div>
        <h4 className="font-semibold text-gray-800">Cost Estimate</h4>
      </div>

      {/* Main Cost Display */}
      <div className="text-center mb-6">
        <motion.div
          key={estimatedCost}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className="text-3xl font-bold text-green-600 mb-1"
        >
          ${estimatedCost.toFixed(6)}
        </motion.div>
        <p className="text-sm text-gray-500">per component generation</p>
      </div>

      {/* Cost Breakdown */}
      <div className="space-y-3 mb-6">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Input tokens:</span>
          <span className="font-medium">{breakdown.inputTokens.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Output tokens:</span>
          <span className="font-medium">{breakdown.outputTokens.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Model:</span>
          <span className="font-medium">Gemini Flash</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Est. time:</span>
          <span className="font-medium">{breakdown.processingTime}s</span>
        </div>
      </div>

      {/* Savings Highlight */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <TrendingDown className="w-4 h-4 text-green-600" />
          <span className="text-sm font-semibold text-green-800">Ultra-Low Cost</span>
        </div>
        <div className="text-xs text-green-700">
          <span className="font-semibold">{savingsPercent.toFixed(1)}% cheaper</span> than traditional platforms
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Zap className="w-4 h-4 text-blue-500" />
            <span className="text-xs font-medium text-gray-700">Efficiency</span>
          </div>
          <div className="text-sm font-bold text-gray-800">99%+</div>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Clock className="w-4 h-4 text-purple-500" />
            <span className="text-xs font-medium text-gray-700">Speed</span>
          </div>
          <div className="text-sm font-bold text-gray-800">{breakdown.processingTime}s</div>
        </div>
      </div>

      {/* Cost Comparison */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <h5 className="text-xs font-semibold text-gray-700 mb-3">Cost Comparison</h5>
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600">Our platform:</span>
            <span className="font-semibold text-green-600">${estimatedCost.toFixed(6)}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600">Traditional tools:</span>
            <span className="font-semibold text-red-500">${(competitorCost).toFixed(4)}</span>
          </div>
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-600">Cache potential:</span>
            <span className="font-semibold text-blue-600">Up to 90% off</span>
          </div>
          <div className="flex justify-between items-center text-xs pt-1 border-t border-gray-100">
            <span className="text-gray-600 font-medium">You save:</span>
            <span className="font-bold text-green-600">${(competitorCost - estimatedCost).toFixed(4)}</span>
          </div>
        </div>
      </div>

      {/* Model Info */}
      <div className="mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Powered by Google Gemini Flash</span>
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">
            Ultra-fast
          </span>
        </div>
      </div>
    </motion.div>
  );
}