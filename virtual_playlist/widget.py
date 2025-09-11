#!/usr/bin/env python3
"""
Virtual Playlist Widget for Silence Suzuka Player

A QTreeWidget that efficiently handles large playlists through virtualization.
"""

from typing import List, Dict, Any, Optional, Callable
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QAbstractItemView, QHeaderView
from PySide6.QtGui import QIcon

from .settings import VirtualPlaylistSettings
from .manager import VirtualPlaylistItemManager


class VirtualPlaylistWidget(QTreeWidget):
    """
    Virtual playlist widget that only renders visible items for performance.
    Inherits from existing PlaylistTree functionality.
    """
    
    # Signal emitted when items need duration fetching
    itemsNeedDuration = Signal(list)  # List of (index, item_dict) tuples
    
    def __init__(self, player, settings: VirtualPlaylistSettings):
        super().__init__()
        self.player = player
        self.settings = settings
        
        # Initialize like original PlaylistTree
        self._setup_tree_widget()
        
        # Virtual playlist manager
        self.item_manager = VirtualPlaylistItemManager(self, settings)
        
        # Timer for delayed viewport updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._delayed_viewport_update)
        self.update_timer.setSingleShot(True)
        
        # Functions for item creation (set by parent)
        self.create_item_func: Optional[Callable] = None
        self.icon_func: Optional[Callable] = None
        self.duration_func: Optional[Callable] = None
        
        # Connect scroll events
        v_scrollbar = self.verticalScrollBar()
        v_scrollbar.valueChanged.connect(self._on_scroll)
        
        # Debug mode (can be enabled for troubleshooting)
        self._debug_virtual = False
    
    def enable_debug_mode(self, enabled: bool = True):
        """Enable or disable debug output for virtual playlist"""
        self._debug_virtual = enabled
        
    def _setup_tree_widget(self):
        """Setup tree widget like the original PlaylistTree"""
        # Enable headers and set column labels
        self.setHeaderLabels(["Title", "Duration"])
        self.setHeaderHidden(True)
        
        # Column sizing
        header = self.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Title stretches
        header.setSectionResizeMode(1, QHeaderView.Fixed)    # Duration fixed
        self.setColumnWidth(1, 70)
        
        # Other configurations
        self.setObjectName('playlistTree')
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setWordWrap(False)
        self.setTextElideMode(Qt.ElideRight)
    
    def set_helper_functions(self, create_item_func, icon_func, duration_func):
        """Set helper functions for creating items"""
        self.create_item_func = create_item_func
        self.icon_func = icon_func  
        self.duration_func = duration_func
    
    def set_playlist_data(self, playlist: List[Dict[str, Any]], group_info: Optional[Dict] = None):
        """Set playlist data and trigger virtual rendering"""
        self.item_manager.set_playlist_data(playlist, group_info)
        
        # Check if virtual mode is beneficial
        is_beneficial = self.item_manager.is_virtual_mode_beneficial()
        playlist_size = len(playlist)
        threshold = self.settings.enable_threshold
        
        # Debug info can be disabled in production
        if hasattr(self, '_debug_virtual') and self._debug_virtual:
            print(f"Virtual Playlist: Size={playlist_size}, Threshold={threshold}, Beneficial={is_beneficial}")
        
        if not is_beneficial:
            # Fallback to regular rendering for small playlists
            if hasattr(self, '_debug_virtual') and self._debug_virtual:
                print(f"Virtual Playlist: Falling back to regular mode (playlist too small)")
            return False
        
        if hasattr(self, '_debug_virtual') and self._debug_virtual:
            print(f"Virtual Playlist: Using virtual mode for {playlist_size} items")
        self._update_virtual_viewport()
        return True
    
    def _on_scroll(self, value):
        """Handle scroll events with debouncing"""
        if self.settings.enabled and self.item_manager.should_update_viewport():
            # Use timer to debounce rapid scroll events
            self.update_timer.start(16)  # ~60fps updates
    
    def _delayed_viewport_update(self):
        """Update viewport after scroll debounce"""
        self._update_virtual_viewport()
    
    def _update_virtual_viewport(self):
        """Update the virtual viewport by creating/destroying items as needed"""
        if not self.settings.enabled or not all([self.create_item_func, self.icon_func, self.duration_func]):
            return
        
        try:
            # Debug info can be disabled in production
            total_items = len(self.item_manager.playlist_data)
            if hasattr(self, '_debug_virtual') and self._debug_virtual:
                print(f"Virtual Playlist: Updating viewport for {total_items} total items")
            
            # Update visible items
            items_needing_duration = self.item_manager.update_visible_items(
                self.create_item_func,
                self.icon_func, 
                self.duration_func
            )
            
            visible_count = len(self.item_manager.visible_items)
            if hasattr(self, '_debug_virtual') and self._debug_virtual:
                print(f"Virtual Playlist: {visible_count} items visible, {len(items_needing_duration)} need duration")
            
            # Request duration fetching for items that need it
            if items_needing_duration and self.settings.lazy_loading:
                duration_items = []
                for idx in items_needing_duration:
                    if idx < len(self.item_manager.playlist_data):
                        item_data = self.item_manager.playlist_data[idx]
                        duration_items.append((idx, item_data))
                
                if duration_items:
                    self.itemsNeedDuration.emit(duration_items)
            
            # Cleanup memory if needed
            self.item_manager.cleanup_memory()
            
        except Exception as e:
            print(f"Virtual playlist viewport update error: {e}")
    
    def get_visible_indices(self) -> List[int]:
        """Get currently visible playlist indices for duration fetching prioritization"""
        return self.item_manager.get_visible_indices()
    
    def update_item_duration(self, playlist_index: int, duration: float):
        """Update duration for a specific item if it's visible"""
        item = self.item_manager.get_item_by_index(playlist_index)
        if item and self.duration_func:
            duration_str = self.duration_func(duration)
            item.setText(1, duration_str)
            item.setTextAlignment(1, Qt.AlignRight | Qt.AlignVCenter)
    
    def refresh_virtual_playlist(self, playlist: List[Dict[str, Any]], expansion_state: Optional[Dict] = None):
        """Refresh the virtual playlist with new data"""
        if not self.settings.enabled:
            return False
        
        # Set new playlist data
        success = self.set_playlist_data(playlist)
        if not success:
            return False  # Fall back to regular mode
        
        # Clear tree 
        self.clear()
        
        # For virtual mode, only create and show visible items
        # The scrolling will be handled by managing visible items dynamically
        self._update_virtual_viewport()
        return True
    
    def find_item_by_playlist_index(self, playlist_index: int) -> Optional[QTreeWidgetItem]:
        """Find tree widget item by playlist index"""
        return self.item_manager.get_item_by_index(playlist_index)
    
    def get_virtual_stats(self) -> Dict[str, Any]:
        """Get statistics about virtual playlist performance"""
        return {
            'enabled': self.settings.enabled,
            'total_items': len(self.item_manager.playlist_data),
            'visible_items': len(self.item_manager.visible_items), 
            'visible_range': (self.item_manager.visible_start, self.item_manager.visible_end),
            'memory_beneficial': self.item_manager.is_virtual_mode_beneficial()
        }
    
    # Override dropEvent to maintain compatibility with drag-and-drop
    def dropEvent(self, event):
        """Handle drag-and-drop events - delegate to parent's implementation"""
        # For virtual mode, we need to be careful about drag-and-drop
        # For now, disable virtual mode during drag operations
        if hasattr(self.player, '_playlist_tree_drop_event'):
            # Call parent's drop handling
            self.player._playlist_tree_drop_event(event, self)
        else:
            # Fallback to standard behavior
            super().dropEvent(event)