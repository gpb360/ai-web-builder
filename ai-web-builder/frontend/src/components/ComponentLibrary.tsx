'use client';

import React from 'react';
import { useDraggable } from '@dnd-kit/core';
import { motion } from 'framer-motion';
import {
  Square,
  Type,
  MousePointer,
  Image,
  Star,
  CreditCard,
  FileText,
  Navigation,
  Layout,
  Layers,
  Grid3X3,
  Box,
  Monitor,
  Smartphone
} from 'lucide-react';

interface ComponentItem {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  category: 'basic' | 'layout' | 'content' | 'media' | 'forms' | 'advanced';
  color: string;
}

const componentLibrary: ComponentItem[] = [
  // Basic Components
  {
    id: 'container',
    name: 'Container',
    description: 'A flexible container for other components',
    icon: Square,
    category: 'basic',
    color: 'bg-blue-500',
  },
  {
    id: 'text',
    name: 'Text',
    description: 'Add text content',
    icon: Type,
    category: 'basic',
    color: 'bg-green-500',
  },
  {
    id: 'button',
    name: 'Button',
    description: 'Interactive button component',
    icon: MousePointer,
    category: 'basic',
    color: 'bg-purple-500',
  },
  
  // Layout Components
  {
    id: 'hero',
    name: 'Hero Section',
    description: 'Large banner section with title and CTA',
    icon: Monitor,
    category: 'layout',
    color: 'bg-indigo-500',
  },
  {
    id: 'navigation',
    name: 'Navigation',
    description: 'Website navigation menu',
    icon: Navigation,
    category: 'layout',
    color: 'bg-cyan-500',
  },
  {
    id: 'card',
    name: 'Card',
    description: 'Content card with title and description',
    icon: CreditCard,
    category: 'layout',
    color: 'bg-orange-500',
  },
  
  // Media Components
  {
    id: 'image',
    name: 'Image',
    description: 'Display images with alt text',
    icon: Image,
    category: 'media',
    color: 'bg-pink-500',
  },
  
  // Form Components
  {
    id: 'form',
    name: 'Form',
    description: 'Contact or signup form',
    icon: FileText,
    category: 'forms',
    color: 'bg-red-500',
  },
];

interface DraggableComponentProps {
  component: ComponentItem;
}

function DraggableComponent({ component }: DraggableComponentProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: `new-${component.id}`,
    data: {
      type: component.id,
      name: component.name,
    },
  });

  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
  } : undefined;

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`
        p-4 bg-white border border-gray-200 rounded-lg cursor-grab shadow-sm hover:shadow-md transition-all
        ${isDragging ? 'opacity-50 shadow-lg' : ''}
      `}
    >
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-8 h-8 ${component.color} rounded-lg flex items-center justify-center`}>
          <component.icon className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 truncate">
            {component.name}
          </h4>
        </div>
      </div>
      <p className="text-sm text-gray-600 leading-relaxed">
        {component.description}
      </p>
    </motion.div>
  );
}

interface ComponentLibraryProps {
  className?: string;
}

export function ComponentLibrary({ className = '' }: ComponentLibraryProps) {
  const [activeCategory, setActiveCategory] = React.useState<ComponentItem['category'] | 'all'>('all');

  const categories = [
    { id: 'all', name: 'All', icon: Grid3X3 },
    { id: 'basic', name: 'Basic', icon: Box },
    { id: 'layout', name: 'Layout', icon: Layout },
    { id: 'content', name: 'Content', icon: Type },
    { id: 'media', name: 'Media', icon: Image },
    { id: 'forms', name: 'Forms', icon: FileText },
    { id: 'advanced', name: 'Advanced', icon: Layers },
  ] as const;

  const filteredComponents = componentLibrary.filter(
    component => activeCategory === 'all' || component.category === activeCategory
  );

  return (
    <div className={`bg-white border-r border-gray-200 h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Components
        </h2>
        <p className="text-sm text-gray-600">
          Drag components to the canvas
        </p>
      </div>

      {/* Category Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex overflow-x-auto scrollbar-hide">
          {categories.map((category) => {
            const Icon = category.icon;
            const isActive = activeCategory === category.id;
            
            return (
              <button
                key={category.id}
                onClick={() => setActiveCategory(category.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap
                  ${isActive
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }
                `}
              >
                <Icon className="w-4 h-4" />
                {category.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Components Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="grid grid-cols-1 gap-3">
          {filteredComponents.map((component) => (
            <DraggableComponent
              key={component.id}
              component={component}
            />
          ))}
        </div>
        
        {filteredComponents.length === 0 && (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <Box className="w-6 h-6 text-gray-400" />
            </div>
            <p className="text-gray-500">
              No components in this category
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-center">
          <p className="text-xs text-gray-500 mb-2">
            {filteredComponents.length} component{filteredComponents.length !== 1 ? 's' : ''} available
          </p>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Request Component
          </motion.button>
        </div>
      </div>
    </div>
  );
}