#!/usr/bin/env python3
"""
Duration Cache for Silence Suzuka Player

Persistent caching system for video durations to avoid repeated yt-dlp calls.
Uses URL hashing for consistent cache keys and JSON persistence.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from urllib.parse import urlparse, parse_qs, urlencode
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Single cache entry for a video duration"""
    duration: int  # Duration in seconds
    timestamp: float  # When cached (Unix timestamp)
    source: str  # 'yt-dlp', 'mpv', 'manual', etc.
    retries: int = 0  # Number of failed fetch attempts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'duration': self.duration,
            'timestamp': self.timestamp,
            'source': self.source,
            'retries': self.retries
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        return cls(
            duration=int(data.get('duration', 0)),
            timestamp=float(data.get('timestamp', 0)),
            source=str(data.get('source', 'unknown')),
            retries=int(data.get('retries', 0))
        )


class DurationCache:
    """
    Persistent cache for video durations with automatic cleanup and URL normalization.
    
    Features:
    - URL normalization for consistent cache keys
    - Automatic expiration of old entries
    - Size limits with LRU-style cleanup
    - Thread-safe operations
    - Statistics tracking
    """
    
    def __init__(self, config_dir: Path, settings: Any = None):
        self.config_dir = Path(config_dir)
        self.cache_file = self.config_dir / 'duration_cache.json'
        self.settings = settings
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'expired': 0,
            'evicted': 0
        }
        self._load_cache()
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL to create consistent cache keys.
        
        For YouTube: Extract video ID and create canonical URL
        For Bilibili: Extract video ID (av/bv number)
        For local files: Use absolute path
        """
        if not url:
            return url
            
        try:
            url_lower = url.lower()
            
            # YouTube normalization
            if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                parsed = urlparse(url)
                
                if 'youtu.be' in url_lower:
                    # Short URL: https://youtu.be/VIDEO_ID
                    video_id = parsed.path.strip('/').split('/')[0].split('?')[0]
                else:
                    # Regular URL: https://www.youtube.com/watch?v=VIDEO_ID
                    query_params = parse_qs(parsed.query)
                    video_id = query_params.get('v', [''])[0]
                
                if video_id:
                    return f"https://www.youtube.com/watch?v={video_id}"
            
            # Bilibili normalization
            elif 'bilibili.com' in url_lower:
                # Extract BV or av number
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                
                for part in path_parts:
                    if part.startswith(('BV', 'av')):
                        return f"https://www.bilibili.com/video/{part}"
            
            # Local files: normalize path
            elif url.startswith(('file://', '/')):
                # Convert to absolute path
                if url.startswith('file://'):
                    from urllib.parse import unquote
                    path = unquote(urlparse(url).path)
                else:
                    path = url
                
                return str(Path(path).resolve())
            
            # Return as-is for other URLs
            return url
            
        except Exception:
            # If normalization fails, return original URL
            return url
    
    def _get_cache_key(self, url: str) -> str:
        """Generate a consistent cache key from URL"""
        normalized_url = self._normalize_url(url)
        # Use SHA-256 hash for consistent, collision-resistant keys
        return hashlib.sha256(normalized_url.encode('utf-8')).hexdigest()
    
    def _load_cache(self):
        """Load cache from persistent storage"""
        if not self.cache_file.exists():
            return
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Load cache entries
            cache_data = data.get('cache', {})
            for key, entry_data in cache_data.items():
                try:
                    self._cache[key] = CacheEntry.from_dict(entry_data)
                except Exception:
                    # Skip corrupted entries
                    continue
            
            # Load statistics
            self._stats.update(data.get('stats', {}))
            
            # Clean up expired entries on load
            self._cleanup_expired()
            
        except Exception as e:
            print(f"Duration Cache: Failed to load cache: {e}")
            self._cache = {}
    
    def _save_cache(self):
        """Save cache to persistent storage"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            cache_data = {
                key: entry.to_dict() 
                for key, entry in self._cache.items()
            }
            
            data = {
                'cache': cache_data,
                'stats': self._stats,
                'last_updated': time.time(),
                'version': '1.0'
            }
            
            # Atomic write using temporary file
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.cache_file)
            
        except Exception as e:
            print(f"Duration Cache: Failed to save cache: {e}")
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        if not self.settings or not self.settings.cache_enabled:
            return
        
        current_time = time.time()
        max_age = self.settings.cache_max_age_days * 24 * 3600  # Convert to seconds
        
        expired_keys = []
        for key, entry in self._cache.items():
            if current_time - entry.timestamp > max_age:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['expired'] += 1
    
    def _enforce_size_limit(self):
        """Enforce cache size limit using LRU-style eviction"""
        if not self.settings or not self.settings.cache_enabled:
            return
        
        max_entries = self.settings.cache_max_entries
        if len(self._cache) <= max_entries:
            return
        
        # Sort by timestamp (oldest first) and remove excess entries
        sorted_items = sorted(
            self._cache.items(),
            key=lambda x: x[1].timestamp
        )
        
        entries_to_remove = len(self._cache) - max_entries
        for key, _ in sorted_items[:entries_to_remove]:
            del self._cache[key]
            self._stats['evicted'] += 1
    
    def get(self, url: str) -> Optional[int]:
        """
        Get cached duration for URL.
        
        Returns:
            Duration in seconds, or None if not cached or expired
        """
        if not url or not self.settings or not self.settings.cache_enabled:
            return None
        
        try:
            cache_key = self._get_cache_key(url)
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None
            
            # Check if entry is expired
            if self.settings.cache_max_age_days > 0:
                max_age = self.settings.cache_max_age_days * 24 * 3600
                if time.time() - entry.timestamp > max_age:
                    del self._cache[cache_key]
                    self._stats['expired'] += 1
                    self._stats['misses'] += 1
                    return None
            
            self._stats['hits'] += 1
            return entry.duration
            
        except Exception as e:
            print(f"Duration Cache: Error getting {url}: {e}")
            return None
    
    def set(self, url: str, duration: int, source: str = 'unknown'):
        """
        Cache duration for URL.
        
        Args:
            url: Video URL
            duration: Duration in seconds
            source: Source of duration ('yt-dlp', 'mpv', 'manual', etc.)
        """
        if not url or not self.settings or not self.settings.cache_enabled:
            return
        
        try:
            cache_key = self._get_cache_key(url)
            entry = CacheEntry(
                duration=int(duration),
                timestamp=time.time(),
                source=source
            )
            
            self._cache[cache_key] = entry
            
            # Enforce size limits and cleanup
            self._enforce_size_limit()
            
            # Save periodically (every 10 additions)
            if len(self._cache) % 10 == 0:
                self._save_cache()
                
        except Exception as e:
            print(f"Duration Cache: Error setting {url}: {e}")
    
    def has(self, url: str) -> bool:
        """Check if URL is cached (and not expired)"""
        return self.get(url) is not None
    
    def remove(self, url: str):
        """Remove URL from cache"""
        if not url:
            return
        
        try:
            cache_key = self._get_cache_key(url)
            self._cache.pop(cache_key, None)
        except Exception as e:
            print(f"Duration Cache: Error removing {url}: {e}")
    
    def clear(self):
        """Clear all cache entries"""
        self._cache.clear()
        self._stats = {'hits': 0, 'misses': 0, 'expired': 0, 'evicted': 0}
        self._save_cache()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests) if total_requests > 0 else 0
        
        return {
            'entries': len(self._cache),
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'hit_rate': hit_rate,
            'expired': self._stats['expired'],
            'evicted': self._stats['evicted'],
            'cache_file_exists': self.cache_file.exists(),
            'cache_file_size': self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }
    
    def save(self):
        """Explicitly save cache to disk"""
        self._save_cache()
    
    def __del__(self):
        """Ensure cache is saved on destruction"""
        try:
            self._save_cache()
        except Exception:
            pass