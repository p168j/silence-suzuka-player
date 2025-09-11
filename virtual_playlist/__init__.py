"""
Virtual Playlist Module for Silence Suzuka Player

Provides virtual playlist functionality for handling large playlists efficiently.
"""

from .settings import VirtualPlaylistSettings
from .manager import VirtualPlaylistItemManager
from .widget import VirtualPlaylistWidget

__all__ = ['VirtualPlaylistSettings', 'VirtualPlaylistItemManager', 'VirtualPlaylistWidget']