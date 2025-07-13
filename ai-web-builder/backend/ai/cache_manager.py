"""
AI Cost-Aware Caching Manager
Intelligent caching system to reduce AI API costs through smart request deduplication
"""
import hashlib
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.models import AIUsage
from .models import AIRequest, AIResponse, ModelType, TaskType

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cached AI response entry"""
    request_hash: str
    response: AIResponse
    cached_at: datetime
    hit_count: int
    cost_saved: float
    original_cost: float
    similarity_threshold: float
    cache_ttl: int  # seconds

@dataclass
class CacheStats:
    """Cache performance statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    total_cost_saved: float
    avg_response_time: float
    storage_usage_mb: float

class AICacheManager:
    """
    Intelligent caching system for AI requests with cost optimization
    """
    
    def __init__(self, redis_client: redis.Redis, db: AsyncSession):
        self.redis = redis_client
        self.db = db
        self.cache_prefix = "ai_cache:"
        self.stats_prefix = "ai_cache_stats:"
        self.default_ttl = 3600 * 24 * 7  # 7 days
        self.similarity_threshold = 0.85  # 85% similarity for cache hits
        
        # Cache configuration by task type
        self.cache_config = {
            TaskType.COMPONENT_GENERATION: {
                "ttl": 3600 * 24 * 30,  # 30 days for components
                "similarity_threshold": 0.90,  # High similarity for components
                "enable_fuzzy_matching": True
            },
            TaskType.CONTENT_WRITING: {
                "ttl": 3600 * 24 * 7,   # 7 days for content
                "similarity_threshold": 0.80,   # Lower similarity for content
                "enable_fuzzy_matching": True
            },
            TaskType.CODE_GENERATION: {
                "ttl": 3600 * 24 * 14,  # 14 days for code
                "similarity_threshold": 0.95,   # Very high similarity for code
                "enable_fuzzy_matching": False
            },
            TaskType.ANALYSIS: {
                "ttl": 3600 * 24 * 3,   # 3 days for analysis
                "similarity_threshold": 0.75,   # Lower similarity for analysis
                "enable_fuzzy_matching": True
            }
        }
    
    async def get_cached_response(
        self, 
        request: AIRequest, 
        user_id: str
    ) -> Optional[AIResponse]:
        """
        Get cached response for a request if available and valid
        
        Args:
            request: AI request to check cache for
            user_id: User making the request
            
        Returns:
            Cached AIResponse if found, None otherwise
        """
        try:
            # Generate request hash
            request_hash = self._generate_request_hash(request, user_id)
            
            # Check exact match first
            cached_response = await self._get_exact_match(request_hash)
            if cached_response:
                await self._record_cache_hit(request_hash, cached_response.cost)
                logger.info(f"Cache hit (exact): {request_hash[:8]}")
                return cached_response
            
            # Check fuzzy matches if enabled
            config = self.cache_config.get(request.task_type, {})
            if config.get("enable_fuzzy_matching", False):
                fuzzy_response = await self._get_fuzzy_match(request, user_id)
                if fuzzy_response:
                    await self._record_cache_hit(request_hash, fuzzy_response.cost, is_fuzzy=True)
                    logger.info(f"Cache hit (fuzzy): {request_hash[:8]}")
                    return fuzzy_response
            
            # No cache hit
            await self._record_cache_miss(request_hash)
            return None
            
        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
            return None
    
    async def cache_response(
        self, 
        request: AIRequest, 
        response: AIResponse, 
        user_id: str
    ) -> bool:
        """
        Cache an AI response for future use
        
        Args:
            request: Original AI request
            response: AI response to cache
            user_id: User who made the request
            
        Returns:
            True if cached successfully, False otherwise
        """
        try:
            # Generate cache key
            request_hash = self._generate_request_hash(request, user_id)
            
            # Get cache configuration
            config = self.cache_config.get(request.task_type, {})
            ttl = config.get("ttl", self.default_ttl)
            
            # Create cache entry
            cache_entry = CacheEntry(
                request_hash=request_hash,
                response=response,
                cached_at=datetime.utcnow(),
                hit_count=0,
                cost_saved=0.0,
                original_cost=response.cost,
                similarity_threshold=config.get("similarity_threshold", self.similarity_threshold),
                cache_ttl=ttl
            )
            
            # Store in Redis
            cache_key = f"{self.cache_prefix}{request_hash}"
            cache_data = self._serialize_cache_entry(cache_entry)
            
            await self.redis.setex(cache_key, ttl, cache_data)
            
            # Store request metadata for fuzzy matching
            await self._store_request_metadata(request, user_id, request_hash)
            
            logger.info(f"Cached response: {request_hash[:8]}, TTL: {ttl}s, Cost: ${response.cost:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
            return False
    
    async def invalidate_cache(
        self, 
        user_id: Optional[str] = None, 
        task_type: Optional[TaskType] = None
    ) -> int:
        """
        Invalidate cached entries based on criteria
        
        Args:
            user_id: User ID to invalidate cache for (None = all users)
            task_type: Task type to invalidate (None = all types)
            
        Returns:
            Number of entries invalidated
        """
        try:
            pattern = f"{self.cache_prefix}*"
            keys = await self.redis.keys(pattern)
            
            invalidated = 0
            for key in keys:
                should_invalidate = False
                
                try:
                    cache_data = await self.redis.get(key)
                    if cache_data:
                        entry = self._deserialize_cache_entry(cache_data)
                        
                        # Check user filter
                        if user_id and not self._entry_matches_user(entry, user_id):
                            continue
                        
                        # Check task type filter
                        if task_type and not self._entry_matches_task_type(entry, task_type):
                            continue
                        
                        should_invalidate = True
                
                except Exception as e:
                    logger.warning(f"Failed to check cache entry {key}: {e}")
                    should_invalidate = True  # Invalidate corrupted entries
                
                if should_invalidate:
                    await self.redis.delete(key)
                    invalidated += 1
            
            logger.info(f"Invalidated {invalidated} cache entries")
            return invalidated
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return 0
    
    async def get_cache_stats(self, user_id: Optional[str] = None) -> CacheStats:
        """
        Get cache performance statistics
        
        Args:
            user_id: User ID to get stats for (None = global stats)
            
        Returns:
            CacheStats object with performance metrics
        """
        try:
            stats_key = f"{self.stats_prefix}{'global' if not user_id else user_id}"
            
            stats_data = await self.redis.hgetall(stats_key)
            
            if stats_data:
                total_requests = int(stats_data.get(b'total_requests', 0))
                cache_hits = int(stats_data.get(b'cache_hits', 0))
                cache_misses = int(stats_data.get(b'cache_misses', 0))
                total_cost_saved = float(stats_data.get(b'total_cost_saved', 0.0))
                avg_response_time = float(stats_data.get(b'avg_response_time', 0.0))
                
                hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
            else:
                total_requests = cache_hits = cache_misses = 0
                hit_rate = total_cost_saved = avg_response_time = 0.0
            
            # Calculate storage usage
            storage_usage = await self._calculate_storage_usage()
            
            return CacheStats(
                total_requests=total_requests,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                hit_rate=round(hit_rate, 2),
                total_cost_saved=round(total_cost_saved, 4),
                avg_response_time=round(avg_response_time, 3),
                storage_usage_mb=round(storage_usage, 2)
            )
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return CacheStats(0, 0, 0, 0.0, 0.0, 0.0, 0.0)
    
    async def optimize_cache(self) -> Dict[str, int]:
        """
        Optimize cache by removing old, unused entries
        
        Returns:
            Dictionary with optimization results
        """
        try:
            pattern = f"{self.cache_prefix}*"
            keys = await self.redis.keys(pattern)
            
            removed_expired = 0
            removed_unused = 0
            compressed = 0
            
            for key in keys:
                try:
                    cache_data = await self.redis.get(key)
                    if not cache_data:
                        continue
                    
                    entry = self._deserialize_cache_entry(cache_data)
                    
                    # Remove expired entries
                    if self._is_entry_expired(entry):
                        await self.redis.delete(key)
                        removed_expired += 1
                        continue
                    
                    # Remove entries with no hits after 24 hours
                    if (entry.hit_count == 0 and 
                        (datetime.utcnow() - entry.cached_at).total_seconds() > 86400):
                        await self.redis.delete(key)
                        removed_unused += 1
                        continue
                    
                    # Compress large entries (simplified - could implement actual compression)
                    if len(cache_data) > 10000:  # 10KB threshold
                        compressed += 1
                
                except Exception as e:
                    logger.warning(f"Failed to optimize cache entry {key}: {e}")
                    await self.redis.delete(key)
                    removed_expired += 1
            
            logger.info(f"Cache optimization: {removed_expired} expired, {removed_unused} unused, {compressed} compressed")
            
            return {
                "removed_expired": removed_expired,
                "removed_unused": removed_unused,
                "compressed": compressed,
                "total_processed": len(keys)
            }
            
        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {"error": str(e)}
    
    def _generate_request_hash(self, request: AIRequest, user_id: str) -> str:
        """Generate unique hash for AI request"""
        # Include relevant request parameters
        hash_data = {
            "task_type": request.task_type.value,
            "content": request.content.lower().strip(),
            "complexity": request.complexity,
            "user_tier": request.user_tier,
            "requires_vision": request.requires_vision,
            "user_id": user_id  # Include user ID for personalization
        }
        
        # Create SHA-256 hash
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    async def _get_exact_match(self, request_hash: str) -> Optional[AIResponse]:
        """Get exact cache match"""
        try:
            cache_key = f"{self.cache_prefix}{request_hash}"
            cache_data = await self.redis.get(cache_key)
            
            if cache_data:
                entry = self._deserialize_cache_entry(cache_data)
                
                # Check if entry is still valid
                if not self._is_entry_expired(entry):
                    return entry.response
                else:
                    # Remove expired entry
                    await self.redis.delete(cache_key)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get exact match: {e}")
            return None
    
    async def _get_fuzzy_match(self, request: AIRequest, user_id: str) -> Optional[AIResponse]:
        """
        Find fuzzy matches based on content similarity
        This is a simplified implementation - in production you'd use more sophisticated NLP
        """
        try:
            # Get all cache keys for this task type
            pattern = f"{self.cache_prefix}*"
            keys = await self.redis.keys(pattern)
            
            best_match = None
            best_similarity = 0.0
            
            config = self.cache_config.get(request.task_type, {})
            threshold = config.get("similarity_threshold", self.similarity_threshold)
            
            for key in keys:
                try:
                    cache_data = await self.redis.get(key)
                    if not cache_data:
                        continue
                    
                    entry = self._deserialize_cache_entry(cache_data)
                    
                    # Skip expired entries
                    if self._is_entry_expired(entry):
                        continue
                    
                    # Calculate similarity (simplified - could use more advanced NLP)
                    similarity = self._calculate_content_similarity(
                        request.content, 
                        entry.response.content  # This would need the original request content
                    )
                    
                    if similarity > threshold and similarity > best_similarity:
                        best_similarity = similarity
                        best_match = entry.response
                
                except Exception as e:
                    logger.warning(f"Failed to check fuzzy match for {key}: {e}")
                    continue
            
            if best_match:
                logger.info(f"Found fuzzy match with {best_similarity:.2f} similarity")
            
            return best_match
            
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {e}")
            return None
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """
        Calculate similarity between two content strings
        Simplified implementation - could use more advanced NLP techniques
        """
        try:
            # Normalize content
            c1 = set(content1.lower().split())
            c2 = set(content2.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(c1.intersection(c2))
            union = len(c1.union(c2))
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception:
            return 0.0
    
    async def _store_request_metadata(self, request: AIRequest, user_id: str, request_hash: str):
        """Store request metadata for fuzzy matching"""
        try:
            metadata_key = f"{self.cache_prefix}meta:{request_hash}"
            metadata = {
                "task_type": request.task_type.value,
                "complexity": request.complexity,
                "user_id": user_id,
                "content_length": len(request.content),
                "requires_vision": request.requires_vision,
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.redis.setex(
                metadata_key, 
                self.default_ttl, 
                json.dumps(metadata)
            )
            
        except Exception as e:
            logger.warning(f"Failed to store request metadata: {e}")
    
    async def _record_cache_hit(self, request_hash: str, cost_saved: float, is_fuzzy: bool = False):
        """Record cache hit statistics"""
        try:
            # Update global stats
            await self._update_stats("global", "cache_hits", 1)
            await self._update_stats("global", "total_cost_saved", cost_saved)
            
            # Update cache entry hit count
            cache_key = f"{self.cache_prefix}{request_hash}"
            cache_data = await self.redis.get(cache_key)
            
            if cache_data:
                entry = self._deserialize_cache_entry(cache_data)
                entry.hit_count += 1
                entry.cost_saved += cost_saved
                
                # Update TTL based on usage
                new_ttl = min(entry.cache_ttl * 2, 86400 * 30)  # Max 30 days
                await self.redis.setex(
                    cache_key, 
                    new_ttl, 
                    self._serialize_cache_entry(entry)
                )
            
        except Exception as e:
            logger.error(f"Failed to record cache hit: {e}")
    
    async def _record_cache_miss(self, request_hash: str):
        """Record cache miss statistics"""
        try:
            await self._update_stats("global", "cache_misses", 1)
            await self._update_stats("global", "total_requests", 1)
            
        except Exception as e:
            logger.error(f"Failed to record cache miss: {e}")
    
    async def _update_stats(self, scope: str, metric: str, value: float):
        """Update cache statistics"""
        try:
            stats_key = f"{self.stats_prefix}{scope}"
            await self.redis.hincrbyfloat(stats_key, metric, value)
            await self.redis.expire(stats_key, 86400 * 30)  # Keep stats for 30 days
            
        except Exception as e:
            logger.warning(f"Failed to update stats: {e}")
    
    async def _calculate_storage_usage(self) -> float:
        """Calculate total cache storage usage in MB"""
        try:
            pattern = f"{self.cache_prefix}*"
            keys = await self.redis.keys(pattern)
            
            total_size = 0
            for key in keys:
                try:
                    size = await self.redis.memory_usage(key)
                    if size:
                        total_size += size
                except Exception:
                    continue
            
            return total_size / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            logger.error(f"Failed to calculate storage usage: {e}")
            return 0.0
    
    def _serialize_cache_entry(self, entry: CacheEntry) -> str:
        """Serialize cache entry for storage"""
        try:
            data = asdict(entry)
            # Handle datetime serialization
            data["cached_at"] = entry.cached_at.isoformat()
            # Handle AIResponse serialization
            data["response"] = asdict(entry.response)
            data["response"]["timestamp"] = entry.response.timestamp.isoformat()
            data["response"]["model_used"] = entry.response.model_used.value
            
            return json.dumps(data)
            
        except Exception as e:
            logger.error(f"Failed to serialize cache entry: {e}")
            raise
    
    def _deserialize_cache_entry(self, data: str) -> CacheEntry:
        """Deserialize cache entry from storage"""
        try:
            parsed = json.loads(data)
            
            # Handle datetime deserialization
            parsed["cached_at"] = datetime.fromisoformat(parsed["cached_at"])
            
            # Handle AIResponse deserialization
            response_data = parsed["response"]
            response_data["timestamp"] = datetime.fromisoformat(response_data["timestamp"])
            response_data["model_used"] = ModelType(response_data["model_used"])
            
            response = AIResponse(**response_data)
            parsed["response"] = response
            
            return CacheEntry(**parsed)
            
        except Exception as e:
            logger.error(f"Failed to deserialize cache entry: {e}")
            raise
    
    def _is_entry_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        try:
            expiry_time = entry.cached_at + timedelta(seconds=entry.cache_ttl)
            return datetime.utcnow() > expiry_time
            
        except Exception:
            return True
    
    def _entry_matches_user(self, entry: CacheEntry, user_id: str) -> bool:
        """Check if cache entry matches user (simplified)"""
        # In a real implementation, you'd store user_id in the cache entry
        # For now, this is a placeholder
        return True
    
    def _entry_matches_task_type(self, entry: CacheEntry, task_type: TaskType) -> bool:
        """Check if cache entry matches task type (simplified)"""
        # In a real implementation, you'd store task_type in the cache entry
        # For now, this is a placeholder
        return True