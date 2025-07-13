'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Settings, Brain, Rocket, Star } from 'lucide-react';

interface ComplexitySliderProps {
  value: number;
  onChange: (value: number) => void;
  className?: string;
}

export function ComplexitySlider({ value, onChange, className = '' }: ComplexitySliderProps) {
  const complexityLevels = [
    {
      value: 1,
      label: 'Simple',
      description: 'Basic structure, minimal styling',
      icon: Zap,
      color: 'from-green-400 to-green-500',
      examples: ['Simple button', 'Basic text input', 'Static card'],
      features: ['Clean HTML structure', 'Basic CSS styling', 'Minimal JavaScript']
    },
    {
      value: 2,
      label: 'Basic',
      description: 'Interactive elements, hover effects',
      icon: Settings,
      color: 'from-blue-400 to-blue-500',
      examples: ['Button with hover', 'Form with labels', 'Card with image'],
      features: ['Hover animations', 'Basic interactivity', 'Improved styling']
    },
    {
      value: 3,
      label: 'Standard',
      description: 'Responsive design, multiple states',
      icon: Brain,
      color: 'from-purple-400 to-purple-500',
      examples: ['Modal dialog', 'Navigation menu', 'Form validation'],
      features: ['Responsive breakpoints', 'State management', 'Error handling']
    },
    {
      value: 4,
      label: 'Advanced',
      description: 'Complex logic, animations, APIs',
      icon: Rocket,
      color: 'from-orange-400 to-orange-500',
      examples: ['Data table', 'Multi-step form', 'File uploader'],
      features: ['Complex state logic', 'API integration', 'Advanced animations']
    },
    {
      value: 5,
      label: 'Expert',
      description: 'Enterprise features, optimizations',
      icon: Star,
      color: 'from-red-400 to-red-500',
      examples: ['Dashboard', 'Code editor', 'Real-time chat'],
      features: ['Performance optimization', 'Advanced patterns', 'Enterprise features']
    }
  ];

  const currentLevel = complexityLevels.find(level => level.value === value) || complexityLevels[2];

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h4 className="text-sm font-semibold text-gray-800 mb-2">Complexity Level</h4>
        <p className="text-xs text-gray-500">Higher complexity adds more features and interactivity</p>
      </div>

      {/* Visual Slider */}
      <div className="relative">
        <div className="flex justify-between mb-4">
          {complexityLevels.map((level) => {
            const IconComponent = level.icon;
            const isActive = value >= level.value;
            const isCurrent = value === level.value;
            
            return (
              <button
                key={level.value}
                onClick={() => onChange(level.value)}
                className={`
                  relative flex flex-col items-center p-2 rounded-lg transition-all duration-200
                  ${isCurrent ? 'transform scale-110' : 'hover:scale-105'}
                `}
              >
                <motion.div
                  className={`
                    w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-all duration-200
                    ${isActive 
                      ? `bg-gradient-to-br ${level.color} text-white shadow-lg` 
                      : 'bg-gray-200 text-gray-400'
                    }
                  `}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <IconComponent className="w-5 h-5" />
                </motion.div>
                
                <span className={`
                  text-xs font-medium transition-colors
                  ${isActive ? 'text-gray-800' : 'text-gray-500'}
                `}>
                  {level.label}
                </span>

                {/* Connection Line */}
                {level.value < 5 && (
                  <div className={`
                    absolute top-7 left-full w-8 h-0.5 transition-colors duration-200
                    ${value > level.value ? 'bg-blue-500' : 'bg-gray-300'}
                  `} style={{ transform: 'translateX(-50%)' }} />
                )}
              </button>
            );
          })}
        </div>

        {/* Range Input (Hidden but functional) */}
        <input
          type="range"
          min={1}
          max={5}
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer opacity-0 absolute top-0"
        />
      </div>

      {/* Current Level Details */}
      <motion.div
        key={value}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`
          p-4 rounded-xl border-2 border-gray-200
          bg-gradient-to-br ${currentLevel.color} bg-opacity-5
        `}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className={`
            w-8 h-8 rounded-lg flex items-center justify-center
            bg-gradient-to-br ${currentLevel.color} text-white
          `}>
            <currentLevel.icon className="w-4 h-4" />
          </div>
          <div>
            <h5 className="font-semibold text-gray-800">{currentLevel.label} Complexity</h5>
            <p className="text-sm text-gray-600">{currentLevel.description}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <h6 className="text-sm font-medium text-gray-700 mb-2">Features included:</h6>
            <ul className="space-y-1">
              {currentLevel.features.map((feature, index) => (
                <li key={index} className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h6 className="text-sm font-medium text-gray-700 mb-2">Example components:</h6>
            <div className="flex flex-wrap gap-1">
              {currentLevel.examples.map((example, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md"
                >
                  {example}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Cost Impact */}
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Estimated generation cost:</span>
          <span className="font-medium text-gray-800">
            ${(0.0001 * value * 2).toFixed(6)}
          </span>
        </div>
      </motion.div>

      {/* Tips */}
      <div className="bg-gray-50 rounded-lg p-3">
        <h6 className="text-sm font-medium text-gray-700 mb-2">💡 Tips for better results:</h6>
        <ul className="text-xs text-gray-600 space-y-1">
          {value <= 2 && (
            <>
              <li>• Perfect for prototyping and quick mockups</li>
              <li>• Ideal when you need fast turnaround times</li>
            </>
          )}
          {value === 3 && (
            <>
              <li>• Great balance of features and simplicity</li>
              <li>• Includes responsive design and basic interactions</li>
            </>
          )}
          {value >= 4 && (
            <>
              <li>• Suitable for production applications</li>
              <li>• Includes advanced patterns and optimizations</li>
              <li>• May require additional customization for specific needs</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
}