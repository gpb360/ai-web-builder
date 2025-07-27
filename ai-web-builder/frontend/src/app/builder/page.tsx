'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useBuilderStore } from '@/stores/builderStore';
import { DragDropCanvas } from '@/components/DragDropCanvas';
import { ComponentLibrary } from '@/components/ComponentLibrary';
import { TemplateLibrary } from '@/components/TemplateLibrary';
import { 
  Menu, 
  X, 
  Save, 
  Download, 
  Share2, 
  Settings,
  Layers,
  Palette,
  Wand2,
  Eye,
  Code
} from 'lucide-react';

export default function BuilderPage() {
  const { 
    sidebarOpen, 
    activePanel, 
    setSidebarOpen, 
    setActivePanel,
    elements,
    canvasMode,
    setCanvasMode
  } = useBuilderStore();

  const sidebarPanels = [
    { id: 'components', name: 'Components', icon: Layers },
    { id: 'templates', name: 'Templates', icon: Eye },
    { id: 'ai', name: 'AI Assistant', icon: Wand2 },
    { id: 'settings', name: 'Settings', icon: Settings },
  ] as const;

  const renderSidebarContent = () => {
    switch (activePanel) {
      case 'components':
        return <ComponentLibrary />;
      
      case 'templates':
        return <TemplateLibrary />;
      
      case 'ai':
        return (
          <div className="p-4">
            <h3 className="font-semibold mb-4">AI Assistant</h3>
            <p className="text-gray-600 text-sm">
              AI-powered component generation coming soon...
            </p>
          </div>
        );
      
      case 'settings':
        return (
          <div className="p-4">
            <h3 className="font-semibold mb-4">Settings</h3>
            <p className="text-gray-600 text-sm">
              Project settings coming soon...
            </p>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="h-screen bg-gray-100 flex flex-col">
      {/* Top Navigation */}
      <div className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-4 z-30">
        {/* Left Side */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Layers className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">
                Web Builder
              </h1>
              <p className="text-xs text-gray-500">
                {elements.length} element{elements.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>

        {/* Center - Mode Toggle */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setCanvasMode('design')}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all
              ${canvasMode === 'design'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <Palette className="w-4 h-4" />
            Design
          </button>
          <button
            onClick={() => setCanvasMode('preview')}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all
              ${canvasMode === 'preview'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <Eye className="w-4 h-4" />
            Preview
          </button>
        </div>

        {/* Right Side */}
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="View code"
          >
            <Code className="w-5 h-5 text-gray-600" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Share"
          >
            <Share2 className="w-5 h-5 text-gray-600" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            title="Download"
          >
            <Download className="w-5 h-5 text-gray-600" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save
          </motion.button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex relative">
        {/* Sidebar */}
        <motion.div
          initial={false}
          animate={{
            width: sidebarOpen ? 320 : 0,
            opacity: sidebarOpen ? 1 : 0,
          }}
          transition={{ duration: 0.2, ease: 'easeInOut' }}
          className="bg-white border-r border-gray-200 overflow-hidden z-20"
        >
          {sidebarOpen && (
            <div className="w-80 h-full flex flex-col">
              {/* Sidebar Tabs */}
              <div className="border-b border-gray-200 flex">
                {sidebarPanels.map((panel) => {
                  const Icon = panel.icon;
                  const isActive = activePanel === panel.id;
                  
                  return (
                    <button
                      key={panel.id}
                      onClick={() => setActivePanel(panel.id)}
                      className={`
                        flex-1 flex flex-col items-center gap-1 py-3 px-2 text-xs font-medium transition-all
                        ${isActive
                          ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-500'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                        }
                      `}
                    >
                      <Icon className="w-4 h-4" />
                      {panel.name}
                    </button>
                  );
                })}
              </div>

              {/* Sidebar Content */}
              <div className="flex-1 overflow-hidden">
                {renderSidebarContent()}
              </div>
            </div>
          )}
        </motion.div>

        {/* Canvas Area */}
        <DragDropCanvas className="flex-1" />
      </div>
    </div>
  );
}