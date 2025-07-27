'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useBuilderStore } from '@/stores/builderStore';
import { 
  Copy, 
  Trash2, 
  Edit3, 
  Move, 
  Layers,
  Palette,
  Type,
  Layout
} from 'lucide-react';

interface ElementToolbarProps {
  elementId: string;
}

export function ElementToolbar({ elementId }: ElementToolbarProps) {
  const { 
    getElementById, 
    updateElement, 
    deleteElement, 
    duplicateElement,
    selectElement 
  } = useBuilderStore();

  const element = getElementById(elementId);

  if (!element) return null;

  const handleDelete = () => {
    deleteElement(elementId);
    selectElement(null);
  };

  const handleDuplicate = () => {
    duplicateElement(elementId);
  };

  const handleStyleChange = (property: string, value: string) => {
    updateElement(elementId, {
      styles: {
        ...element.styles,
        [property]: value,
      },
    });
  };

  const handleContentChange = (content: string) => {
    updateElement(elementId, { content });
  };

  const handleNameChange = (name: string) => {
    updateElement(elementId, { name });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-50"
    >
      <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-4 min-w-[600px]">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <Layers className="w-4 h-4 text-white" />
            </div>
            <div>
              <input
                type="text"
                value={element.name}
                onChange={(e) => handleNameChange(e.target.value)}
                className="font-semibold text-gray-900 bg-transparent border-none outline-none focus:bg-gray-50 rounded px-1"
              />
              <p className="text-sm text-gray-500 capitalize">{element.type} element</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleDuplicate}
              className="p-2 rounded hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition-colors"
              title="Duplicate element"
            >
              <Copy className="w-4 h-4" />
            </button>
            <button
              onClick={handleDelete}
              className="p-2 rounded hover:bg-red-50 text-red-500 hover:text-red-700 transition-colors"
              title="Delete element"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-4">
          <button className="px-4 py-2 border-b-2 border-blue-500 text-blue-600 font-medium">
            <div className="flex items-center gap-2">
              <Edit3 className="w-4 h-4" />
              Content
            </div>
          </button>
          <button className="px-4 py-2 text-gray-600 hover:text-gray-900">
            <div className="flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Style
            </div>
          </button>
          <button className="px-4 py-2 text-gray-600 hover:text-gray-900">
            <div className="flex items-center gap-2">
              <Layout className="w-4 h-4" />
              Layout
            </div>
          </button>
        </div>

        {/* Content Tab */}
        <div className="space-y-4">
          {/* Content Editor */}
          {(element.type === 'text' || element.type === 'button' || element.type === 'hero') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Type className="w-4 h-4 inline mr-1" />
                Content
              </label>
              {element.type === 'text' ? (
                <textarea
                  value={element.content}
                  onChange={(e) => handleContentChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  rows={3}
                  placeholder="Enter your text content..."
                />
              ) : (
                <input
                  type="text"
                  value={element.content}
                  onChange={(e) => handleContentChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder={element.type === 'button' ? 'Button text' : 'Hero title'}
                />
              )}
            </div>
          )}

          {/* Quick Style Controls */}
          <div className="grid grid-cols-2 gap-4">
            {/* Background Color */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Background
              </label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={element.styles.backgroundColor || '#ffffff'}
                  onChange={(e) => handleStyleChange('backgroundColor', e.target.value)}
                  className="w-10 h-8 border border-gray-300 rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={element.styles.backgroundColor || '#ffffff'}
                  onChange={(e) => handleStyleChange('backgroundColor', e.target.value)}
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="#ffffff"
                />
              </div>
            </div>

            {/* Text Color */}
            {element.type !== 'container' && element.type !== 'image' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Text Color
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={element.styles.color || '#000000'}
                    onChange={(e) => handleStyleChange('color', e.target.value)}
                    className="w-10 h-8 border border-gray-300 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={element.styles.color || '#000000'}
                    onChange={(e) => handleStyleChange('color', e.target.value)}
                    className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="#000000"
                  />
                </div>
              </div>
            )}

            {/* Font Size */}
            {element.type !== 'container' && element.type !== 'image' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Font Size
                </label>
                <div className="flex gap-2">
                  <input
                    type="range"
                    min="10"
                    max="72"
                    value={parseInt(element.styles.fontSize?.replace('px', '') || '16')}
                    onChange={(e) => handleStyleChange('fontSize', `${e.target.value}px`)}
                    className="flex-1"
                  />
                  <span className="text-sm text-gray-600 min-w-[3rem]">
                    {element.styles.fontSize || '16px'}
                  </span>
                </div>
              </div>
            )}

            {/* Padding */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Padding
              </label>
              <input
                type="text"
                value={element.styles.padding || '0'}
                onChange={(e) => handleStyleChange('padding', e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                placeholder="20px or 20px 10px"
              />
            </div>

            {/* Border Radius */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Border Radius
              </label>
              <div className="flex gap-2">
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={parseInt(element.styles.borderRadius?.replace('px', '') || '0')}
                  onChange={(e) => handleStyleChange('borderRadius', `${e.target.value}px`)}
                  className="flex-1"
                />
                <span className="text-sm text-gray-600 min-w-[3rem]">
                  {element.styles.borderRadius || '0px'}
                </span>
              </div>
            </div>

            {/* Width */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Width
              </label>
              <select
                value={element.styles.width || '100%'}
                onChange={(e) => handleStyleChange('width', e.target.value)}
                className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="auto">Auto</option>
                <option value="100%">Full Width</option>
                <option value="50%">Half Width</option>
                <option value="33.333%">Third Width</option>
                <option value="25%">Quarter Width</option>
                <option value="fit-content">Fit Content</option>
              </select>
            </div>
          </div>

          {/* Element-specific controls */}
          {element.type === 'button' && (
            <div className="border-t border-gray-200 pt-4">
              <h4 className="font-medium text-gray-900 mb-3">Button Settings</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Link URL
                  </label>
                  <input
                    type="text"
                    value={element.props.href || ''}
                    onChange={(e) => updateElement(elementId, {
                      props: { ...element.props, href: e.target.value }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Target
                  </label>
                  <select
                    value={element.props.target || '_self'}
                    onChange={(e) => updateElement(elementId, {
                      props: { ...element.props, target: e.target.value }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="_self">Same Window</option>
                    <option value="_blank">New Window</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {element.type === 'image' && (
            <div className="border-t border-gray-200 pt-4">
              <h4 className="font-medium text-gray-900 mb-3">Image Settings</h4>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Image URL
                  </label>
                  <input
                    type="text"
                    value={element.props.src || ''}
                    onChange={(e) => updateElement(elementId, {
                      props: { ...element.props, src: e.target.value }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="https://example.com/image.jpg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Alt Text
                  </label>
                  <input
                    type="text"
                    value={element.props.alt || ''}
                    onChange={(e) => updateElement(elementId, {
                      props: { ...element.props, alt: e.target.value }
                    })}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe the image"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}