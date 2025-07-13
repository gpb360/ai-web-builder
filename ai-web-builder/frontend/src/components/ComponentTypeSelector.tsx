'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface ComponentTypeSelectorProps {
  value: 'react' | 'html' | 'vue';
  onChange: (value: 'react' | 'html' | 'vue') => void;
  className?: string;
}

export function ComponentTypeSelector({ value, onChange, className = '' }: ComponentTypeSelectorProps) {
  const options = [
    {
      value: 'react' as const,
      label: 'React',
      description: 'TypeScript + Tailwind CSS',
      icon: '⚛️',
      color: 'from-blue-500 to-cyan-500',
      features: ['TypeScript types', 'Hooks & functional components', 'Modern patterns']
    },
    {
      value: 'html' as const,
      label: 'HTML',
      description: 'Pure HTML5 + CSS3',
      icon: '🌐',
      color: 'from-orange-500 to-red-500',
      features: ['Semantic HTML', 'Modern CSS', 'Universal compatibility']
    },
    {
      value: 'vue' as const,
      label: 'Vue',
      description: 'Vue 3 + Composition API',
      icon: '💚',
      color: 'from-green-500 to-emerald-500',
      features: ['Composition API', 'TypeScript support', 'Reactive data']
    }
  ];

  return (
    <div className={`space-y-4 ${className}`}>
      <div>
        <h4 className="text-sm font-semibold text-gray-800 mb-2">Component Type</h4>
        <p className="text-xs text-gray-500">Choose your preferred framework or technology</p>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {options.map((option) => (
          <motion.button
            key={option.value}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onChange(option.value)}
            className={`
              relative p-4 rounded-xl border-2 text-left transition-all duration-200
              ${value === option.value
                ? 'border-blue-500 bg-blue-50 shadow-md'
                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
              }
            `}
          >
            <div className="flex items-start gap-3">
              <div className={`
                w-10 h-10 rounded-lg flex items-center justify-center text-lg
                bg-gradient-to-br ${option.color}
              `}>
                <span className="text-white font-bold">
                  {option.icon}
                </span>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h5 className="font-semibold text-gray-800">{option.label}</h5>
                  {value === option.value && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-2 h-2 bg-blue-500 rounded-full"
                    />
                  )}
                </div>
                <p className="text-sm text-gray-600 mb-2">{option.description}</p>
                
                <div className="flex flex-wrap gap-1">
                  {option.features.map((feature, index) => (
                    <span
                      key={index}
                      className={`
                        px-2 py-1 text-xs rounded-md
                        ${value === option.value
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-600'
                        }
                      `}
                    >
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Selection indicator */}
            {value === option.value && (
              <motion.div
                layoutId="selected-framework"
                className="absolute inset-0 border-2 border-blue-500 rounded-xl pointer-events-none"
                initial={false}
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
              />
            )}
          </motion.button>
        ))}
      </div>

      {/* Additional Info */}
      <div className="bg-gray-50 rounded-lg p-3">
        <h5 className="text-sm font-medium text-gray-700 mb-2">What you'll get:</h5>
        <ul className="text-xs text-gray-600 space-y-1">
          <li className="flex items-center gap-2">
            <span className="w-1 h-1 bg-gray-400 rounded-full" />
            Production-ready code with best practices
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1 h-1 bg-gray-400 rounded-full" />
            Responsive design and mobile optimization
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1 h-1 bg-gray-400 rounded-full" />
            Accessibility features built-in
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1 h-1 bg-gray-400 rounded-full" />
            Modern styling and animations
          </li>
        </ul>
      </div>
    </div>
  );
}