#!/usr/bin/env python3
"""
Virtual Playlist Item Manager for Silence Suzuka Player

Manages the lifecycle of virtual playlist items including loading, unloading,
and viewport calculations.
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import QRect

from .settings import VirtualPlaylistSettings


class VirtualPlaylistItemManager:
    """Manages virtual playlist items and viewport calculations"""
    
    def __init__(self, tree_widget: QTreeWidget, settings: VirtualPlaylistSettings):
        self.tree_widget = tree_widget
        self.settings = settings
        
        # Cache of created items: {index: QTreeWidgetItem}
        self.visible_items: Dict[int, QTreeWidgetItem] = {}
        
        # Current visible range
        self.visible_start = 0
        self.visible_end = 0
        
        # Total playlist data
        self.playlist_data: List[Dict[str, Any]] = []
        
        # Group information for grouped playlists
        self.group_data: Dict[str, Any] = {}
        self.is_grouped = False
        
    def set_playlist_data(self, playlist: List[Dict[str, Any]], group_info: Optional[Dict[str, Any]] = None):
        """Set the full playlist data"""
        self.playlist_data = playlist
        self.group_data = group_info or {}
        self.is_grouped = bool(group_info)
        
        # Clear existing items when data changes
        self.clear_items()
    
    def clear_items(self):
        """Clear all cached items"""
        self.visible_items.clear()
        self.visible_start = 0
        self.visible_end = 0
    
    def calculate_visible_range(self) -> Tuple[int, int]:
        """Calculate which playlist items should be visible based on scroll position"""
        if not self.playlist_data:
            return 0, 0
        
        # Get viewport geometry
        viewport = self.tree_widget.viewport()
        viewport_rect = viewport.rect()
        
        # Calculate scroll position
        v_scrollbar = self.tree_widget.verticalScrollBar()
        scroll_value = v_scrollbar.value()
        
        # Calculate visible range based on scroll value and viewport size
        items_per_page = max(1, viewport_rect.height() // self.settings.item_height)
        start_index = max(0, scroll_value)  # scroll value is already in item units
        
        # Add buffer above and below
        buffered_start = max(0, start_index - self.settings.viewport_buffer_size)
        buffered_end = min(len(self.playlist_data), 
                          start_index + items_per_page + self.settings.viewport_buffer_size)
        
        return buffered_start, buffered_end
    
    def get_visible_indices(self) -> List[int]:
        """Get list of currently visible playlist indices"""
        start, end = self.calculate_visible_range()
        return list(range(start, end))
    
    def should_update_viewport(self) -> bool:
        """Check if viewport needs updating based on scroll position"""
        new_start, new_end = self.calculate_visible_range()
        
        # Update if visible range changed significantly
        threshold = self.settings.viewport_buffer_size // 2
        start_diff = abs(new_start - self.visible_start)
        end_diff = abs(new_end - self.visible_end)
        
        return start_diff > threshold or end_diff > threshold
    
    def update_visible_items(self, create_item_func, icon_func, duration_func) -> List[int]:
        """
        Update visible items and return list of indices that need duration fetching
        
        Args:
            create_item_func: Function to create QTreeWidgetItem (title, duration_str) -> QTreeWidgetItem
            icon_func: Function to get icon for item type (item_type) -> QIcon
            duration_func: Function to format duration (duration_seconds) -> str
        
        Returns:
            List of playlist indices that need duration fetching
        """
        new_start, new_end = self.calculate_visible_range()
        
        # Get items that should be visible now
        should_be_visible = set(range(new_start, new_end))
        currently_visible = set(self.visible_items.keys())
        
        # Remove items that are no longer visible
        to_remove = currently_visible - should_be_visible
        for idx in to_remove:
            item = self.visible_items.pop(idx)
            # Remove from tree widget
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                root = self.tree_widget.invisibleRootItem()
                root.removeChild(item)
        
        # Add new items that should be visible
        to_add = should_be_visible - currently_visible
        items_needing_duration = []
        
        for idx in to_add:
            if idx < len(self.playlist_data):
                item_data = self.playlist_data[idx]
                
                # Create tree widget item
                title = item_data.get('title', 'Unknown')
                duration = item_data.get('duration', 0)
                duration_str = duration_func(duration)
                
                tree_item = create_item_func(title, duration_str)
                
                # Set icon
                item_type = item_data.get('type', 'unknown')
                icon = icon_func(item_type)
                if icon:
                    tree_item.setIcon(0, icon)
                
                # Store item data
                tree_item.setData(0, 0x0100, ('current', idx, item_data))  # Qt.UserRole
                
                # Add to cache
                self.visible_items[idx] = tree_item
                
                # Check if needs duration fetching
                if not duration and item_type in ('youtube', 'bilibili', 'local'):
                    items_needing_duration.append(idx)
        
        # Update visible range tracking
        self.visible_start = new_start
        self.visible_end = new_end
        
        return items_needing_duration
    
    def cleanup_memory(self):
        """Clean up memory if too many items are cached"""
        if not self.settings.auto_cleanup:
            return
        
        if len(self.visible_items) > self.settings.cleanup_threshold:
            # Keep only items in current visible range
            current_start, current_end = self.calculate_visible_range()
            current_visible = set(range(current_start, current_end))
            
            to_remove = []
            for idx in self.visible_items:
                if idx not in current_visible:
                    to_remove.append(idx)
            
            for idx in to_remove:
                item = self.visible_items.pop(idx)
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    root = self.tree_widget.invisibleRootItem()
                    root.removeChild(item)
    
    def get_item_by_index(self, playlist_index: int) -> Optional[QTreeWidgetItem]:
        """Get tree widget item for a specific playlist index"""
        return self.visible_items.get(playlist_index)
    
    def is_virtual_mode_beneficial(self) -> bool:
        """Check if virtual mode would be beneficial for current playlist size"""
        return len(self.playlist_data) >= self.settings.enable_threshold