'use client';

import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { motion } from 'framer-motion';
import { ComponentElement } from '@/stores/builderStore';
import { useBuilderStore } from '@/stores/builderStore';

interface CanvasElementProps {
  element: ComponentElement;
  isSelected: boolean;
  isHovered: boolean;
  onSelect: () => void;
  onHover: () => void;
  canvasMode: 'design' | 'preview';
}

export function CanvasElement({
  element,
  isSelected,
  isHovered,
  onSelect,
  onHover,
  canvasMode,
}: CanvasElementProps) {
  const { getElementChildren } = useBuilderStore();
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: element.id,
    disabled: canvasMode === 'preview',
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const children = getElementChildren(element.id);

  const renderElement = () => {
    const combinedStyles = {
      ...element.styles,
      ...(canvasMode === 'design' && {
        outline: isSelected 
          ? '2px solid #3b82f6' 
          : isHovered 
          ? '2px solid #93c5fd' 
          : 'none',
        outlineOffset: '2px',
      }),
    };

    const handleClick = (e: React.MouseEvent) => {
      if (canvasMode === 'design') {
        e.stopPropagation();
        onSelect();
      }
    };

    const handleMouseEnter = (e: React.MouseEvent) => {
      if (canvasMode === 'design') {
        e.stopPropagation();
        onHover();
      }
    };

    switch (element.type) {
      case 'container':
        return (
          <div
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative min-h-[50px] group"
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            {children.map((child) => (
              <CanvasElement
                key={child.id}
                element={child}
                isSelected={false}
                isHovered={false}
                onSelect={() => {}}
                onHover={() => {}}
                canvasMode={canvasMode}
              />
            ))}
            {children.length === 0 && canvasMode === 'design' && (
              <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                Drop components here
              </div>
            )}
          </div>
        );

      case 'text':
        return (
          <div
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group"
            contentEditable={canvasMode === 'design' && isSelected}
            suppressContentEditableWarning={true}
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            {element.content}
          </div>
        );

      case 'button':
        return (
          <button
            style={combinedStyles}
            onClick={canvasMode === 'design' ? handleClick : undefined}
            onMouseEnter={handleMouseEnter}
            className="relative group transition-all hover:opacity-80"
            disabled={canvasMode === 'design'}
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            {element.content}
          </button>
        );

      case 'image':
        return (
          <div
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group overflow-hidden"
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            {element.props.src ? (
              <img
                src={element.props.src}
                alt={element.props.alt || ''}
                style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              />
            ) : (
              <div 
                className="w-full h-full bg-gray-200 flex items-center justify-center text-gray-500"
              >
                <div className="text-center">
                  <div className="text-4xl mb-2">🖼️</div>
                  <div className="text-sm">Image placeholder</div>
                </div>
              </div>
            )}
          </div>
        );

      case 'hero':
        return (
          <section
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group"
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            <div className="max-w-4xl mx-auto">
              <h1 className="text-4xl md:text-6xl font-bold mb-6">
                {element.content || 'Hero Title'}
              </h1>
              <p className="text-xl md:text-2xl mb-8 opacity-90">
                Your compelling hero subtitle goes here
              </p>
              <div className="space-x-4">
                <button className="bg-white text-gray-900 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
                  Get Started
                </button>
                <button className="border border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-gray-900 transition-colors">
                  Learn More
                </button>
              </div>
            </div>
          </section>
        );

      case 'card':
        return (
          <div
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group bg-white border border-gray-200 rounded-lg shadow-sm p-6"
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            <h3 className="text-lg font-semibold mb-2">Card Title</h3>
            <p className="text-gray-600 mb-4">
              {element.content || 'Card description goes here. Add your content to make this card meaningful.'}
            </p>
            <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
              Action
            </button>
          </div>
        );

      case 'form':
        return (
          <form
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group space-y-4"
            onSubmit={(e) => canvasMode === 'design' && e.preventDefault()}
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your name"
                disabled={canvasMode === 'design'}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your email"
                disabled={canvasMode === 'design'}
              />
            </div>
            <button
              type="submit"
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50"
              disabled={canvasMode === 'design'}
            >
              Submit
            </button>
          </form>
        );

      case 'navigation':
        return (
          <nav
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group bg-white border-b border-gray-200"
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="font-bold text-xl text-gray-900">
                  Logo
                </div>
                <div className="hidden md:flex space-x-8">
                  <a href="#" className="text-gray-700 hover:text-gray-900 transition-colors">Home</a>
                  <a href="#" className="text-gray-700 hover:text-gray-900 transition-colors">About</a>
                  <a href="#" className="text-gray-700 hover:text-gray-900 transition-colors">Services</a>
                  <a href="#" className="text-gray-700 hover:text-gray-900 transition-colors">Contact</a>
                </div>
                <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors">
                  Get Started
                </button>
              </div>
            </div>
          </nav>
        );

      default:
        return (
          <div
            style={combinedStyles}
            onClick={handleClick}
            onMouseEnter={handleMouseEnter}
            className="relative group bg-gray-100 border border-gray-300 rounded p-4"
          >
            {canvasMode === 'design' && isHovered && !isSelected && (
              <div className="absolute -top-6 left-0 bg-gray-800 text-white text-xs px-2 py-1 rounded z-10">
                {element.name}
              </div>
            )}
            Unknown element type: {element.type}
          </div>
        );
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...(canvasMode === 'design' ? listeners : {})}
      className={`${isDragging ? 'z-50' : ''}`}
    >
      {canvasMode === 'design' && isSelected && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute -top-8 left-0 bg-blue-500 text-white text-xs px-2 py-1 rounded z-20 font-medium"
        >
          {element.name}
        </motion.div>
      )}
      {renderElement()}
    </div>
  );
}