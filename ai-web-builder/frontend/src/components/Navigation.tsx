'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Code2, 
  Sparkles, 
  Menu, 
  X, 
  ChevronDown,
  Zap,
  Shield,
  BarChart3,
  ArrowRight,
  User,
  Settings,
  LogOut
} from 'lucide-react';

interface NavigationProps {
  className?: string;
}

export function Navigation({ className = '' }: NavigationProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProductsOpen, setIsProductsOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const products = [
    {
      name: 'Component Generator',
      description: 'AI-powered React, Vue, and HTML component generation',
      icon: Code2,
      href: '/generate',
      color: 'text-blue-400'
    },
    {
      name: 'Quality Validator',
      description: '6-category validation for production-ready code',
      icon: Shield,
      href: '/validate',
      color: 'text-green-400'
    },
    {
      name: 'Analytics Dashboard',
      description: 'Real-time cost tracking and performance metrics',
      icon: BarChart3,
      href: '/analytics',
      color: 'text-purple-400'
    }
  ];

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled 
        ? 'glass-morphism border-b border-white/10' 
        : 'bg-transparent'
    } ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <motion.div 
            className="flex items-center space-x-2"
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            <div className="w-8 h-8 gradient-bg rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold font-mono gradient-text">
              AI Web Builder
            </span>
          </motion.div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {/* Products Dropdown */}
            <div className="relative">
              <button
                className="flex items-center space-x-1 text-gray-300 hover:text-white transition-colors"
                onMouseEnter={() => setIsProductsOpen(true)}
                onMouseLeave={() => setIsProductsOpen(false)}
              >
                <span className="font-medium">Products</span>
                <ChevronDown className={`w-4 h-4 transition-transform ${
                  isProductsOpen ? 'rotate-180' : ''
                }`} />
              </button>

              <AnimatePresence>
                {isProductsOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.2 }}
                    className="absolute top-full left-0 mt-2 w-80 glass-morphism rounded-xl p-4 border border-white/10"
                    onMouseEnter={() => setIsProductsOpen(true)}
                    onMouseLeave={() => setIsProductsOpen(false)}
                  >
                    <div className="space-y-3">
                      {products.map((product) => (
                        <a
                          key={product.name}
                          href={product.href}
                          className="flex items-start space-x-3 p-3 rounded-lg hover:bg-white/5 transition-colors group"
                        >
                          <div className={`w-8 h-8 rounded-lg bg-gray-800/50 flex items-center justify-center ${product.color}`}>
                            <product.icon className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2">
                              <h4 className="text-sm font-medium text-white group-hover:text-gray-100">
                                {product.name}
                              </h4>
                              <ArrowRight className="w-3 h-3 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                            </div>
                            <p className="text-xs text-gray-400 mt-1">
                              {product.description}
                            </p>
                          </div>
                        </a>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <a href="/docs" className="text-gray-300 hover:text-white transition-colors font-medium">
              Documentation
            </a>
            <a href="/pricing" className="text-gray-300 hover:text-white transition-colors font-medium">
              Pricing
            </a>
            <a href="/blog" className="text-gray-300 hover:text-white transition-colors font-medium">
              Blog
            </a>
          </div>

          {/* Right side actions */}
          <div className="hidden md:flex items-center space-x-4">
            {/* User menu or auth buttons */}
            <div className="relative">
              <button
                className="flex items-center space-x-2 text-gray-300 hover:text-white transition-colors"
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              >
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <ChevronDown className={`w-4 h-4 transition-transform ${
                  isUserMenuOpen ? 'rotate-180' : ''
                }`} />
              </button>

              <AnimatePresence>
                {isUserMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    transition={{ duration: 0.2 }}
                    className="absolute top-full right-0 mt-2 w-48 glass-morphism rounded-xl p-2 border border-white/10"
                  >
                    <div className="space-y-1">
                      <a href="/dashboard" className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <BarChart3 className="w-4 h-4" />
                        <span>Dashboard</span>
                      </a>
                      <a href="/settings" className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <Settings className="w-4 h-4" />
                        <span>Settings</span>
                      </a>
                      <hr className="border-gray-700 my-2" />
                      <button className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 rounded-lg transition-colors w-full text-left">
                        <LogOut className="w-4 h-4" />
                        <span>Sign out</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <motion.button 
              className="btn btn-primary flex items-center space-x-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Zap className="w-4 h-4" />
              <span>Generate Now</span>
            </motion.button>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-gray-300 hover:text-white transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="md:hidden glass-morphism border-t border-white/10"
          >
            <div className="px-4 py-6 space-y-4">
              {/* Products section */}
              <div>
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Products
                </h3>
                <div className="space-y-2">
                  {products.map((product) => (
                    <a
                      key={product.name}
                      href={product.href}
                      className="flex items-center space-x-3 py-2 text-gray-300 hover:text-white transition-colors"
                    >
                      <product.icon className={`w-5 h-5 ${product.color}`} />
                      <span>{product.name}</span>
                    </a>
                  ))}
                </div>
              </div>

              {/* Navigation links */}
              <div className="space-y-2">
                <a href="/docs" className="block py-2 text-gray-300 hover:text-white transition-colors">
                  Documentation
                </a>
                <a href="/pricing" className="block py-2 text-gray-300 hover:text-white transition-colors">
                  Pricing
                </a>
                <a href="/blog" className="block py-2 text-gray-300 hover:text-white transition-colors">
                  Blog
                </a>
              </div>

              {/* CTA button */}
              <div className="pt-4 border-t border-gray-700">
                <button className="btn btn-primary w-full flex items-center justify-center space-x-2">
                  <Zap className="w-4 h-4" />
                  <span>Generate Now</span>
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}