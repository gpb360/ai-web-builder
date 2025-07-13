'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Eye, Zap, Image as ImageIcon, AlertCircle, CheckCircle, Loader } from 'lucide-react';

interface ImageAnalysis {
  width: number;
  height: number;
  format: string;
  size_kb: number;
  aspect_ratio: number;
  layout_hint: string;
  responsive_hint: string;
  component_type: string;
  suggested_complexity: number;
  layout_elements: string[];
  color_palette: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
}

interface ImageAnalyzerProps {
  onAnalysisComplete?: (analysis: ImageAnalysis, file: File) => void;
  className?: string;
}

export function ImageAnalyzer({ onAnalysisComplete, className = '' }: ImageAnalyzerProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<ImageAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const handleFileSelect = async (file: File) => {
    setError(null);
    setSelectedFile(file);
    
    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    
    // Auto-analyze
    await analyzeImage(file);
  };

  const analyzeImage = async (file: File) => {
    if (!file) return;
    
    setIsAnalyzing(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('image', file);
      
      const response = await fetch('/api/ai/analyze-image', {
        method: 'POST',
        body: formData,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        const analysisData = {
          ...data.analysis,
          ...data.suggestions
        };
        setAnalysis(analysisData);
        
        if (onAnalysisComplete) {
          onAnalysisComplete(analysisData, file);
        }
      } else {
        throw new Error('Analysis failed on server');
      }
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      setError(errorMessage);
      console.error('Image analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));
    
    if (imageFile) {
      handleFileSelect(imageFile);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 shadow-sm ${className}`}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
          <Eye className="w-4 h-4 text-purple-600" />
        </div>
        <h4 className="font-semibold text-gray-800">Image Analysis</h4>
      </div>

      {!selectedFile ? (
        // Upload Area
        <div
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors cursor-pointer"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => document.getElementById('image-input')?.click()}
        >
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center">
              <Upload className="w-8 h-8 text-gray-400" />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-800 mb-1">Upload Component Image</p>
              <p className="text-sm text-gray-500">Drop an image here or click to browse</p>
            </div>
            <div className="text-xs text-gray-400">
              Supports JPG, PNG, WebP • Max 10MB
            </div>
          </div>
          <input
            id="image-input"
            type="file"
            accept="image/*"
            onChange={handleFileInput}
            className="hidden"
          />
        </div>
      ) : (
        // Analysis Results
        <div className="space-y-6">
          {/* Image Preview */}
          <div className="flex items-start gap-4">
            <div className="w-24 h-24 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
              {previewUrl && (
                <img
                  src={previewUrl}
                  alt="Upload preview"
                  className="w-full h-full object-cover"
                />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h5 className="font-medium text-gray-800 truncate">{selectedFile.name}</h5>
              <p className="text-sm text-gray-500 mb-2">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setAnalysis(null);
                  setError(null);
                  if (previewUrl) {
                    URL.revokeObjectURL(previewUrl);
                    setPreviewUrl(null);
                  }
                }}
                className="text-sm text-purple-600 hover:text-purple-700 transition-colors"
              >
                Upload different image
              </button>
            </div>
          </div>

          {/* Analysis Status */}
          <AnimatePresence mode="wait">
            {isAnalyzing && (
              <motion.div
                key="analyzing"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg"
              >
                <Loader className="w-5 h-5 text-blue-600 animate-spin" />
                <div>
                  <p className="font-medium text-blue-800">Analyzing Image...</p>
                  <p className="text-sm text-blue-600">Extracting design patterns and layout information</p>
                </div>
              </motion.div>
            )}

            {error && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg"
              >
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-red-800">Analysis Failed</p>
                  <p className="text-sm text-red-600">{error}</p>
                  <button
                    onClick={() => selectedFile && analyzeImage(selectedFile)}
                    className="text-sm text-red-600 hover:text-red-700 underline mt-1"
                  >
                    Try again
                  </button>
                </div>
              </motion.div>
            )}

            {analysis && !isAnalyzing && (
              <motion.div
                key="success"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-4"
              >
                {/* Success Header */}
                <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  <div>
                    <p className="font-medium text-green-800">Analysis Complete</p>
                    <p className="text-sm text-green-600">Ready to generate similar component</p>
                  </div>
                </div>

                {/* Analysis Results */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Image Properties */}
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h6 className="font-medium text-gray-700 mb-3">Image Properties</h6>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Dimensions:</span>
                        <span className="font-medium">{analysis.width}×{analysis.height}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Aspect Ratio:</span>
                        <span className="font-medium">{analysis.aspect_ratio}:1</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Format:</span>
                        <span className="font-medium">{analysis.format}</span>
                      </div>
                    </div>
                  </div>

                  {/* Component Suggestions */}
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h6 className="font-medium text-gray-700 mb-3">Component Suggestions</h6>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Type:</span>
                        <span className="font-medium">{analysis.component_type}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Complexity:</span>
                        <span className="font-medium">{analysis.suggested_complexity}/5</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Layout:</span>
                        <span className="font-medium">{analysis.layout_hint}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Layout Elements */}
                {analysis.layout_elements && analysis.layout_elements.length > 0 && (
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <h6 className="font-medium text-purple-800 mb-3">Detected Elements</h6>
                    <div className="flex flex-wrap gap-2">
                      {analysis.layout_elements.map((element, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-md"
                        >
                          {element}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Color Palette */}
                {analysis.color_palette && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h6 className="font-medium text-gray-700 mb-3">Extracted Color Palette</h6>
                    <div className="flex gap-3">
                      {Object.entries(analysis.color_palette).map(([name, color]) => (
                        <div key={name} className="text-center">
                          <div
                            className="w-8 h-8 rounded-lg border border-gray-300 mb-1"
                            style={{ backgroundColor: color }}
                          />
                          <span className="text-xs text-gray-600 capitalize">{name}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Responsive Hints */}
                <div className="p-4 bg-blue-50 rounded-lg">
                  <h6 className="font-medium text-blue-800 mb-2">Responsive Design Recommendations</h6>
                  <p className="text-sm text-blue-700">{analysis.responsive_hint}</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}