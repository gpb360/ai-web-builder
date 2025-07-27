'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useBuilderStore } from '@/stores/builderStore';
import { sampleTemplates, templateCategories, getTemplatesByCategory } from '@/data/templates';
import { 
  Eye, 
  Download, 
  Star, 
  Clock,
  Grid3X3,
  Search,
  Filter
} from 'lucide-react';

interface TemplateLibraryProps {
  className?: string;
}

export function TemplateLibrary({ className = '' }: TemplateLibraryProps) {
  const { loadTemplate, currentTemplate } = useBuilderStore();
  const [selectedCategory, setSelectedCategory] = React.useState('all');
  const [searchTerm, setSearchTerm] = React.useState('');

  const filteredTemplates = React.useMemo(() => {
    let templates = getTemplatesByCategory(selectedCategory);
    
    if (searchTerm) {
      templates = templates.filter(template =>
        template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    return templates;
  }, [selectedCategory, searchTerm]);

  const handleTemplateSelect = (templateId: string) => {
    const template = sampleTemplates.find(t => t.id === templateId);
    if (template) {
      loadTemplate(template);
    }
  };

  return (
    <div className={`bg-white h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          Templates
        </h2>
        <p className="text-sm text-gray-600">
          Choose from professionally designed templates
        </p>
      </div>

      {/* Search */}
      <div className="p-4 border-b border-gray-200">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="border-b border-gray-200">
        <div className="flex overflow-x-auto scrollbar-hide">
          {templateCategories.map((category) => {
            const isActive = selectedCategory === category.id;
            
            return (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`
                  flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap
                  ${isActive
                    ? 'border-blue-500 text-blue-600 bg-blue-50'
                    : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }
                `}
              >
                {category.name}
                <span className={`
                  text-xs px-2 py-0.5 rounded-full
                  ${isActive ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}
                `}>
                  {category.count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Templates Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {filteredTemplates.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {filteredTemplates.map((template) => (
              <motion.div
                key={template.id}
                whileHover={{ scale: 1.02 }}
                className={`
                  bg-white border rounded-lg overflow-hidden cursor-pointer transition-all shadow-sm hover:shadow-md
                  ${currentTemplate?.id === template.id ? 'border-blue-500 ring-2 ring-blue-100' : 'border-gray-200'}
                `}
                onClick={() => handleTemplateSelect(template.id)}
              >
                {/* Template Thumbnail */}
                <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Grid3X3 className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <span className="text-sm text-gray-500 font-medium">
                        {template.name}
                      </span>
                    </div>
                  </div>
                  
                  {/* Overlay on hover */}
                  <div className="absolute inset-0 bg-black bg-opacity-0 hover:bg-opacity-50 transition-all duration-300 flex items-center justify-center opacity-0 hover:opacity-100">
                    <div className="flex gap-2">
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-50"
                        onClick={(e) => {
                          e.stopPropagation();
                          // Preview functionality
                        }}
                      >
                        <Eye className="w-4 h-4 text-gray-700" />
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className="p-2 bg-blue-500 rounded-full shadow-lg hover:bg-blue-600"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleTemplateSelect(template.id);
                        }}
                      >
                        <Download className="w-4 h-4 text-white" />
                      </motion.button>
                    </div>
                  </div>
                </div>

                {/* Template Info */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-gray-900 truncate flex-1">
                      {template.name}
                    </h3>
                    <div className="flex items-center gap-1 ml-2">
                      <Star className="w-3 h-3 text-yellow-400 fill-current" />
                      <span className="text-xs text-gray-600">4.8</span>
                    </div>
                  </div>
                  
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {template.description}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`
                        text-xs px-2 py-1 rounded-full font-medium
                        ${template.category === 'landing' ? 'bg-blue-100 text-blue-700' :
                          template.category === 'ecommerce' ? 'bg-green-100 text-green-700' :
                          template.category === 'blog' ? 'bg-purple-100 text-purple-700' :
                          template.category === 'portfolio' ? 'bg-pink-100 text-pink-700' :
                          template.category === 'corporate' ? 'bg-gray-100 text-gray-700' :
                          'bg-orange-100 text-orange-700'
                        }
                      `}>
                        {template.category}
                      </span>
                      <span className="text-xs text-gray-500">
                        {template.elements.length} components
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-1 text-xs text-gray-500">
                      <Clock className="w-3 h-3" />
                      {template.updatedAt.toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
              <Filter className="w-6 h-6 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-600 mb-2">
              No templates found
            </h3>
            <p className="text-gray-500 max-w-sm mx-auto">
              {searchTerm 
                ? `No templates match "${searchTerm}". Try a different search term.`
                : 'No templates available in this category.'
              }
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      {filteredTemplates.length > 0 && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-2">
              {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} found
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="text-sm text-blue-600 hover:text-blue-700 font-medium"
            >
              Browse All Templates
            </motion.button>
          </div>
        </div>
      )}
    </div>
  );
}