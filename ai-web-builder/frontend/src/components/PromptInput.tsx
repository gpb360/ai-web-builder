'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Upload, X, Image as ImageIcon } from 'lucide-react';

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  onImageUpload?: (file: File) => void;
  uploadedImage?: File | null;
  className?: string;
}

export function PromptInput({ 
  value, 
  onChange, 
  placeholder = "Describe your component...",
  onImageUpload,
  uploadedImage,
  className = ''
}: PromptInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [value]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));
    
    if (imageFile && onImageUpload) {
      onImageUpload(imageFile);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onImageUpload) {
      onImageUpload(file);
    }
  };

  const removeImage = () => {
    if (onImageUpload) {
      onImageUpload(null as any);
    }
  };

  const characterCount = value.length;
  const maxCharacters = 1000;
  const isNearLimit = characterCount > maxCharacters * 0.8;
  const isOverLimit = characterCount > maxCharacters;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Main Input Area */}
      <div
        className={`
          relative border-2 rounded-xl transition-all duration-200
          ${isFocused 
            ? 'border-blue-500 bg-blue-50/50' 
            : 'border-gray-200 bg-gray-50/50 hover:border-gray-300'
          }
          ${isDragging ? 'border-blue-500 bg-blue-50' : ''}
        `}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setIsDragging(false);
        }}
        onDrop={handleDrop}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={placeholder}
          className="w-full p-4 bg-transparent border-none outline-none resize-none min-h-[120px] text-gray-800 placeholder-gray-500"
          maxLength={maxCharacters}
        />

        {/* Upload Button */}
        {onImageUpload && (
          <div className="absolute top-4 right-4">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={`
                p-2 rounded-lg transition-all duration-200
                ${isFocused || isDragging
                  ? 'bg-blue-500 text-white shadow-lg'
                  : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                }
              `}
              title="Upload reference image"
            >
              <Upload className="w-4 h-4" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>
        )}
      </div>

      {/* Uploaded Image Preview */}
      {uploadedImage && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 10 }}
          className="relative bg-white border border-gray-200 rounded-lg p-3 flex items-center gap-3"
        >
          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
            <ImageIcon className="w-6 h-6 text-gray-500" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">
              {uploadedImage.name}
            </p>
            <p className="text-xs text-gray-500">
              {(uploadedImage.size / 1024).toFixed(1)} KB
            </p>
          </div>
          <button
            onClick={removeImage}
            className="p-1 text-gray-400 hover:text-red-500 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {/* Character Count and Tips */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          {isDragging && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-blue-600 font-medium"
            >
              Drop image here to add as reference
            </motion.span>
          )}
          {!isDragging && (
            <span className="text-gray-500">
              Try: "Create a responsive pricing card with hover effects and gradient background"
            </span>
          )}
        </div>
        
        <span className={`
          font-medium transition-colors
          ${isOverLimit 
            ? 'text-red-500' 
            : isNearLimit 
            ? 'text-yellow-500' 
            : 'text-gray-400'
          }
        `}>
          {characterCount}/{maxCharacters}
        </span>
      </div>

      {/* Quick Suggestions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {quickSuggestions.map((suggestion, index) => (
          <button
            key={index}
            onClick={() => onChange(suggestion)}
            className="text-left p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-sm text-gray-700 transition-colors"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}

const quickSuggestions = [
  "Responsive navigation menu with dropdown",
  "Pricing card with features and CTA button",
  "Dashboard widget with chart and metrics",
  "Contact form with validation",
  "Hero section with background image",
  "Product showcase with image gallery"
];