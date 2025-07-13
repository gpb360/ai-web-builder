'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Database, 
  TrendingUp, 
  DollarSign, 
  Zap, 
  HardDrive, 
  Clock,
  RefreshCw,
  Trash2,
  BarChart3,
  CheckCircle,
  AlertTriangle
} from 'lucide-react';

interface CacheStats {
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  hit_rate_percent: number;
  total_cost_saved: number;
  avg_response_time_ms: number;
  storage_usage_mb: number;
}

interface CacheEfficiencyReport {
  cache_performance: {
    hit_rate_percent: number;
    cost_efficiency_percent: number;
    total_cost_saved: number;
    estimated_without_cache: number;
  };
  usage_comparison: {
    actual_cost: number;
    requests_served_from_cache: number;
    requests_requiring_ai: number;
    cache_to_ai_ratio: number;
  };
  recommendations: string[];
}

interface CacheEfficiencyDashboardProps {
  className?: string;
}

export function CacheEfficiencyDashboard({ className = '' }: CacheEfficiencyDashboardProps) {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [report, setReport] = useState<CacheEfficiencyReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCacheData();
  }, []);

  const loadCacheData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load cache stats and efficiency report in parallel
      const [statsResponse, reportResponse] = await Promise.all([
        fetch('/api/ai/cache-stats', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
          }
        }),
        fetch('/api/ai/cache-efficiency-report?days=30', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
          }
        })
      ]);

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        if (statsData.cache_statistics?.stats) {
          setStats(statsData.cache_statistics.stats);
        }
      }

      if (reportResponse.ok) {
        const reportData = await reportResponse.json();
        if (reportData.report) {
          setReport(reportData.report);
        }
      }

      setLastUpdated(new Date());

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load cache data';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeCache = async () => {
    setIsOptimizing(true);
    
    try {
      const response = await fetch('/api/ai/optimize-cache', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });

      if (response.ok) {
        // Reload data after optimization
        await loadCacheData();
      } else {
        throw new Error('Cache optimization failed');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Cache optimization failed';
      setError(errorMessage);
    } finally {
      setIsOptimizing(false);
    }
  };

  const clearCache = async () => {
    if (!confirm('Are you sure you want to clear all cached data? This cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch('/api/ai/cache', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token') || ''}`
        }
      });

      if (response.ok) {
        // Reload data after clearing
        await loadCacheData();
      } else {
        throw new Error('Cache clearing failed');
      }

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Cache clearing failed';
      setError(errorMessage);
    }
  };

  const getHitRateColor = (hitRate: number) => {
    if (hitRate >= 80) return 'text-green-600';
    if (hitRate >= 60) return 'text-blue-600';
    if (hitRate >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getHitRateBackground = (hitRate: number) => {
    if (hitRate >= 80) return 'bg-green-100';
    if (hitRate >= 60) return 'bg-blue-100';
    if (hitRate >= 40) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  if (error) {
    return (
      <div className={`bg-white rounded-xl border border-gray-200 p-6 shadow-sm ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <Database className="w-5 h-5 text-red-500" />
          <h4 className="font-semibold text-gray-800">Cache Performance</h4>
        </div>
        <div className="text-center py-8">
          <AlertTriangle className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={loadCacheData}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
            <Database className="w-4 h-4 text-blue-600" />
          </div>
          <h4 className="font-semibold text-gray-800">Cache Performance Dashboard</h4>
        </div>
        
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={loadCacheData}
            disabled={isLoading}
            className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-600 rounded-lg transition-all disabled:opacity-50"
            title="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={optimizeCache}
            disabled={isOptimizing}
            className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 transition-all flex items-center gap-2"
          >
            {isOptimizing ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Optimizing...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4" />
                Optimize
              </>
            )}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={clearCache}
            className="p-2 bg-red-100 hover:bg-red-200 text-red-600 rounded-lg transition-all"
            title="Clear cache"
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {lastUpdated && (
        <p className="text-sm text-gray-500">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Hit Rate */}
          <div className={`p-4 rounded-xl ${getHitRateBackground(stats.hit_rate_percent)}`}>
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Hit Rate</span>
            </div>
            <div className={`text-2xl font-bold ${getHitRateColor(stats.hit_rate_percent)}`}>
              {stats.hit_rate_percent.toFixed(1)}%
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {stats.cache_hits} hits / {stats.total_requests} requests
            </p>
          </div>

          {/* Cost Saved */}
          <div className="p-4 bg-green-100 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Cost Saved</span>
            </div>
            <div className="text-2xl font-bold text-green-600">
              ${stats.total_cost_saved.toFixed(4)}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Total savings
            </p>
          </div>

          {/* Response Time */}
          <div className="p-4 bg-purple-100 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Avg Response</span>
            </div>
            <div className="text-2xl font-bold text-purple-600">
              {stats.avg_response_time_ms.toFixed(0)}ms
            </div>
            <p className="text-xs text-gray-600 mt-1">
              From cache
            </p>
          </div>

          {/* Storage Usage */}
          <div className="p-4 bg-orange-100 rounded-xl">
            <div className="flex items-center gap-2 mb-2">
              <HardDrive className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-700">Storage</span>
            </div>
            <div className="text-2xl font-bold text-orange-600">
              {stats.storage_usage_mb.toFixed(1)}MB
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Cache size
            </p>
          </div>
        </div>
      )}

      {report && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Analysis */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              <h5 className="font-semibold text-gray-800">Performance Analysis</h5>
            </div>
            
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cost Efficiency:</span>
                <span className="font-semibold text-green-600">
                  {report.cache_performance.cost_efficiency_percent.toFixed(1)}%
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Without Cache:</span>
                <span className="font-semibold text-gray-800">
                  ${report.cache_performance.estimated_without_cache.toFixed(4)}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Actual Cost:</span>
                <span className="font-semibold text-gray-800">
                  ${report.usage_comparison.actual_cost.toFixed(4)}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Cache vs AI Ratio:</span>
                <span className="font-semibold text-blue-600">
                  {report.usage_comparison.cache_to_ai_ratio.toFixed(1)}:1
                </span>
              </div>
            </div>
          </div>

          {/* Recommendations */}
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <h5 className="font-semibold text-gray-800">Recommendations</h5>
            </div>
            
            <div className="space-y-3">
              {report.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                  <p className="text-sm text-gray-600">{recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {isLoading && !stats && (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading cache performance data...</p>
        </div>
      )}

      {!isLoading && !stats && !error && (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 mb-4">No cache data available</p>
          <p className="text-sm text-gray-500">
            Generate some components to see cache performance metrics
          </p>
        </div>
      )}
    </div>
  );
}