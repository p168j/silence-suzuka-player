"""
Virtual Playlist Module for Silence Suzuka Player

Provides virtual playlist functionality for handling large playlists efficiently.
"""

from .settings import VirtualPlaylistSettings

# Import GUI components only if available (for testing compatibility)
try:
    from .manager import VirtualPlaylistItemManager
    from .widget import VirtualPlaylistWidget
    
    __all__ = ['VirtualPlaylistSettings', 'VirtualPlaylistItemManager', 'VirtualPlaylistWidget']
except ImportError:
    # GUI components not available (e.g., in headless environment)
    __all__ = ['VirtualPlaylistSettings']