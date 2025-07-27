'use client';

// Frontend development kickoff - drag-drop builder ready for production
import Link from 'next/link';
import { ComponentGenerator } from '@/components/ComponentGenerator';
import { motion } from 'framer-motion';
import { Wand2, Layout, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-12"
        >
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI Web Builder Platform
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            Build production-ready websites with AI precision. Use our drag-drop builder or generate components with natural language.
          </p>
          
          <div className="flex gap-4 justify-center">
            <Link href="/builder">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="bg-blue-500 text-white px-8 py-4 rounded-xl font-semibold text-lg shadow-lg hover:bg-blue-600 transition-colors flex items-center gap-3"
              >
                <Layout className="w-6 h-6" />
                Open Builder
              </motion.button>
            </Link>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="bg-white text-blue-500 border-2 border-blue-500 px-8 py-4 rounded-xl font-semibold text-lg shadow-lg hover:bg-blue-50 transition-colors flex items-center gap-3"
              onClick={() => document.getElementById('generator')?.scrollIntoView({ behavior: 'smooth' })}
            >
              <Wand2 className="w-6 h-6" />
              AI Generator
            </motion.button>
          </div>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid md:grid-cols-3 gap-8 mb-16"
        >
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <Layout className="w-12 h-12 text-blue-500 mb-4 mx-auto" />
            <h3 className="text-xl font-semibold mb-2">Drag & Drop Builder</h3>
            <p className="text-gray-600">Visual canvas with drag-drop components, real-time preview, and responsive design.</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <Wand2 className="w-12 h-12 text-purple-500 mb-4 mx-auto" />
            <h3 className="text-xl font-semibold mb-2">AI Component Generator</h3>
            <p className="text-gray-600">Describe components in plain English and get production-ready code instantly.</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <Zap className="w-12 h-12 text-green-500 mb-4 mx-auto" />
            <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
            <p className="text-gray-600">Optimized performance with <3s load times and instant interactions.</p>
          </div>
        </motion.div>
      </div>

      {/* AI Generator Section */}
      <div id="generator">
        <ComponentGenerator />
      </div>
    </div>
  );
}
// Frontend development started
