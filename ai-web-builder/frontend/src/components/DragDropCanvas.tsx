'use client';

import React, { useCallback, useRef } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragStartEvent,
  DragOverEvent,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { motion, AnimatePresence } from 'framer-motion';
import { useBuilderStore } from '@/stores/builderStore';
import { CanvasElement } from './CanvasElement';
import { ElementToolbar } from './ElementToolbar';
import { DropIndicator } from './DropIndicator';
import { 
  Eye, 
  Edit3, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Redo,
  Grid3X3,
  Monitor,
  Tablet,
  Smartphone
} from 'lucide-react';

interface DragDropCanvasProps {
  className?: string;
}

type ViewportSize = 'mobile' | 'tablet' | 'desktop';

export function DragDropCanvas({ className = '' }: DragDropCanvasProps) {
  const {
    elements,
    selectedElementId,
    hoveredElementId,
    canvasMode,
    zoom,
    draggedElementType,
    isDropTarget,
    selectElement,
    hoverElement,
    addElement,
    moveElement,
    setCanvasMode,
    setZoom,
    setDraggedElementType,
    setIsDropTarget,
    undo,
    redo,
    history,
    historyIndex,
  } = useBuilderStore();

  const canvasRef = useRef<HTMLDivElement>(null);
  const [activeId, setActiveId] = React.useState<string | null>(null);
  const [viewport, setViewport] = React.useState<ViewportSize>('desktop');
  const [showGrid, setShowGrid] = React.useState(true);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const rootElements = elements.filter(el => el.parentId === null);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const { active } = event;
    setActiveId(active.id as string);
    
    // Check if this is a new element being dragged from the component library
    if (typeof active.id === 'string' && active.id.startsWith('new-')) {
      const elementType = active.id.replace('new-', '');
      setDraggedElementType(elementType);
    }
  }, [setDraggedElementType]);

  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { over } = event;
    setIsDropTarget(!!over);
  }, [setIsDropTarget]);

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    
    setActiveId(null);
    setDraggedElementType(null);
    setIsDropTarget(false);

    if (!over) return;

    // Handle new element creation
    if (typeof active.id === 'string' && active.id.startsWith('new-')) {
      const elementType = active.id.replace('new-', '') as any;
      const dropTargetId = over.id === 'canvas-root' ? null : over.id as string;
      
      const newElement = createElementFromType(elementType, dropTargetId);
      if (newElement) {
        addElement(newElement);
      }
      return;
    }

    // Handle existing element movement
    const activeElement = elements.find(el => el.id === active.id);
    const overElement = elements.find(el => el.id === over.id);
    
    if (activeElement && active.id !== over.id) {
      const newParentId = over.id === 'canvas-root' ? null : over.id as string;
      const newOrder = overElement ? overElement.order + 1 : 0;
      
      moveElement(activeElement.id, newParentId, newOrder);
    }
  }, [elements, addElement, moveElement, setDraggedElementType, setIsDropTarget]);

  const createElementFromType = useCallback((type: string, parentId: string | null) => {
    const baseElement = {
      type: type as any,
      name: `${type.charAt(0).toUpperCase() + type.slice(1)} Component`,
      content: getDefaultContent(type),
      styles: getDefaultStyles(type),
      props: getDefaultProps(type),
      children: [],
      parentId,
    };

    return baseElement;
  }, []);

  const getViewportDimensions = () => {
    switch (viewport) {
      case 'mobile':
        return { width: 375, height: 812 };
      case 'tablet':
        return { width: 768, height: 1024 };
      case 'desktop':
        return { width: 1200, height: 800 };
    }
  };

  const dimensions = getViewportDimensions();
  const scaledWidth = (dimensions.width * zoom) / 100;
  const scaledHeight = (dimensions.height * zoom) / 100;

  return (
    <div className={`flex-1 bg-gray-50 relative overflow-hidden ${className}`}>
      {/* Canvas Toolbar */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
        <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-2 flex items-center gap-2">
          {/* Mode Toggle */}
          <div className="flex bg-gray-100 rounded-md p-1">
            <button
              onClick={() => setCanvasMode('design')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
                canvasMode === 'design'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Edit3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setCanvasMode('preview')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
                canvasMode === 'preview'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Eye className="w-4 h-4" />
            </button>
          </div>

          <div className="w-px h-6 bg-gray-300" />

          {/* Viewport Controls */}
          <div className="flex gap-1">
            {(['mobile', 'tablet', 'desktop'] as ViewportSize[]).map((size) => {
              const Icon = size === 'mobile' ? Smartphone : size === 'tablet' ? Tablet : Monitor;
              return (
                <button
                  key={size}
                  onClick={() => setViewport(size)}
                  className={`p-2 rounded transition-all ${
                    viewport === size
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  title={`${size.charAt(0).toUpperCase() + size.slice(1)} view`}
                >
                  <Icon className="w-4 h-4" />
                </button>
              );
            })}
          </div>

          <div className="w-px h-6 bg-gray-300" />

          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoom(zoom - 10)}
              disabled={zoom <= 25}
              className="p-2 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm font-medium text-gray-700 min-w-[3rem] text-center">
              {zoom}%
            </span>
            <button
              onClick={() => setZoom(zoom + 10)}
              disabled={zoom >= 200}
              className="p-2 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>

          <div className="w-px h-6 bg-gray-300" />

          {/* Grid Toggle */}
          <button
            onClick={() => setShowGrid(!showGrid)}
            className={`p-2 rounded transition-all ${
              showGrid
                ? 'bg-purple-500 text-white'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title="Toggle grid"
          >
            <Grid3X3 className="w-4 h-4" />
          </button>

          <div className="w-px h-6 bg-gray-300" />

          {/* History Controls */}
          <button
            onClick={undo}
            disabled={historyIndex <= 0}
            className="p-2 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Undo"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={redo}
            disabled={historyIndex >= history.length - 1}
            className="p-2 rounded text-gray-600 hover:text-gray-900 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Redo"
          >
            <Redo className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas Container */}
      <div 
        className="flex-1 overflow-auto p-8 flex items-center justify-center"
        style={{ minHeight: '100vh' }}
      >
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
        >
          {/* Canvas */}
          <div
            ref={canvasRef}
            className={`relative bg-white shadow-xl border border-gray-200 overflow-hidden ${
              canvasMode === 'preview' ? 'pointer-events-none' : ''
            }`}
            style={{
              width: scaledWidth,
              height: scaledHeight,
              minHeight: scaledHeight,
              transform: `scale(${zoom / 100})`,
              transformOrigin: 'center',
            }}
          >
            {/* Grid Overlay */}
            {showGrid && canvasMode === 'design' && (
              <div
                className="absolute inset-0 pointer-events-none opacity-20"
                style={{
                  backgroundImage: `
                    linear-gradient(rgba(59, 130, 246, 0.3) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(59, 130, 246, 0.3) 1px, transparent 1px)
                  `,
                  backgroundSize: '20px 20px',
                }}
              />
            )}

            {/* Drop Zone */}
            <div
              id="canvas-root"
              className={`w-full h-full relative ${
                isDropTarget ? 'bg-blue-50 border-2 border-dashed border-blue-300' : ''
              }`}
              onMouseLeave={() => hoverElement(null)}
            >
              <SortableContext 
                items={rootElements.map(el => el.id)} 
                strategy={verticalListSortingStrategy}
              >
                {rootElements.map((element) => (
                  <CanvasElement
                    key={element.id}
                    element={element}
                    isSelected={selectedElementId === element.id}
                    isHovered={hoveredElementId === element.id}
                    onSelect={() => selectElement(element.id)}
                    onHover={() => hoverElement(element.id)}
                    canvasMode={canvasMode}
                  />
                ))}
              </SortableContext>

              {/* Empty State */}
              {rootElements.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center"
                  >
                    <div className="w-24 h-24 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                      <Grid3X3 className="w-8 h-8 text-gray-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-600 mb-2">
                      Start Building
                    </h3>
                    <p className="text-gray-500 max-w-sm">
                      Drag components from the sidebar to start building your page
                    </p>
                  </motion.div>
                </div>
              )}
            </div>

            {/* Drop Indicator */}
            <DropIndicator />
          </div>

          {/* Drag Overlay */}
          <DragOverlay>
            {activeId && elements.find(el => el.id === activeId) && (
              <div className="bg-white border border-gray-300 rounded-lg p-4 shadow-lg opacity-80">
                <span className="text-sm font-medium text-gray-700">
                  {elements.find(el => el.id === activeId)?.name}
                </span>
              </div>
            )}
          </DragOverlay>
        </DndContext>
      </div>

      {/* Element Toolbar */}
      <AnimatePresence>
        {selectedElementId && canvasMode === 'design' && (
          <ElementToolbar elementId={selectedElementId} />
        )}
      </AnimatePresence>
    </div>
  );
}

// Helper functions for creating default elements
function getDefaultContent(type: string): string {
  switch (type) {
    case 'text':
      return 'Your text here';
    case 'button':
      return 'Click me';
    case 'hero':
      return 'Hero Section';
    case 'card':
      return 'Card Content';
    default:
      return '';
  }
}

function getDefaultStyles(type: string): any {
  const baseStyles = {
    position: 'relative',
    width: '100%',
  };

  switch (type) {
    case 'container':
      return {
        ...baseStyles,
        padding: '20px',
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        minHeight: '100px',
      };
    case 'text':
      return {
        ...baseStyles,
        fontSize: '16px',
        color: '#374151',
        lineHeight: '1.5',
      };
    case 'button':
      return {
        ...baseStyles,
        padding: '12px 24px',
        backgroundColor: '#3b82f6',
        color: '#ffffff',
        borderRadius: '6px',
        border: 'none',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: '500',
        display: 'inline-block',
        width: 'auto',
      };
    case 'image':
      return {
        ...baseStyles,
        width: '100%',
        height: '200px',
        backgroundColor: '#f3f4f6',
        borderRadius: '8px',
        objectFit: 'cover',
      };
    case 'hero':
      return {
        ...baseStyles,
        padding: '80px 20px',
        backgroundColor: '#1f2937',
        color: '#ffffff',
        textAlign: 'center',
        minHeight: '400px',
      };
    default:
      return baseStyles;
  }
}

function getDefaultProps(type: string): any {
  switch (type) {
    case 'button':
      return {
        href: '#',
        target: '_self',
      };
    case 'image':
      return {
        src: '/placeholder-image.jpg',
        alt: 'Placeholder image',
      };
    default:
      return {};
  }
}