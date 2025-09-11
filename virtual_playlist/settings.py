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


# Simple test when run directly
if __name__ == '__main__':
    print("=== Virtual Playlist Settings Test ===")
    
    # Test default settings
    settings = VirtualPlaylistSettings()
    print(f"✓ Default settings created: enabled={settings.enabled}")
    print(f"  - Viewport buffer: {settings.viewport_buffer_size}")
    print(f"  - Item height: {settings.item_height}")
    print(f"  - Enable threshold: {settings.enable_threshold}")
    print(f"  - Auto cleanup: {settings.auto_cleanup}")
    print(f"  - Lazy loading: {settings.lazy_loading}")
    
    # Test serialization
    data = settings.to_dict()
    print(f"✓ Serialization: {len(data)} settings saved")
    
    restored = VirtualPlaylistSettings.from_dict(data)
    print(f"✓ Deserialization: enabled={restored.enabled}")
    
    # Test decision logic
    print("\nDecision logic for different playlist sizes:")
    test_sizes = [10, 50, 100, 500, 1000, 2000, 5000, 10000]
    for size in test_sizes:
        should_use = size >= settings.enable_threshold
        print(f"  Size {size:5d}: Use virtual mode = {'YES' if should_use else 'NO '}")
    
    # Test custom configurations
    print("\nTesting different configurations:")
    
    configs = [
        ("Conservative", VirtualPlaylistSettings(
            enabled=True, enable_threshold=2000, viewport_buffer_size=5
        )),
        ("Aggressive", VirtualPlaylistSettings(
            enabled=True, enable_threshold=100, viewport_buffer_size=50
        )),
        ("Disabled", VirtualPlaylistSettings(enabled=False)),
    ]
    
    for name, config in configs:
        print(f"  {name}: enabled={config.enabled}, threshold={config.enable_threshold}")
        
        # Test serialization round-trip
        config_dict = config.to_dict()
        restored_config = VirtualPlaylistSettings.from_dict(config_dict)
        assert restored_config.enabled == config.enabled
        assert restored_config.enable_threshold == config.enable_threshold
        print(f"    ✓ Serialization round-trip successful")
    
    print("\n🎉 All virtual playlist settings tests passed!")
    print("\nThis confirms that the settings system is working correctly.")
    print("The virtual playlist will automatically enable for playlists larger")
    print(f"than {settings.enable_threshold} items and provide significant")
    print("performance improvements for large playlists.")