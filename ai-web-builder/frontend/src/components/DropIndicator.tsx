'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useBuilderStore } from '@/stores/builderStore';

export function DropIndicator() {
  const { draggedElementType, isDropTarget } = useBuilderStore();

  return (
    <AnimatePresence>
      {draggedElementType && isDropTarget && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 pointer-events-none z-40"
        >
          {/* Drop zone overlay */}
          <div className="absolute inset-0 bg-blue-50 bg-opacity-50 border-2 border-dashed border-blue-300 rounded-lg">
            <div className="absolute inset-0 flex items-center justify-center">
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg font-medium"
              >
                Drop {draggedElementType} here
              </motion.div>
            </div>
          </div>

          {/* Animated particles */}
          <div className="absolute inset-0">
            {[...Array(6)].map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-blue-400 rounded-full"
                initial={{
                  x: Math.random() * 100 + '%',
                  y: Math.random() * 100 + '%',
                  scale: 0,
                }}
                animate={{
                  scale: [0, 1, 0],
                  opacity: [0, 1, 0],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  delay: i * 0.2,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}