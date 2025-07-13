'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Editor } from '@monaco-editor/react';
import { Eye, Code, Copy, Download, ExternalLink, Settings } from 'lucide-react';

interface ComponentPreviewProps {
  code: string;
  componentType: 'react' | 'html' | 'vue';
  className?: string;
}

export function ComponentPreview({ code, componentType, className = '' }: ComponentPreviewProps) {
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  const handleDownload = () => {
    const fileExtensions = {
      react: 'tsx',
      html: 'html',
      vue: 'vue'
    };
    
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `component.${fileExtensions[componentType]}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getLanguage = () => {
    switch (componentType) {
      case 'react':
        return 'typescript';
      case 'html':
        return 'html';
      case 'vue':
        return 'javascript';
      default:
        return 'typescript';
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center gap-4">
          {/* Tab Navigation */}
          <div className="flex bg-white rounded-lg p-1 border border-gray-200">
            <button
              onClick={() => setActiveTab('preview')}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all
                ${activeTab === 'preview'
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
                }
              `}
            >
              <Eye className="w-4 h-4" />
              Preview
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`
                flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all
                ${activeTab === 'code'
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
                }
              `}
            >
              <Code className="w-4 h-4" />
              Code
            </button>
          </div>

          {/* Component Type Badge */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500">Type:</span>
            <span className={`
              px-2 py-1 rounded-md text-xs font-medium
              ${componentType === 'react' ? 'bg-blue-100 text-blue-700' : ''}
              ${componentType === 'html' ? 'bg-orange-100 text-orange-700' : ''}
              ${componentType === 'vue' ? 'bg-green-100 text-green-700' : ''}
            `}>
              {componentType.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCopy}
            className={`
              p-2 rounded-lg transition-all duration-200
              ${copied 
                ? 'bg-green-500 text-white' 
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
              }
            `}
            title="Copy code"
          >
            <Copy className="w-4 h-4" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleDownload}
            className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg transition-all duration-200"
            title="Download code"
          >
            <Download className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* Content */}
      <div className="relative">
        <AnimatePresence mode="wait">
          {activeTab === 'preview' && (
            <motion.div
              key="preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="p-6"
            >
              <ComponentRenderer code={code} componentType={componentType} />
            </motion.div>
          )}

          {activeTab === 'code' && (
            <motion.div
              key="code"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="relative"
            >
              <Editor
                height="400px"
                language={getLanguage()}
                value={code}
                theme="vs"
                options={{
                  readOnly: true,
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontFamily: 'JetBrains Mono, Monaco, Consolas, monospace',
                  fontSize: 13,
                  lineNumbers: 'on',
                  folding: true,
                  wordWrap: 'on',
                  automaticLayout: true
                }}
              />
              
              {/* Copy overlay */}
              {copied && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.8 }}
                  className="absolute inset-0 bg-green-500 bg-opacity-90 flex items-center justify-center"
                >
                  <div className="bg-white rounded-lg p-4 shadow-lg">
                    <p className="text-green-600 font-semibold">Code copied to clipboard!</p>
                  </div>
                </motion.div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-4">
            <span>Lines: {code.split('\n').length}</span>
            <span>Characters: {code.length}</span>
            <span>Language: {getLanguage()}</span>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-xs">Ready for production</span>
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Component renderer for previewing the generated code
function ComponentRenderer({ code, componentType }: { code: string; componentType: string }) {
  if (componentType === 'html') {
    return (
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <iframe
          srcDoc={code}
          className="w-full h-64 border-none"
          title="Component Preview"
          sandbox="allow-scripts"
        />
      </div>
    );
  }

  // For React and Vue, show a styled code preview since we can't easily render them
  return (
    <div className="space-y-4">
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
        <div className="text-center text-gray-600">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <Code className="w-8 h-8 text-white" />
          </div>
          <h4 className="text-lg font-semibold mb-2">Component Preview</h4>
          <p className="text-sm mb-4">
            Your {componentType.toUpperCase()} component is ready! 
            Switch to the Code tab to see the full implementation.
          </p>
          
          {/* Mock component preview */}
          <div className="max-w-md mx-auto">
            <MockComponentPreview componentType={componentType} />
          </div>
        </div>
      </div>

      {/* Component Usage Example */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h5 className="font-semibold text-blue-800 mb-2">How to use this component:</h5>
        <div className="text-sm text-blue-700 space-y-1">
          {componentType === 'react' && (
            <>
              <p>1. Save the code as a .tsx file in your components folder</p>
              <p>2. Import and use: <code className="bg-blue-100 px-1 rounded">{'<GeneratedComponent />'}</code></p>
              <p>3. Customize props and styling as needed</p>
            </>
          )}
          {componentType === 'html' && (
            <>
              <p>1. Save the code as an .html file</p>
              <p>2. Open in your browser or integrate into your website</p>
              <p>3. Customize styles and content as needed</p>
            </>
          )}
          {componentType === 'vue' && (
            <>
              <p>1. Save the code as a .vue file in your components folder</p>
              <p>2. Import and use in your Vue templates</p>
              <p>3. Customize props and methods as needed</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// Mock visual preview of the component
function MockComponentPreview({ componentType }: { componentType: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
        <h3 className="text-lg font-semibold text-gray-800">Generated Component</h3>
      </div>
      <p className="text-gray-600 mb-4">
        This is a preview of your {componentType} component. The actual implementation 
        includes proper styling, interactivity, and responsive design.
      </p>
      <div className="flex gap-2">
        <button className="px-4 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition-colors">
          Primary Action
        </button>
        <button className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300 transition-colors">
          Secondary
        </button>
      </div>
    </div>
  );
}