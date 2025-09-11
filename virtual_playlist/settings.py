#!/usr/bin/env python3
"""
Virtual Playlist Settings for Silence Suzuka Player

Configuration for virtual playlist behavior.
"""

from dataclasses import dataclass


@dataclass
class VirtualPlaylistSettings:
    """Virtual Playlist configuration settings"""
    
    # Main toggle
    enabled: bool = False
    
    # Performance settings
    viewport_buffer_size: int = 10  # How many off-screen items to keep loaded above/below viewport
    item_height: int = 28  # Expected item height in pixels for scroll calculations
    
    # Loading settings
    lazy_loading: bool = True  # Enable on-demand metadata loading
    lazy_threshold: int = 5  # How many items ahead to start loading
    
    # Memory management
    auto_cleanup: bool = True  # Automatically unload off-screen items
    cleanup_threshold: int = 100  # Max items to keep in memory before cleanup
    
    # Performance thresholds
    enable_threshold: int = 500  # Minimum playlist size to enable virtual mode automatically
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'enabled': self.enabled,
            'viewport_buffer_size': self.viewport_buffer_size,
            'item_height': self.item_height,
            'lazy_loading': self.lazy_loading,
            'lazy_threshold': self.lazy_threshold,
            'auto_cleanup': self.auto_cleanup,
            'cleanup_threshold': self.cleanup_threshold,
            'enable_threshold': self.enable_threshold
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(
            enabled=data.get('enabled', False),
            viewport_buffer_size=data.get('viewport_buffer_size', 10),
            item_height=data.get('item_height', 28),
            lazy_loading=data.get('lazy_loading', True),
            lazy_threshold=data.get('lazy_threshold', 5),
            auto_cleanup=data.get('auto_cleanup', True),
            cleanup_threshold=data.get('cleanup_threshold', 100),
            enable_threshold=data.get('enable_threshold', 500)
        )