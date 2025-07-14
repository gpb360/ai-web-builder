'use client';

import React, { useState } from 'react';
import { Code2, Menu, X } from 'lucide-react';

interface NavigationProps {
  className?: string;
}

export function Navigation({ className = '' }: NavigationProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-md border-b border-border-subtle ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <Code2 className="w-6 h-6 text-accent-primary" />
            <span className="text-lg font-semibold text-foreground font-mono">
              AI Web Builder
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <a href="/features" className="text-foreground-muted hover:text-foreground transition-colors">
              Features
            </a>
            <a href="/docs" className="text-foreground-muted hover:text-foreground transition-colors">
              Documentation
            </a>
            <a href="/pricing" className="text-foreground-muted hover:text-foreground transition-colors">
              Pricing
            </a>
          </div>

          {/* Right side actions */}
          <div className="hidden md:flex items-center space-x-4">
            <a href="/signin" className="text-foreground-muted hover:text-foreground transition-colors">
              Sign in
            </a>
            <button className="btn btn-primary">
              Get Started
            </button>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-foreground-muted hover:text-foreground transition-colors"
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
      {isMobileMenuOpen && (
        <div className="md:hidden bg-background-secondary border-t border-border-subtle">
          <div className="px-4 py-6 space-y-4">
            <a href="/features" className="block py-2 text-foreground-muted hover:text-foreground transition-colors">
              Features
            </a>
            <a href="/docs" className="block py-2 text-foreground-muted hover:text-foreground transition-colors">
              Documentation
            </a>
            <a href="/pricing" className="block py-2 text-foreground-muted hover:text-foreground transition-colors">
              Pricing
            </a>
            <div className="pt-4 border-t border-border-subtle">
              <button className="btn btn-primary w-full">
                Get Started
              </button>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}