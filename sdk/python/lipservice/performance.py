"""
Memory-optimized signature cache and batch processing for LipService.

This module provides:
- LRU cache for signature computation
- Memory pooling for batch operations
- Efficient string operations
- Memory usage monitoring
"""

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Tuple
from weakref import WeakValueDictionary

import structlog

logger = structlog.get_logger(__name__)


class LRUSignatureCache:
    """
    Thread-safe LRU cache for log signatures.
    
    Features:
    - Fixed memory usage with LRU eviction
    - Thread-safe operations
    - Memory usage monitoring
    - Hit rate statistics
    """
    
    def __init__(self, max_size: int = 10000, max_memory_mb: int = 50):
        """
        Initialize LRU signature cache.
        
        Args:
            max_size: Maximum number of signatures to cache
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._memory_usage = 0
        
    def get(self, message: str) -> Optional[str]:
        """Get signature from cache."""
        with self._lock:
            if message in self._cache:
                # Move to end (most recently used)
                signature = self._cache.pop(message)
                self._cache[message] = signature
                self._hits += 1
                return signature
            
            self._misses += 1
            return None
    
    def put(self, message: str, signature: str) -> None:
        """Put signature in cache."""
        with self._lock:
            # Remove if already exists
            if message in self._cache:
                self._cache.pop(message)
            
            # Add new entry
            self._cache[message] = signature
            
            # Update memory usage estimate
            self._memory_usage += len(message.encode('utf-8')) + len(signature.encode('utf-8'))
            
            # Evict if necessary
            self._evict_if_needed()
    
    def _evict_if_needed(self) -> None:
        """Evict entries if cache is too large."""
        while (len(self._cache) > self.max_size or 
               self._memory_usage > self.max_memory_bytes):
            if not self._cache:
                break
                
            # Remove least recently used
            message, signature = self._cache.popitem(last=False)
            self._memory_usage -= len(message.encode('utf-8')) + len(signature.encode('utf-8'))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'memory_usage_mb': self._memory_usage / (1024 * 1024),
                'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
            }
    
    def clear(self) -> None:
        """Clear cache."""
        with self._lock:
            self._cache.clear()
            self._memory_usage = 0
            self._hits = 0
            self._misses = 0


class MemoryPool:
    """
    Memory pool for efficient batch operations.
    
    Reuses memory blocks to reduce allocation overhead.
    """
    
    def __init__(self, block_size: int = 1024, max_blocks: int = 100):
        """
        Initialize memory pool.
        
        Args:
            block_size: Size of each memory block
            max_blocks: Maximum number of blocks to keep
        """
        self.block_size = block_size
        self.max_blocks = max_blocks
        self._available_blocks = []
        self._lock = threading.Lock()
        self._total_allocated = 0
    
    def get_block(self) -> bytearray:
        """Get a memory block from the pool."""
        with self._lock:
            if self._available_blocks:
                return self._available_blocks.pop()
            
            # Allocate new block
            self._total_allocated += 1
            return bytearray(self.block_size)
    
    def return_block(self, block: bytearray) -> None:
        """Return a memory block to the pool."""
        with self._lock:
            if len(self._available_blocks) < self.max_blocks:
                # Clear the block
                block[:] = b'\x00' * len(block)
                self._available_blocks.append(block)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self._lock:
            return {
                'available_blocks': len(self._available_blocks),
                'total_allocated': self._total_allocated,
                'block_size': self.block_size,
                'max_blocks': self.max_blocks,
            }


class OptimizedSignatureComputer:
    """
    Optimized signature computation with caching and memory efficiency.
    """
    
    def __init__(self, cache_size: int = 10000):
        """Initialize optimized signature computer."""
        self.cache = LRUSignatureCache(max_size=cache_size)
        self._compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, Any]:
        """Pre-compile regex patterns for better performance."""
        import re
        
        return {
            'numbers': re.compile(r'\b\d+\b'),
            'uuids': re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE),
            'timestamps': re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}'),
            'ips': re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'urls': re.compile(r'https?://[^\s]+'),
        }
    
    def compute_signature(self, message: str) -> str:
        """
        Compute signature with caching and optimization.
        
        Args:
            message: Log message to compute signature for
            
        Returns:
            Hexadecimal signature string
        """
        # Check cache first
        cached_signature = self.cache.get(message)
        if cached_signature:
            return cached_signature
        
        # Compute signature
        signature = self._compute_signature_optimized(message)
        
        # Cache result
        self.cache.put(message, signature)
        
        return signature
    
    def _compute_signature_optimized(self, message: str) -> str:
        """Optimized signature computation."""
        import re
        import hashlib
        
        # Normalize the message (same as original function)
        normalized = message

        # Replace UUIDs first (before numbers)
        normalized = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "UUID", normalized, flags=re.IGNORECASE)

        # Replace hex IDs
        normalized = re.sub(r"\b[a-f0-9]{32,}\b", "HEXID", normalized, flags=re.IGNORECASE)

        # Replace ISO timestamps
        normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "TIMESTAMP", normalized)

        # Replace dates
        normalized = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "DATE", normalized)

        # Replace times
        normalized = re.sub(r"\b\d{2}:\d{2}:\d{2}\b", "TIME", normalized)

        # Replace IP addresses
        normalized = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "IP", normalized)

        # Replace email addresses
        normalized = re.sub(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "EMAIL", normalized)

        # Replace URLs
        normalized = re.sub(r"https?://[^\s]+", "URL", normalized)

        # Replace numbers with placeholder (after other patterns)
        normalized = re.sub(r"\b\d+\b", "N", normalized)

        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized)

        # Trim
        normalized = normalized.strip()

        # Generate MD5 hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get signature computation statistics."""
        return {
            'cache_stats': self.cache.get_stats(),
            'compiled_patterns': len(self._compiled_patterns),
        }


# Global instances for reuse
_signature_cache = LRUSignatureCache()
_memory_pool = MemoryPool()
_signature_computer = OptimizedSignatureComputer()


def get_signature_cache() -> LRUSignatureCache:
    """Get global signature cache instance."""
    return _signature_cache


def get_memory_pool() -> MemoryPool:
    """Get global memory pool instance."""
    return _memory_pool


def get_signature_computer() -> OptimizedSignatureComputer:
    """Get global signature computer instance."""
    return _signature_computer
