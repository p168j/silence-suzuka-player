#!/usr/bin/env python3
"""
Duration Fetch Settings for Silence Suzuka Player

Configuration for background duration fetching system following the same pattern
as SmartQueueSettings for consistency.
"""

from dataclasses import dataclass


@dataclass
class DurationFetchSettings:
    """Duration fetch configuration settings"""
    
    # Main toggle
    auto_fetch_enabled: bool = True
    
    # Threading settings
    worker_thread_count: int = 2
    max_concurrent_fetches: int = 3
    
    # Timeout settings (seconds)
    fetch_timeout: int = 30
    retry_timeout: int = 60
    
    # Cache settings
    cache_enabled: bool = True
    cache_max_age_days: int = 30
    cache_max_entries: int = 10000
    
    # Prioritization settings
    prioritize_visible: bool = True
    prioritize_recent: bool = True
    batch_size: int = 10
    
    # Rate limiting
    delay_between_fetches_ms: int = 300
    max_retries: int = 3
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'auto_fetch_enabled': self.auto_fetch_enabled,
            'worker_thread_count': self.worker_thread_count,
            'max_concurrent_fetches': self.max_concurrent_fetches,
            'fetch_timeout': self.fetch_timeout,
            'retry_timeout': self.retry_timeout,
            'cache_enabled': self.cache_enabled,
            'cache_max_age_days': self.cache_max_age_days,
            'cache_max_entries': self.cache_max_entries,
            'prioritize_visible': self.prioritize_visible,
            'prioritize_recent': self.prioritize_recent,
            'batch_size': self.batch_size,
            'delay_between_fetches_ms': self.delay_between_fetches_ms,
            'max_retries': self.max_retries
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(
            auto_fetch_enabled=data.get('auto_fetch_enabled', True),
            worker_thread_count=data.get('worker_thread_count', 3),
            max_concurrent_fetches=data.get('max_concurrent_fetches', 5),
            fetch_timeout=data.get('fetch_timeout', 15),
            retry_timeout=data.get('retry_timeout', 30),
            cache_enabled=data.get('cache_enabled', True),
            cache_max_age_days=data.get('cache_max_age_days', 30),
            cache_max_entries=data.get('cache_max_entries', 10000),
            prioritize_visible=data.get('prioritize_visible', True),
            prioritize_recent=data.get('prioritize_recent', True),
            batch_size=data.get('batch_size', 10),
            delay_between_fetches_ms=data.get('delay_between_fetches_ms', 100),
            max_retries=data.get('max_retries', 2)
        )