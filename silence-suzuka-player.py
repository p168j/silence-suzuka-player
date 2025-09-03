#!/usr/bin/env python3
"""
Silence Auto-Player (mpv edition)
- mpv backend for fast streaming and near-instant next/prev
- System-wide silence monitor (auto-play on silence)
- AFK monitor (auto-pause on inactivity)
- Tray icon + tooltip reflecting playback state
- Saved playlist management (save/load)
- Theme styling (Dark) and optional thumbnails
"""

import sys
import os
import json
import time
import logging
import zipfile
import qtawesome as qta
import re
import queue
import warnings
from PySide6.QtGui import QIcon
from pathlib import Path
from datetime import datetime
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QProgressBar, QMessageBox, QFileDialog,
    QInputDialog, QMenu, QFrame, QScrollArea, QWidget, QAbstractItemView,
    QDialogButtonBox, QTabWidget, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QBrush
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QSize, QRectF, QByteArray
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCursor
from PySide6.QtGui import QShortcut
from PySide6.QtWidgets import QProxyStyle, QStyle, QStyledItemDelegate
from PySide6.QtGui import QPainter, QColor, QPolygon
from PySide6.QtCore import QPoint
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QFont, QFontDatabase, QFontMetrics, QPalette
from PySide6.QtCore import QTimer, QEvent
from PySide6.QtGui import QInputMethodEvent
from PySide6.QtWidgets import QLineEdit
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QProgressBar, QMessageBox, QFileDialog,
    QInputDialog, QMenu, QFrame, QScrollArea, QWidget, QAbstractItemView,
    QDialogButtonBox, QTabWidget, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QBrush
from PySide6.QtWidgets import QGraphicsColorizeEffect


class PlaylistMetadataWidget(QWidget):
    """Widget to display playlist metadata in a card-like format"""
    
    def __init__(self, playlist_data, parent=None):
        super().__init__(parent)
        self.playlist_data = playlist_data
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Title
        name = self.playlist_data.get('name', 'Unnamed Playlist')
        title_label = QLabel(name)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #e76f51; margin-bottom: 4px;")
        layout.addWidget(title_label)
        
        # Metadata grid
        metadata = self.playlist_data.get('metadata', {})
        items = self.playlist_data.get('items', [])
        
        info_layout = QGridLayout()
        info_layout.setSpacing(6)
        
        # Basic stats
        info_layout.addWidget(QLabel("Items:"), 0, 0)
        info_layout.addWidget(QLabel(str(len(items))), 0, 1)
        
        info_layout.addWidget(QLabel("Created:"), 1, 0)
        created_date = metadata.get('created', '')
        if created_date:
            try:
                dt = datetime.fromisoformat(created_date)
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except:
                formatted_date = created_date
        else:
            formatted_date = "Unknown"
        info_layout.addWidget(QLabel(formatted_date), 1, 1)
        
        # Duration (if available)
        total_duration = metadata.get('total_duration', 0)
        if total_duration > 0:
            info_layout.addWidget(QLabel("Duration:"), 2, 0)
            info_layout.addWidget(QLabel(self._format_duration(total_duration)), 2, 1)
        
        # Source breakdown
        source_counts = {}
        for item in items:
            source_type = item.get('type', 'unknown')
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
        
        if source_counts:
            info_layout.addWidget(QLabel("Sources:"), 3, 0)
            sources_text = ", ".join(f"{count} {type}" for type, count in source_counts.items())
            sources_label = QLabel(sources_text)
            sources_label.setWordWrap(True)
            info_layout.addWidget(sources_label, 3, 1)
        
        layout.addLayout(info_layout)
        
        # Description (if available)
        description = metadata.get('description', '')
        if description:
            layout.addWidget(QLabel("Description:"))
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("background: rgba(0,0,0,0.1); padding: 8px; border-radius: 4px;")
            layout.addWidget(desc_label)
    
    def _format_duration(self, seconds):
        """Format duration in seconds to human readable format"""
        if seconds < 60:
            return f"{int(seconds)}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{int(minutes)}m {int(seconds % 60)}s"
        hours = minutes // 60
        return f"{int(hours)}h {int(minutes % 60)}m"

class PlaylistPreviewWidget(QTreeWidget):
    """Widget to preview playlist contents"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(["Title", "Source", "Duration"])
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.setMaximumHeight(200)
        self.setIconSize(QSize(28, 28))

        self.setStyleSheet("""
            QTreeWidget::item {
                min-height: 36px;      /* A taller row for good spacing */
                padding-left: 5px;     /* A little space on the left */
                padding-top: 4px;      /* This pushes the icon/text down to the center */
            }
        """)
    
    def load_playlist_items(self, items):
        """Load playlist items into the preview"""
        self.clear()
        
        for item in items[:50]:  # Limit to first 50 for performance
            title = item.get('title', 'Unknown')
            source = item.get('type', 'unknown').title()
            
            # Try to get duration from metadata if available
            duration_text = "Unknown"
            
            tree_item = QTreeWidgetItem([title, source, duration_text])
            
            # Add source icons
            item_type = item.get('type')
            icon_size = QSize(28, 28) # Corrected size
            if item_type == 'youtube':
                icon = load_svg_icon(str(APP_DIR / 'icons/youtube-fa7.svg'), icon_size)
                tree_item.setIcon(0, icon)
            elif item_type == 'bilibili':
                icon = load_svg_icon(str(APP_DIR / 'icons/bilibili-fa7.svg'), icon_size)
                tree_item.setIcon(0, icon)
            elif item_type == 'local':
                # Use emoji for local as no SVG was specified
                tree_item.setText(0, f"🎬 {title}")
            
            self.addTopLevelItem(tree_item)
        
        # Add "..." item if there are more items
        if len(items) > 50:
            more_item = QTreeWidgetItem([f"... and {len(items) - 50} more items", "", ""])
            more_item.setDisabled(True)
            self.addTopLevelItem(more_item)

class PlaylistSaveDialog(QDialog):
    """Enhanced dialog for saving playlists with metadata"""
    def _size_and_center_relative_to_parent(self, parent):
        """Calculate and set size relative to the parent window."""
        if not parent:
            return
        parent_geom = parent.geometry()
        
        # Set the dialog size to be a percentage of the parent's size
        self.resize(int(parent_geom.width() * 0.45), int(parent_geom.height() * 0.65))
        
        # Move the dialog to be centered over the parent
        self_geom = self.geometry()
        center_point = parent_geom.center()
        self_geom.moveCenter(center_point)
        self.move(self_geom.topLeft())
    
    def __init__(self, current_playlist, existing_names=None, parent=None):
        super().__init__(parent)
        self.current_playlist = current_playlist
        self.existing_names = existing_names or []
        self.setWindowTitle("Save Playlist")
        self.setModal(True)

        self._setup_ui()

        # Apply the theme from the parent window
        if parent and hasattr(parent, '_apply_dialog_theme'): # <--- ADD THIS BLOCK
            parent._apply_dialog_theme(self)

        # Size and center the dialog after the UI is built
        self._size_and_center_relative_to_parent(parent)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Header
        header_label = QLabel("Save Current Playlist")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setStyleSheet("color: #e76f51; margin-bottom: 10px;")
        layout.addWidget(header_label)
        
        # Playlist info
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Box)
        info_frame.setStyleSheet("background: rgba(0,0,0,0.05); border-radius: 6px; padding: 8px;")
        info_layout = QHBoxLayout(info_frame)
        
        source_counts = {}
        for item in self.current_playlist:
            source_type = item.get('type', 'unknown')
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
        
        sources_text = ", ".join(f"{count} {type}" for type, count in source_counts.items())
        info_label = QLabel(f"📊 {len(self.current_playlist)} items ({sources_text})")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_frame)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter playlist name...")
        self.name_edit.textChanged.connect(self._validate_name)
        form_layout.addRow("Name:", self.name_edit)
        
        # Description field
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Optional description...")
        self.desc_edit.setMaximumHeight(80)
        form_layout.addRow("Description:", self.desc_edit)
        
        # Options
        self.overwrite_existing = QCheckBox("Overwrite if name exists")
        form_layout.addRow("", self.overwrite_existing)
        
        layout.addLayout(form_layout)
        
        # Preview (collapsible)
        preview_group = QGroupBox("Preview (first 20 items):")
        preview_layout = QVBoxLayout(preview_group)
        
        
        self.preview_list = QListWidget()
        self.preview_list.setIconSize(QSize(28, 28))
        self.preview_list.setAlternatingRowColors(True)
        self.preview_list.setStyleSheet("""
        QListWidget {
            background-color: #f0e7cf;
            color: #4a2c2a;
            border: 1px solid #c2a882;
            border-radius: 4px;
            alternate-background-color: #e9e0c8;
        }
        QListWidget::item { 
            padding: 4px 6px; 
        }
        """)
                          
        self.preview_list.setMaximumHeight(150)

        for item in self.current_playlist[:20]:
            title = item.get('title', 'Unknown')
            item_type = item.get('type')

            # Create the list item with just the title
            list_item = QListWidgetItem(title)

            # Set the icon based on the source type
            icon_size = QSize(28, 28) # Corrected size
            if item_type == 'youtube':
                icon = load_svg_icon(str(APP_DIR / 'icons/youtube-fa7.svg'), icon_size)
                list_item.setIcon(icon)
            elif item_type == 'bilibili':
                icon = load_svg_icon(str(APP_DIR / 'icons/bilibili-fa7.svg'), icon_size)
                list_item.setIcon(icon)
            else:
                # Fallback for other types like 'local'
                emoji = {"local": "🎬"}.get(item_type, "🎵")
                list_item.setText(f"{emoji} {title}")

            self.preview_list.addItem(list_item)
        
        if len(self.current_playlist) > 20:
            more_item = QListWidgetItem(f"... and {len(self.current_playlist) - 20} more")
            more_item.setFlags(more_item.flags() & ~Qt.ItemIsSelectable)
            self.preview_list.addItem(more_item)

        self.preview_list.setAlternatingRowColors(True)
        
        preview_layout.addWidget(self.preview_list)
        layout.addWidget(preview_group)
        
        # Validation message
        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet("color: #d86a4a; font-weight: bold;")
        layout.addWidget(self.validation_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("💾 Save Playlist")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)
        
        # Set focus to name field
        self.name_edit.setFocus()
        
        # Initial validation
        self._validate_name()
    
    def _validate_name(self):
        """Validate the playlist name and update UI accordingly"""
        name = self.name_edit.text().strip()
        
        if not name:
            self.validation_label.setText("⚠️ Playlist name is required")
            self.save_btn.setEnabled(False)
            return False
        
        if name in self.existing_names:
            if self.overwrite_existing.isChecked():
                self.validation_label.setText("⚠️ Will overwrite existing playlist")
                self.validation_label.setStyleSheet("color: #f39c12;")  # Orange warning
                self.save_btn.setEnabled(True)
                return True
            else:
                self.validation_label.setText("❌ Playlist name already exists")
                self.validation_label.setStyleSheet("color: #d86a4a;")  # Red error
                self.save_btn.setEnabled(False)
                return False
        
        # Valid name
        self.validation_label.setText("✅ Valid playlist name")
        self.validation_label.setStyleSheet("color: #27ae60;")  # Green success
        self.save_btn.setEnabled(True)
        return True
    
    def get_name(self):
        return self.name_edit.text().strip()
    
    def get_description(self):
        return self.desc_edit.toPlainText().strip()
    
    def should_overwrite(self):
        return self.overwrite_existing.isChecked()

class PlaylistManagerDialog(QDialog):
    """Comprehensive playlist management dialog with fixed lifecycle management"""

    def _size_and_center_relative_to_parent(self, parent):
        """Calculate and set size relative to the parent window."""
        if not parent:
            return
        parent_geom = parent.geometry()

        self.resize(int(parent_geom.width() * 0.60), int(parent_geom.height() * 0.70))

        self_geom = self.geometry()
        center_point = parent_geom.center()
        self_geom.moveCenter(center_point)
        self.move(self_geom.topLeft())
    
    def __init__(self, saved_playlists, current_playlist, parent=None):
            super().__init__(parent)
            self.saved_playlists = saved_playlists
            self.current_playlist = current_playlist
            self.selected_playlist_data = None
            self.load_mode = "replace"
            self._is_destroyed = False
            self._initial_load_done = False # Flag to ensure we only load once

            self.setWindowTitle("Playlist Manager")
            self.setModal(True)

            self._setup_ui()

            # Apply the theme from the parent window
            if parent and hasattr(parent, '_apply_dialog_theme'): # <--- ADD THIS BLOCK
                parent._apply_dialog_theme(self)

            # Size and center the dialog after the UI is built
            self._size_and_center_relative_to_parent(parent)

    def showEvent(self, event):
        """Populate the list just before the dialog is shown for the first time."""
        super().showEvent(event)
        # The _initial_load_done flag prevents this from running again
        # if the dialog is hidden and re-shown.
        if not self._initial_load_done:
            self._safe_refresh_playlist_list()
            self._initial_load_done = True        
    
    def closeEvent(self, event):
        """Mark dialog as destroyed when closing"""
        self._is_destroyed = True
        super().closeEvent(event)
    
    def reject(self):
        """Mark dialog as destroyed when rejecting"""
        self._is_destroyed = True
        super().reject()
    
    def accept(self):
        """Mark dialog as destroyed when accepting"""
        self._is_destroyed = True
        super().accept()
    
    def _safe_refresh_playlist_list(self):
        """Safe wrapper for _refresh_playlist_list that checks object validity"""
        try:
            # Check if dialog was destroyed
            if self._is_destroyed:
                print("[DEBUG] Dialog destroyed, skipping refresh")
                return
                
            # Check if we can safely access the playlist_list
            if not hasattr(self, 'playlist_list'):
                print("[DEBUG] playlist_list not available")
                return
                
            # Try to access the C++ object safely
            try:
                # This will throw RuntimeError if C++ object is deleted
                _ = self.playlist_list.count()
            except RuntimeError as e:
                print(f"[DEBUG] C++ object invalid: {e}")
                return
            
            # Proceed with actual refresh
            self._refresh_playlist_list()
            
        except Exception as e:
            print(f"[DEBUG] Safe refresh error: {e}")
    
    def _setup_ui(self):
        # Create the main layout for the dialog, but DO NOT assign it a parent yet.
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0) # Use a borderless layout for the splitter

        
        # Left panel - Playlist list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 8, 0)
        
        # Header
        header_label = QLabel("Saved Playlists")
        header_label.setFont(QFont("Arial", 14, QFont.Bold))
        left_layout.addWidget(header_label)
        
        # Playlist list
        self.playlist_list = QListWidget()
        self.playlist_list.currentItemChanged.connect(self._on_playlist_selected)
        self.playlist_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self._show_playlist_context_menu)

        self.playlist_list.setAlternatingRowColors(True)
        self.playlist_list.setStyleSheet("""
            QListWidget {
                background-color: #f0e7cf;
                color: #4a2c2a;
                border: 1px solid #c2a882;
                border-radius: 4px;
                alternate-background-color: #e9e0c8;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #e5d5b8;
                min-height: 40px;
            }
            QListWidget::item:selected {
                background-color: #e76f51;
                color: #f3ead3;
            }
            QListWidget::item:hover {
                background-color: rgba(231, 111, 81, 0.1);
            }
        """)
        left_layout.addWidget(self.playlist_list)
        
        # Quick actions
        quick_actions = QHBoxLayout()
        
        self.new_btn = QPushButton("📁 New")
        self.new_btn.setToolTip("Save current playlist as new")
        self.new_btn.clicked.connect(self._save_current_playlist)
        
        self.import_btn = QPushButton("📂 Import")
        self.import_btn.setToolTip("Import M3U playlist")
        self.import_btn.clicked.connect(self._import_playlist)
        
        quick_actions.addWidget(self.new_btn)
        quick_actions.addWidget(self.import_btn)
        quick_actions.addStretch()
        
        left_layout.addLayout(quick_actions)
        
        # Right panel - Playlist details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 0, 0, 0)
        
        # Details header
        self.details_header = QLabel("Select a playlist to view details")
        self.details_header.setFont(QFont("Arial", 14, QFont.Bold))
        right_layout.addWidget(self.details_header)
        
        # Scrollable details area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        scroll_area.setWidget(self.details_widget)
        right_layout.addWidget(scroll_area, 1)
        
        # Load options
        load_group = QGroupBox("Load Options")
        load_layout = QFormLayout(load_group)
        
        self.load_mode_combo = QComboBox()
        self.load_mode_combo.addItem("Replace current playlist", "replace")
        self.load_mode_combo.addItem("Add to current playlist", "append")
        self.load_mode_combo.addItem("Insert at current position", "insert")
        load_layout.addRow("Mode:", self.load_mode_combo)
        
        self.auto_play_check = QCheckBox("Start playing after load")
        self.auto_play_check.setChecked(True)
        load_layout.addRow("", self.auto_play_check)
        
        right_layout.addWidget(load_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("📂 Load Playlist")
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self.accept)
        
        self.export_btn = QPushButton("💾 Export M3U")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_selected)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addWidget(self.load_btn)
        
        right_layout.addLayout(button_layout)
        
        # Add panels to splitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])  # 1:2 ratio
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def _refresh_playlist_list(self):
        """Refresh the list of saved playlists - with improved safety checks"""
        try:
            print(f"[DEBUG] _refresh_playlist_list called")
            
            # Early exit if dialog is destroyed
            if self._is_destroyed:
                print("[DEBUG] Dialog destroyed, aborting refresh")
                return
                
            # Validate playlist_list exists and is accessible
            if not hasattr(self, 'playlist_list'):
                print("[DEBUG] playlist_list attribute missing")
                return
                
            # Test C++ object validity
            try:
                current_count = self.playlist_list.count()
                # print(f"[DEBUG] playlist_list is valid, current count: {current_count}")
            except RuntimeError as e:
                print(f"[DEBUG] playlist_list C++ object invalid: {e}")
                return
            except Exception as e:
                print(f"[DEBUG] Unexpected error testing playlist_list: {e}")
                return
                
            # print(f"[DEBUG] saved_playlists type: {type(self.saved_playlists)}")
            # print(f"[DEBUG] saved_playlists content: {list(self.saved_playlists.keys()) if isinstance(self.saved_playlists, dict) else 'Not a dict'}")
            
            # Clear the list safely
            self.playlist_list.clear()
            # print(f"[DEBUG] playlist_list cleared successfully")
            
            # Handle empty playlists case
            if not self.saved_playlists:
                print("[DEBUG] No saved playlists found")
                item = QListWidgetItem("No saved playlists")
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                item.setData(Qt.UserRole, None)
                
                # Check if we can still add items safely
                if not self._is_destroyed:
                    try:
                        self.playlist_list.addItem(item)
                        print(f"[DEBUG] Added placeholder item")
                    except RuntimeError:
                        print("[DEBUG] Failed to add placeholder - dialog destroyed")
                return

            # print(f"[DEBUG] Processing {len(self.saved_playlists)} saved playlists")
            
            # Sort by creation date (newest first)
            try:
                sorted_playlists = sorted(
                    self.saved_playlists.items(),
                    key=lambda x: x[1].get('metadata', {}).get('created', ''),
                    reverse=True
                )
            except Exception as e:
                print(f"[DEBUG] Sorting failed: {e}, using unsorted")
                sorted_playlists = list(self.saved_playlists.items())
            
            for i, (name, playlist_data) in enumerate(sorted_playlists):
                # Check if dialog was destroyed during iteration
                if self._is_destroyed:
                    print(f"[DEBUG] Dialog destroyed during iteration at item {i}")
                    break
                    
                # print(f"[DEBUG] Processing playlist {i+1}: '{name}'")
                
                try:
                    items = playlist_data.get('items', [])
                    metadata = playlist_data.get('metadata', {})
                    
                    # Create display text
                    item_count = len(items)
                    created = metadata.get('created', '')
                    if created:
                        try:
                            dt = datetime.fromisoformat(created)
                            age = datetime.now() - dt
                            if age.days == 0:
                                age_str = "Today"
                            elif age.days == 1:
                                age_str = "Yesterday"
                            elif age.days < 7:
                                age_str = f"{age.days} days ago"
                            else:
                                age_str = dt.strftime("%Y-%m-%d")
                        except:
                            age_str = "Unknown date"
                    else:
                        age_str = "Unknown date"
                    
                    display_text = f"{name}\n{item_count} items • {age_str}"
                    # print(f"[DEBUG] Creating list item with text: '{display_text}'")
                    
                    list_item = QListWidgetItem(display_text)
                    list_item.setData(Qt.UserRole, (name, playlist_data))
                    
                     # Add icon based on content
                    icon_size = QSize(24, 24)
                    icon_set = False

                    if any(item.get('type') == 'youtube' for item in items):
                        icon = load_svg_icon(str(APP_DIR / 'icons/youtube-fa7.svg'), icon_size)
                        list_item.setIcon(icon)
                        icon_set = True
                    elif any(item.get('type') == 'bilibili' for item in items):
                        icon = load_svg_icon(str(APP_DIR / 'icons/bilibili-fa7.svg'), icon_size)
                        list_item.setIcon(icon)
                        icon_set = True
                    
                    if not icon_set:
                        # Fallback for playlists with only local files or other types
                        list_item.setIcon(self._create_source_icon('local'))
                    
                    # Add item safely
                    if not self._is_destroyed:
                        try:
                            self.playlist_list.addItem(list_item)
                            # print(f"[DEBUG] Added playlist item, list count now: {self.playlist_list.count()}")
                        except RuntimeError:
                            print(f"[DEBUG] Failed to add item {i} - dialog destroyed")
                            break
                    else:
                        print(f"[DEBUG] Skipping item {i} - dialog destroyed")
                        break
                        
                except Exception as e:
                    print(f"[DEBUG] Error processing playlist {name}: {e}")
                    continue
            
            # print(f"[DEBUG] _refresh_playlist_list completed successfully")
                
        except Exception as e:
            print(f"[DEBUG] _refresh_playlist_list error: {e}")
            import traceback
            traceback.print_exc()
    
    def _create_source_icon(self, source_type):
        """Create a simple colored icon for source types"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        colors = {
            'youtube': QColor("#FF0000"),
            'bilibili': QColor("#00A1D6"), 
            'local': QColor("#8E44AD")
        }
        
        color = colors.get(source_type, QColor("#7F8C8D"))
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        return QIcon(pixmap)
    
    def _show_playlist_context_menu(self, pos):
        """Show context menu for the playlist list."""
        item = self.playlist_list.itemAt(pos)
        if not item or not item.data(Qt.UserRole):
            return

        menu = QMenu(self)
        self._apply_menu_theme(menu)

        menu.addAction("✏️ Rename", self._rename_selected_playlist)
        menu.addAction("🗑️ Delete", self._delete_selected_playlist)
        menu.addAction("📋 Duplicate", self._duplicate_selected_playlist)

        menu.exec(self.playlist_list.mapToGlobal(pos))

    def _rename_selected_playlist(self):
        """Rename the currently selected playlist."""
        current_item = self.playlist_list.currentItem()
        if not current_item:
            return

        name, _ = current_item.data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(self, "Rename Playlist", "New name:", QLineEdit.Normal, name)

        if ok and new_name and new_name.strip():
            new_name = new_name.strip()
            if new_name == name:
                return
            if new_name in self.saved_playlists:
                QMessageBox.warning(self, "Error", "A playlist with this name already exists.")
                return

            self.saved_playlists[new_name] = self.saved_playlists.pop(name)
            self._save_playlists()
            self._safe_refresh_playlist_list()

    def _delete_selected_playlist(self):
        """Delete the currently selected playlist with confirmation."""
        current_item = self.playlist_list.currentItem()
        if not current_item:
            return

        name, data = current_item.data(Qt.UserRole)
        item_count = len(data.get('items', []))

        reply = QMessageBox.question(
            self, "Delete Playlist",
            f"Are you sure you want to delete '{name}' ({item_count} items)?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if name in self.saved_playlists:
                del self.saved_playlists[name]
                self._save_playlists()
                self._safe_refresh_playlist_list()
                # Clear details panel
                self._on_playlist_selected(None, None)

    def _duplicate_selected_playlist(self):
        """Duplicate the currently selected playlist."""
        current_item = self.playlist_list.currentItem()
        if not current_item:
            return

        name, data = current_item.data(Qt.UserRole)
        new_name_base = f"{name} Copy"
        i = 1
        new_name = new_name_base
        while new_name in self.saved_playlists:
            i += 1
            new_name = f"{new_name_base} ({i})"
        
        # Create a deep copy
        new_data = json.loads(json.dumps(data))
        new_data['metadata']['created'] = datetime.now().isoformat()
        new_data['metadata']['description'] = f"Copy of {name}"

        self.saved_playlists[new_name] = new_data
        self._save_playlists()
        self._safe_refresh_playlist_list()

    def _on_playlist_selected(self, current_item, previous_item):
        """Handle selection change in the playlist list."""
        if self._is_destroyed or not hasattr(self, 'details_layout'):
            return

        # Clear existing details
        for i in reversed(range(self.details_layout.count())):
            widget = self.details_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not current_item or not current_item.data(Qt.UserRole):
            self.details_header.setText("Select a playlist to view details")
            self.load_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.selected_playlist_data = None
            return

        name, playlist_data = current_item.data(Qt.UserRole)
        self.selected_playlist_data = playlist_data
        
        # Update header
        self.details_header.setText(f"Details for '{name}'")
        
        # Add metadata widget
        meta_data_with_name = {'name': name, **playlist_data}
        metadata_widget = PlaylistMetadataWidget(meta_data_with_name)
        self.details_layout.addWidget(metadata_widget)

        # Add preview widget if items exist
        items = playlist_data.get('items', [])
        if items:
            preview_widget = PlaylistPreviewWidget()
            preview_widget.load_playlist_items(items)
            
            # SOLUTION 1: Make the preview widget expand to fill available space
            preview_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Remove the fixed height constraint to let it grow
            preview_widget.setMaximumHeight(16777215)  # Qt's QWIDGETSIZE_MAX
            preview_widget.setMinimumHeight(300)  # Increase minimum height for better visibility
            
            self.details_layout.addWidget(preview_widget)

        # SOLUTION 2: Only add stretch if there's NO content, or reduce the stretch
        # Instead of always adding stretch, only add it when there's minimal content
        if not items:
            self.details_layout.addStretch()
        else:
            # Add a smaller spacer instead of full stretch when there is content
            spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Minimum)
            self.details_layout.addItem(spacer)

        # Enable action buttons
        self.load_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
    
    def get_selected_playlist(self):
        """Return the data for the currently selected playlist."""
        return self.selected_playlist_data

    def get_load_mode(self):
        """Return the selected load mode ('replace', 'append', 'insert')."""
        return self.load_mode_combo.currentData()

    def should_auto_play(self):
        """Return whether to start playing after loading."""
        return self.auto_play_check.isChecked()   
    
    def _save_current_playlist(self):
        """Save the current playlist as a new entry."""
        if not self.current_playlist:
            QMessageBox.information(self, "Save Playlist", "The current playlist is empty.")
            return

        dialog = PlaylistSaveDialog(
            self.current_playlist,
            list(self.saved_playlists.keys()),
            self
        )
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            description = dialog.get_description()

            playlist_data = {
                'items': [item.copy() for item in self.current_playlist],
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'description': description,
                    'version': '2.0'
                }
            }
            self.saved_playlists[name] = playlist_data
            self._save_playlists()
            self._safe_refresh_playlist_list()

    def _import_playlist(self):
        """Import an M3U playlist file."""
        path, _ = QFileDialog.getOpenFileName(self, "Import M3U", "", "M3U Playlists (*.m3u *.m3u8)")
        if not path:
            return

        items = []
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    # Basic type guessing
                    url_lower = s.lower()
                    media_type = 'local'
                    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                        media_type = 'youtube'
                    elif 'bilibili.com' in url_lower:
                        media_type = 'bilibili'
                    
                    items.append({'title': Path(s).name, 'url': s, 'type': media_type})
        except Exception as e:
            QMessageBox.warning(self, "Import Error", f"Failed to read playlist: {e}")
            return

        if not items:
            QMessageBox.information(self, "Import", "No valid media URLs found in the file.")
            return

        name, ok = QInputDialog.getText(self, "Import Playlist", "Enter a name for the imported playlist:", QLineEdit.Normal, Path(path).stem)
        if ok and name:
            playlist_data = {
                'items': items,
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'description': f"Imported from {Path(path).name}",
                    'version': '2.0'
                }
            }
            self.saved_playlists[name] = playlist_data
            self._save_playlists()
            self._safe_refresh_playlist_list()

    def _export_selected(self):
        """Export the selected playlist to an M3U file."""
        if not self.selected_playlist_data:
            return

        current_item = self.playlist_list.currentItem()
        if not current_item:
            return
            
        name, _ = current_item.data(Qt.UserRole)
        default_filename = f"{name}.m3u8"

        path, _ = QFileDialog.getSaveFileName(self, "Export Playlist", default_filename, "M3U Playlists (*.m3u *.m3u8)")
        if not path:
            return

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for item in self.selected_playlist_data.get('items', []):
                    title = item.get('title', item.get('url', ''))
                    url = item.get('url', '')
                    f.write(f'#EXTINF:-1,{title}\n{url}\n')
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to save playlist: {e}")

    def _save_playlists(self):
        """Save the playlist data back to the JSON file."""
        try:
            config_file = Path(__file__).parent / 'playlists_v2.json'
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_playlists, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save playlists: {e}")

    def _apply_menu_theme(self, menu):
        """Apply a basic theme to a context menu."""
        # This is a simplified theme application. A more robust solution would
        # inherit the theme from the main window.
        menu.setStyleSheet("""
            QMenu {
                background-color: #2a2a2a;
                color: #f3f3f3;
                border: 1px solid #4a4a4a;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background-color: #e76f51;
            }
        """)

class EnhancedPlaylistManager:
    """Enhanced playlist management functionality to replace the basic save/load system"""
    
    def __init__(self, media_player, app_dir):
        self.player = media_player
        self.saved_playlists = {}
        self.config_file = Path(app_dir) / 'playlists_v2.json'
        self._load_playlists()
    
    def _load_playlists(self):
        """Load saved playlists from file - with debug output"""
        try:
            #p rint(f"[DEBUG] Loading playlists from: {self.config_file}")
            # print(f"[DEBUG] Config file exists: {self.config_file.exists()}")
            
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # print(f"[DEBUG] Loaded data type: {type(data)}")
                # print(f"[DEBUG] Loaded data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Handle migration from old format
                if isinstance(data, dict):
                    migrated = {}
                    for name, playlist_items in data.items():
                        if isinstance(playlist_items, list):
                            # Old format - migrate
                            print(f"[DEBUG] Migrating old format playlist: {name}")
                            migrated[name] = {
                                'items': playlist_items,
                                'metadata': {
                                    'created': datetime.now().isoformat(),
                                    'total_items': len(playlist_items),
                                    'description': 'Migrated from old format',
                                    'version': '2.0'
                                }
                            }
                        else:
                            # New format
                            # print(f"[DEBUG] Found new format playlist: {name}")
                            migrated[name] = playlist_items
                    
                    self.saved_playlists = migrated
                    # print(f"[DEBUG] Final saved_playlists: {list(self.saved_playlists.keys())}")
                    self._save_playlists()  # Save migrated format
            else:
                # Try to migrate from old playlists.json
                old_file = self.config_file.parent / 'playlists.json'
                print(f"[DEBUG] Checking old file: {old_file} (exists: {old_file.exists()})")
                if old_file.exists():
                    self._migrate_from_old_format(old_file)
            
        except Exception as e:
            print(f"Load playlists error: {e}")
            import traceback
            traceback.print_exc()
            self.saved_playlists = {}
    
    def _migrate_from_old_format(self, old_file):
        """Migrate playlists from old format"""
        try:
            with open(old_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            migrated = {}
            for name, items in old_data.items():
                if isinstance(items, list):
                    migrated[name] = {
                        'items': items,
                        'metadata': {
                            'created': datetime.now().isoformat(),
                            'total_items': len(items),
                            'description': 'Migrated from v1',
                            'version': '2.0'
                        }
                    }
            
            self.saved_playlists = migrated
            self._save_playlists()
            
            # Backup old file
            backup_file = old_file.parent / f'{old_file.stem}_backup.json'
            old_file.rename(backup_file)
            
            print(f"Migrated {len(migrated)} playlists from old format")
            
        except Exception as e:
            print(f"Migration error: {e}")
    
    def _save_playlists(self):
        """Save playlists to file"""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.saved_playlists, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Save playlists error: {e}")
    
    def save_current_playlist(self):
        """Save current playlist with enhanced dialog"""
        if not self.player.playlist:
            QMessageBox.information(
                self.player, "Save Playlist", 
                "Current playlist is empty.\n\nAdd some media first!"
            )
            return False
        
        dialog = PlaylistSaveDialog(
            self.player.playlist, 
            list(self.saved_playlists.keys()),
            self.player
        )
        
        if dialog.exec() == QDialog.Accepted:
            name = dialog.get_name()
            description = dialog.get_description()
            
            # Calculate metadata
            source_counts = {}
            for item in self.player.playlist:
                source_type = item.get('type', 'unknown')
                source_counts[source_type] = source_counts.get(source_type, 0) + 1
            
            # Create enhanced playlist data
            playlist_data = {
                'items': [item.copy() for item in self.player.playlist],
                'metadata': {
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat(),
                    'total_items': len(self.player.playlist),
                    'source_breakdown': source_counts,
                    'description': description,
                    'saved_from_index': self.player.current_index,
                    'version': '2.0'
                }
            }
            
            # Handle overwrite
            if name in self.saved_playlists and not dialog.should_overwrite():
                return False
            
            self.saved_playlists[name] = playlist_data
            self._save_playlists()
            
            self.player.status.showMessage(f"Saved playlist '{name}' ({len(self.player.playlist)} items)", 4000)
            return True
        
        return False
    
    def load_playlist_dialog(self):
        """Show enhanced playlist manager dialog with proper lifecycle management"""
        if not self.saved_playlists:
            reply = QMessageBox.question(
                self.player, "No Saved Playlists",
                "No saved playlists found.\n\nWould you like to save the current playlist?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.save_current_playlist()
            return
        
        # CRITICAL FIX: Store dialog as instance variable to prevent garbage collection
        self.dialog = PlaylistManagerDialog(
            self.saved_playlists, 
            self.player.playlist, 
            self.player  
        )
        
        # Show the dialog and handle result
        result = self.dialog.exec()
        
        if result == QDialog.Accepted:
            selected_data = self.dialog.get_selected_playlist()
            load_mode = self.dialog.get_load_mode()
            should_auto_play = self.dialog.should_auto_play()
            
            if not selected_data:
                return

            # ... rest of your existing load logic remains the same ...
            items_to_load = selected_data.get('items', [])
            if not items_to_load:
                QMessageBox.warning(
                    self.player, "Load Error", 
                    "Selected playlist is empty."
                )
                return
            
            # Store undo data
            undo_data = {
                'old_playlist': self.player.playlist.copy(),
                'old_current_index': self.player.current_index,
                'was_playing': self.player._is_playing(),
                'load_mode': load_mode,
                'items_loaded': len(items_to_load)
            }
            self.player._add_undo_operation('load_playlist', undo_data)

            # Apply the load mode
            if load_mode == 'replace':
                self.player.playlist = [item.copy() for item in items_to_load]
                self.player.current_index = 0
            elif load_mode == 'append':
                self.player.playlist.extend([item.copy() for item in items_to_load])
            elif load_mode == 'insert':
                insert_pos = max(0, self.player.current_index + 1)
                for i, item in enumerate(items_to_load):
                    self.player.playlist.insert(insert_pos + i, item.copy())

            # Save and refresh
            self.player._save_current_playlist()
            self.player._refresh_playlist_widget()
            self.player.play_scope = None
            self.player._update_scope_label()
            self.player._update_up_next()

            # Auto-play if requested
            if should_auto_play and self.player.playlist:
                if load_mode == 'replace':
                    self.player.current_index = 0
                self.player.play_current()

            self.player.status.showMessage(f"Loaded playlist ({len(items_to_load)} items)", 4000)

        else:
            # Dialog was cancelled, clear reference
            pass

    def get_playlist_names(self):
        """Get list of saved playlist names"""
        return list(self.saved_playlists.keys())
    
    def delete_playlist(self, name):
        """Delete a saved playlist"""
        if name in self.saved_playlists:
            del self.saved_playlists[name]
            self._save_playlists()
            return True
        return False
    
    def duplicate_playlist(self, name, new_name=None):
        """Duplicate an existing playlist"""
        if name not in self.saved_playlists:
            return False
        
        if not new_name:
            new_name = self._ensure_unique_name(f"{name} Copy")
        else:
            new_name = self._ensure_unique_name(new_name)
        
        # Deep copy the playlist data
        original_data = self.saved_playlists[name]
        new_data = {
            'items': [item.copy() for item in original_data.get('items', [])],
            'metadata': {
                **original_data.get('metadata', {}),
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
                'description': f"Copy of {name}"
            }
        }
        
        self.saved_playlists[new_name] = new_data
        self._save_playlists()
        return new_name

# Integration methods to add to MediaPlayer class
def enhanced_save_playlist(self):
    """Replace the old save_playlist method"""
    return self._playlist_manager.save_current_playlist()

def enhanced_load_playlist_dialog(self):
    """Replace the old load_playlist_dialog method"""
    return self._playlist_manager.load_playlist_dialog()

def _undo_load_playlist(self, data):
    """Undo a playlist load operation"""
    try:
        self.playlist = data['old_playlist']
        self.current_index = data['old_current_index']
        was_playing = data['was_playing']
        
        self._save_current_playlist()
        self._refresh_playlist_widget()
        self._recover_current_after_change(was_playing)
        
    except Exception as e:
        print(f"[UNDO] Error restoring playlist load: {e}")

def setup_enhanced_playlist_manager(player, app_dir):
    """Setup the enhanced playlist manager on an existing MediaPlayer instance"""
    
    # Create the manager
    player._playlist_manager = EnhancedPlaylistManager(player, app_dir)
    
    # Replace the button connections
    if hasattr(player, 'save_btn'):
        player.save_btn.clicked.disconnect()
        player.save_btn.clicked.connect(player.enhanced_save_playlist)
    
    if hasattr(player, 'load_btn'):
        player.load_btn.clicked.disconnect()
        player.load_btn.clicked.connect(player.enhanced_load_playlist_dialog)
    
    # Add the new methods to the player
    player.enhanced_save_playlist = enhanced_save_playlist.__get__(player)
    player.enhanced_load_playlist_dialog = enhanced_load_playlist_dialog.__get__(player)
    player._undo_load_playlist = _undo_load_playlist.__get__(player)
    
    # Update the undo system to handle playlist loads
    original_perform_undo = player._perform_undo
    
    def enhanced_perform_undo(self):
        try:
            if not self._undo_stack:
                self.status.showMessage("Nothing to undo", 2000)
                return
                
            operation = self._undo_stack.pop()
            op_type = operation['type']
            op_data = operation['data']
            
            if op_type == 'load_playlist':
                self._undo_load_playlist(op_data)
            else:
                # Call original undo logic for other operations
                self._undo_stack.append(operation)  # Put it back
                original_perform_undo()
                return
                
            self.status.showMessage(f"Undid: {op_type.replace('_', ' ').title()}", 3000)
            
        except Exception as e:
            print(f"[UNDO] Enhanced undo error: {e}")
            self.status.showMessage(f"Undo failed: {e}", 3000)
    
    player._perform_undo = enhanced_perform_undo.__get__(player)
    
    # Add playlist management to context menus
    def show_playlist_manager_menu(self):
        """Show playlist management context menu"""
        menu = QMenu(self)
        self._apply_menu_theme(menu)
        
        menu.addAction("📂 Manage Playlists", self.enhanced_load_playlist_dialog)
        menu.addAction("💾 Save Current Playlist", self.enhanced_save_playlist)
        menu.addSeparator()
        
        # Quick load submenu
        if self._playlist_manager.saved_playlists:
            quick_load = menu.addMenu("⚡ Quick Load")
            for name in sorted(self._playlist_manager.saved_playlists.keys()):
                quick_load.addAction(name, lambda n=name: self._quick_load_playlist(n))
        
        return menu
    
    def _quick_load_playlist(self, name):
        """Quick load a playlist by name (replace mode)"""
        if name not in self._playlist_manager.saved_playlists:
            return
        
        playlist_data = self._playlist_manager.saved_playlists[name]
        items = playlist_data.get('items', [])
        
        if not items:
            self.status.showMessage(f"Playlist '{name}' is empty", 3000)
            return
        
        # Confirm replacement if current playlist exists
        if self.playlist:
            reply = QMessageBox.question(
                self, "Quick Load",
                f"Replace current playlist with '{name}' ({len(items)} items)?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Store undo data
        undo_data = {
            'old_playlist': self.playlist.copy(),
            'old_current_index': self.current_index,
            'was_playing': self._is_playing(),
            'load_mode': 'replace',
            'items_loaded': len(items)
        }
        self._add_undo_operation('load_playlist', undo_data)
        
        # Load the playlist
        self.playlist = [item.copy() for item in items]
        self.current_index = 0
        
        self._save_current_playlist()
        self._refresh_playlist_widget()
        self.play_scope = None
        self._update_scope_label()
        self._update_up_next()
        
        # Auto-play
        self.play_current()
        
        self.status.showMessage(f"Loaded '{name}' ({len(items)} items)", 4000)
    
    # Add these methods to the player
    player.show_playlist_manager_menu = show_playlist_manager_menu.__get__(player)
    player._quick_load_playlist = _quick_load_playlist.__get__(player)
    
    print("Enhanced playlist manager setup complete!")

class SearchBar(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ime_composing = False  # Track IME composition state
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_search_filter)

        # Connect the textChanged signal for non-IME cases
        self.textChanged.connect(self._on_text_changed)

    def inputMethodEvent(self, event: QInputMethodEvent):
        """Handle IME input events."""
        if isinstance(event, QInputMethodEvent):
            self._ime_composing = event.commitString() == ""
            if self._ime_composing:
                # print("[DEBUG] IME composition started.")
                pass  
            else:
                # print("[DEBUG] IME composition finalized.")
                self._apply_search_filter()  # Trigger search when IME finalizes input
        super().inputMethodEvent(event)

    def _on_text_changed(self, text):
        """Start a timer to debounce inputs, unless IME is active."""
        if not self._ime_composing:
            self._search_timer.start(300)

    def _apply_search_filter(self):
        """Apply the search filter logic."""
        search_text = self.text().strip()
        # print(f"Applying search filter: {search_text}")
        # Add your filtering logic or signal emission here

# REPLACE your existing PlayingItemDelegate class with this one
class PlayingItemDelegate(QStyledItemDelegate):
    def __init__(self, player, parent=None):
        super().__init__(parent)
        self.player = player
    
    def paint(self, painter, option, index):
        # First, let Qt draw the normal item
        super().paint(painter, option, index)
        
        # Then check if this is the currently playing item to draw the background
        item = self.player.playlist_tree.itemFromIndex(index)
        if item:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, tuple) and data[0] == 'current':
                idx = data[1]
                if idx == self.player.current_index:
                    bg_color = QColor(231, 111, 81, 40) # Subtle orange tint
                    painter.save()
                    painter.fillRect(option.rect, bg_color)
                    painter.restore()

class LightChevronTreeStyle(QProxyStyle):
    def __init__(self, base=None, color="#e0e0e0"):
        super().__init__(base)
        self.chevron_color = QColor(color)

    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorBranch:
            if (option.state & QStyle.State_Children and 
                not (option.state & QStyle.State_MouseOver)):
                
                r = option.rect
                size = 8  # Smaller, more refined size
                x = r.center().x()
                y = r.center().y()
                
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing, True)
                
                # Use a thin pen for delicate lines
                pen = QPen(self.chevron_color, 1.5)  # Thinner stroke
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)  # No fill, just outline
                
                if option.state & QStyle.State_Open:
                    # ▼ (expanded) - thin triangle outline
                    points = [
                        QPoint(x - size//2, y - size//3),
                        QPoint(x + size//2, y - size//3),
                        QPoint(x, y + size//3)
                    ]
                    painter.drawPolygon(QPolygon(points))
                else:
                    # ▶ (collapsed) - thin triangle outline
                    points = [
                        QPoint(x - size//3, y - size//2),
                        QPoint(x - size//3, y + size//2),
                        QPoint(x + size//3, y)
                    ]
                    painter.drawPolygon(QPolygon(points))
                
                painter.restore()
                return
        
        super().drawPrimitive(element, option, painter, widget)

def _render_svg_tinted(svg_path, size: QSize, color: str) -> QPixmap:
    """Renders an SVG file, tinting its fill/stroke with a single color."""
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
        
        # A simple regex to find fill/stroke attributes and replace their values.
        # This works for simple, single-color icons.
        svg_data = re.sub(r'(fill|stroke)="[^"]+"', f'\\1="{color}"', svg_data)
        
        # Load the modified SVG data
        renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
        pixmap = QPixmap(size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        renderer.render(painter)
        painter.end()
        
        return pixmap
    except Exception:
        return QPixmap() # Return an empty pixmap on error

def playlist_icon_for_type(item_type):
    # Standardized to 28x28 for better visibility
    icon_size = QSize(28, 28)
    if item_type == 'youtube':
        return load_svg_icon(str(APP_DIR / 'icons/youtube-fa7.svg'), icon_size)
    elif item_type == 'bilibili':
        return load_svg_icon(str(APP_DIR / 'icons/bilibili-fa7.svg'), icon_size)
    elif item_type == 'local':
        return "🎬"
    else:
        return "🎵"
        
def load_svg_icon(path, size=QSize(18, 18)):
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, size.width(), size.height()))
    painter.end()
    return QIcon(pixmap)        

# Initialize logging
def setup_logging(level='INFO'):
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / 'silence_player.log'
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def human_duration(seconds):
    """Converts seconds to a human-readable string (e.g., 1h 5m 10s)."""
    if seconds < 0:
        return "0s"
    if seconds < 60:
        return f"{int(seconds)}s"
    
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 and hours == 0: # Only show seconds if duration is less than an hour
        parts.append(f"{seconds}s")
        
    return " ".join(parts) if parts else "0s"

def format_time(ms):
    """Converts milliseconds to a MM:SS or H:MM:SS string."""
    if ms < 0:
        return "0:00"
    
    seconds_total = ms // 1000
    minutes, seconds = divmod(seconds_total, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes}:{seconds:02d}"    

# Initialize with default level (will be updated from settings)
logger = setup_logging()

# Debug banner
logger.info("Starting Silence Suzuka Player...")
# logger.info(f"Python version: {sys.version}")

# Dependencies
required = []

try:
    from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout,
    QPushButton, QLabel, QSlider, QFileDialog, QMessageBox, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView, QStatusBar, QMenu,
    QSystemTrayIcon, QStyle, QDialog, QFormLayout, QDialogButtonBox, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QTabWidget, QToolTip, QGraphicsDropShadowEffect, QSpacerItem, QGridLayout, QSizePolicy, QTreeWidgetItemIterator, QSizePolicy
    )
    from PySide6.QtCore import Qt, QTimer, QSize, QThread, Signal, QEvent, QPropertyAnimation, QEasingCurve, Property
    from PySide6.QtGui import QIcon, QPixmap, QKeySequence, QShortcut, QAction, QPainter, QColor, QPen, QBrush, QFont, QFontDatabase, QFontMetrics, QGuiApplication
    # print("✓ PySide6 imported")
    try:
        from PySide6.QtSvg import QSvgRenderer
        # print("✓ QtSvg imported")
    except Exception as e:
        QSvgRenderer = None
        print(f"⚠ QtSvg not available: {e}")
except Exception as e:
    print(f"✗ PySide6 import failed: {e}")
    print("pip install PySide6")
    required.append("PySide6")

try:
    from mpv import MPV
    # print("✓ python-mpv imported")
except Exception as e:
    print(f"✗ python-mpv import failed: {e}")
    print("pip install python-mpv")
    required.append("python-mpv")

try:
    import yt_dlp
    # print("✓ yt-dlp imported")
except Exception as e:
    print(f"✗ yt-dlp import failed: {e}")
    print("pip install yt-dlp")
    required.append("yt-dlp")

try:
    import requests  # Optional for thumbnails
    HAVE_REQUESTS = True
    # print("✓ requests imported")
except Exception as e:
    HAVE_REQUESTS = False
    print(f"⚠ requests not available (thumbnails disabled): {e}")

if required:
    print("\n❌ Missing required modules: " + ", ".join(required))
    input("\nPress Enter to exit...")
    sys.exit(1)

APP_DIR = Path(__file__).parent
CFG_CURRENT = APP_DIR / 'current.json'
CFG_POS = APP_DIR / 'positions.json'
CFG_PLAYLISTS = APP_DIR / 'playlists.json'
CFG_SETTINGS = APP_DIR / 'config.json'
CFG_STATS = APP_DIR / 'stats.json'
COOKIES_BILI = APP_DIR / 'cookies.txt'
CFG_COMPLETED = APP_DIR / 'completed.json'
CFG_SESSION = APP_DIR / 'session.json'


# --- Monitors ---
class SystemAudioMonitor(QThread):
    silenceDetected = Signal()
    audioStateChanged = Signal(bool)
    rmsUpdated = Signal(float)

    def __init__(self, silence_duration_s=300.0, silence_threshold=0.03, resume_threshold=None, monitor_system_output=True, device_id=None, parent=None):
        super().__init__(parent)
        self.silence_duration_s = float(silence_duration_s)
        self.threshold = float(silence_threshold)
        try:
            self.resume_threshold = float(resume_threshold) if (resume_threshold is not None) else float(silence_threshold) * 1.5
        except Exception:
            self.resume_threshold = float(silence_threshold) * 1.5
        self.monitor_system_output = bool(monitor_system_output)
        self.device_id = device_id
        self._is_running = True
        self._last_state_is_silent = False
        self._silence_counter = 0.0
        self._restart_requested = False
        self._ema_rms = 0.0
        self._last_rms_emit = 0.0
        self.last_error = None
        try:
            import sounddevice as sd
            self._sd = sd
            logger.debug("✓ sounddevice available for system audio monitoring")
        except Exception as e:
            self._sd = None
            self.last_error = f"Failed to import the 'sounddevice' library.\n\nTo enable this feature, please run:\npip install sounddevice"
            logger.error(self.last_error)

    def stop(self):
        self._is_running = False

    def update_settings(self, silence_duration_s=None, silence_threshold=None, resume_threshold=None, monitor_system_output=None, device_id=None):
        """Update monitoring settings and restart if needed"""
        if silence_duration_s is not None:
            self.silence_duration_s = float(silence_duration_s)
        if silence_threshold is not None:
            self.threshold = float(silence_threshold)
        if resume_threshold is not None:
            try:
                self.resume_threshold = float(resume_threshold)
            except Exception:
                pass
        restart = False
        if monitor_system_output is not None:
            old_mode = self.monitor_system_output
            self.monitor_system_output = bool(monitor_system_output)
            restart = restart or (old_mode != self.monitor_system_output)
        if device_id is not None and device_id != self.device_id:
            self.device_id = device_id
            restart = True
        if restart and self._is_running:
            self._restart_monitor()

    def _restart_monitor(self):
        """Internal method to restart monitoring with new settings"""
        # Signal the run loop to break the current stream and reopen with new settings
        self._restart_requested = True

    def run(self):
        if not self._sd:
            return
        try:
            import numpy as np
        except Exception:
            logger.error("numpy unavailable, disabling system audio monitoring")
            return

        def _host_name_for(dev_dict):
            try:
                idx = dev_dict.get('hostapi')
                return self._sd.query_hostapis()[idx]['name']
            except Exception:
                return dev_dict.get('hostapi_name', '') or ''

        while self._is_running:
            try:
                monitor_device = self.device_id if (isinstance(self.device_id, int) and self.device_id >= 0) else None
                logger.debug(f"[AudioMonitor] Starting stream setup. Preferred device ID: {monitor_device}")

                if self.monitor_system_output and hasattr(self._sd, 'query_devices'):
                    try:
                        import platform
                        if platform.system() == 'Windows':
                            devices = self._sd.query_devices()
                            for i, dev in enumerate(devices):
                                name = (dev.get('name') or '').lower()
                                host = _host_name_for(dev)
                                if ('loopback' in name or 'stereo mix' in name or 'what u hear' in name) and host.startswith('Windows WASAPI'):
                                    monitor_device = i
                                    print(f"✓ Using WASAPI loopback device: [{i}] {dev.get('name')} ({host})")
                                    break
                            if monitor_device is None:
                                try:
                                    di = self._sd.default.device
                                    if isinstance(di, (list, tuple)) and len(di) >= 2 and di[1] is not None:
                                        monitor_device = di[1]
                                        info = self._sd.query_devices(monitor_device, 'output')
                                        print(f"✓ Using default output for loopback: [{monitor_device}] {info.get('name')} ({_host_name_for(info)})")
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"WASAPI loopback detection failed: {e}")
                
                logger.debug(f"[AudioMonitor] Attempting to use device ID: {monitor_device}")

                try:
                    samplerate = self._sd.query_devices(monitor_device, 'input')['default_samplerate']
                    channels = 1
                    extra_settings = None
                except Exception:
                    samplerate = 44100; channels = 1; extra_settings = None

                def audio_callback(indata, frames, time_info, status):
                    if status:
                        logger.debug(f"[AudioMonitor] Callback status: {status}")
                        if status.input_overflow:
                            logger.debug("[AudioMonitor] Input overflow occurred. Data may be lost.")

                    if frames > 0 and indata.size > 0:
                        try:
                            rms = float(np.sqrt(np.mean(indata**2)))
                            logger.debug(f"[AudioMonitor] Calculated RMS: {rms:.4f}")
                        except Exception as e:
                            logger.error(f"[AudioMonitor] Error calculating RMS: {e}")
                            rms = 0.0
                    else:
                        logger.warning("[AudioMonitor] Empty indata buffer received.")
                        rms = 0.0

                    try:
                        self._ema_rms = 0.2 * rms + 0.8 * float(getattr(self, '_ema_rms', 0.0))
                    except Exception:
                        self._ema_rms = rms

                    if time.time() - self._last_rms_emit > 0.1:
                        self.rmsUpdated.emit(self._ema_rms)
                        # logger.info(f"[AudioMonitor] Emitting RMS: {self._ema_rms:.4f}")
                        self._last_rms_emit = time.time()

                    effective_threshold = self.resume_threshold if self._last_state_is_silent else self.threshold
                    is_currently_silent = self._ema_rms < effective_threshold
                    
                    if is_currently_silent:
                        self._silence_counter += float(len(indata)) / float(samplerate)
                        if self._silence_counter >= self.silence_duration_s:
                            self.silenceDetected.emit()
                            self._silence_counter = 0.0
                    else:
                        self._silence_counter = 0.0
                    
                    if is_currently_silent != self._last_state_is_silent:
                        self.audioStateChanged.emit(is_currently_silent)
                        self._last_state_is_silent = is_currently_silent
                
                logger.debug(f"[AudioMonitor] Opening audio InputStream with samplerate={samplerate}, channels={channels}")
                with self._sd.InputStream(
                    device=monitor_device, samplerate=samplerate, channels=channels,
                    callback=audio_callback, blocksize=1024, extra_settings=extra_settings
                ):
                    logger.info("[AudioMonitor] Stream opened successfully. Monitoring...")
                    while self._is_running:
                        if getattr(self, '_restart_requested', False):
                            break
                        self.msleep(100)

                if getattr(self, '_restart_requested', False):
                    self._restart_requested = False
                    logger.info("[AudioMonitor] Restarting stream with new settings.")
                    continue

            except Exception as e:
                logger.error(f"[AudioMonitor] Stream error: {e}", exc_info=True)
                self.audioStateChanged.emit(False)
                self.msleep(3000)


class AFKMonitor(QThread):
    userIsAFK = Signal()

    def __init__(self, timeout_minutes=15, parent=None):
        super().__init__(parent)
        self.timeout_seconds = int(timeout_minutes) * 60
        self.last_input_time = time.time()
        self._is_running = True

    def update_activity(self, *args):
        self.last_input_time = time.time()

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            from pynput import mouse, keyboard
        except Exception as e:
            print(f"✗ pynput unavailable for AFK monitor: {e}")
            return
        mouse_listener = mouse.Listener(on_move=self.update_activity, on_click=self.update_activity, on_scroll=self.update_activity)
        keyboard_listener = keyboard.Listener(on_press=self.update_activity)
        mouse_listener.start(); keyboard_listener.start()
        try:
            while self._is_running:
                if time.time() - self.last_input_time > self.timeout_seconds:
                    self.userIsAFK.emit()
                    self.last_input_time = time.time()
                self.msleep(2000)
        finally:
            try:
                mouse_listener.stop(); keyboard_listener.stop()
            except Exception:
                pass


# --- Thumbnail fetcher ---
class ThumbnailFetcher(QThread):
    thumbnailReady = Signal(QPixmap)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url

    def run(self):
        if not HAVE_REQUESTS or not self.url:
            return
        try:
            r = requests.get(self.url, timeout=6)
            if r.status_code == 200:
                pm = QPixmap(); pm.loadFromData(r.content)
                if not pm.isNull():
                    self.thumbnailReady.emit(pm)
        except Exception as e:
            print(f"Thumbnail fetch error: {e}")

class PlaylistLoaderThread(QThread):
    itemsReady = Signal(list)
    error = Signal(str)

    def __init__(self, url: str, kind: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.kind = kind  # 'youtube' or 'bilibili' or 'local'

    def run(self):
        try:
            import yt_dlp
        except Exception as e:
            self.error.emit(f"yt-dlp not available: {e}")
            return
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'socket_timeout': 60,
            'retries': 3,
            'playliststart': 1,
            'playlistend': 10000,
        }
        if self.kind == 'bilibili':
            ydl_opts['cookiefile'] = str(COOKIES_BILI)
        try:
            import urllib.parse as up
            target_url = self.url
            if self.kind == 'youtube' and ('list=' in self.url):
                try:
                    u = up.urlparse(self.url)
                    qs = up.parse_qs(u.query)
                    lid = (qs.get('list') or [''])[0]
                    if lid:
                        target_url = f"https://www.youtube.com/playlist?list={lid}"
                except Exception:
                    pass
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(target_url, download=False)
        except Exception as e:
            self.error.emit(f"Failed to load playlist: {e}")
            return
        try:
            if info is None:
                self.itemsReady.emit([]); return
            # If this is a playlist with 'entries'
            if isinstance(info, dict) and info.get('entries'):
                playlist_title = info.get('title') or self.url
                entries = list(info.get('entries') or [])
                chunk = []
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    idv = entry.get('id') or ''
                    u = entry.get('webpage_url') or entry.get('url') or idv
                    if not u:
                        continue
                    # Normalize to full URL when extractor returns IDs only
                    if self.kind == 'bilibili' and not (u.startswith('http://') or u.startswith('https://')):
                        u = f"https://www.bilibili.com/video/{idv or u}"
                    if self.kind == 'youtube' and not (u.startswith('http://') or u.startswith('https://')):
                        u = f"https://www.youtube.com/watch?v={idv or u}"
                    title = entry.get('title') or u
                    chunk.append({'title': title, 'url': u, 'type': self.kind, 'playlist': playlist_title, 'playlist_key': info.get('id') or self.url})
                    if len(chunk) >= 25:
                        self.itemsReady.emit(chunk); chunk = []
                if chunk:
                    self.itemsReady.emit(chunk)
            else:
                # Single video fallback
                self.itemsReady.emit([{'title': info.get('title') or self.url, 'url': self.url, 'type': self.kind}])
        except Exception as e:
            self.error.emit(str(e)); return

class YtdlManager(QThread):
    """A persistent background thread to manage and reuse expensive yt-dlp instances."""
    titleResolved = Signal(str, str)  # url, title
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue = queue.Queue()
        self._should_stop = False
        self.ydl_instances = {}  # To store one ydl instance per configuration

    def resolve(self, url: str, kind: str):
        """Public method for the main thread to request a title resolution."""
        if url and kind:
            self._queue.put({'url': url, 'kind': kind})

    def stop(self):
        """Gracefully stop the background thread."""
        self._should_stop = True
        self._queue.put(None)  # Sentinel value to unblock the queue.get()

    def run(self):
        logger.debug("[YtdlManager] Background thread started.")
        import yt_dlp

        while not self._should_stop:
            job = self._queue.get()
            if job is None:
                break # Exit loop if sentinel is received

            url = job['url']
            kind = job['kind']

            try:
                # Lazy-initialize a yt-dlp instance for this 'kind' if it doesn't exist
                if kind not in self.ydl_instances:
                    logger.info(f"[YtdlManager] Creating new yt-dlp instance for kind: {kind}")
                    opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'skip_download': True,
                        'socket_timeout': 10,
                        'retries': 2,
                    }
                    if kind == 'bilibili':
                        opts['cookiefile'] = str(COOKIES_BILI)
                    
                    # This is the expensive call that will now only happen once per kind.
                    self.ydl_instances[kind] = yt_dlp.YoutubeDL(opts)

                # Use the appropriate, persistent instance
                ydl = self.ydl_instances[kind]
                info = ydl.extract_info(url, download=False)
                
                title = info.get('title') if isinstance(info, dict) else None
                if title and title != url:
                    self.titleResolved.emit(url, title)

            except Exception as e:
                logger.warning(f"[YtdlManager] Failed to resolve title for {url}: {e}")
                # Optionally emit an error signal
                # self.error.emit(str(e))
        
        logger.info("[YtdlManager] Background thread finished.")

class DurationFetcher(QThread):
    progressUpdated = Signal(int, int)  # current, total
    durationReady = Signal(int, int)    # index, duration
    
    def __init__(self, items_to_fetch, parent=None):
        super().__init__(parent)
        self.items_to_fetch = items_to_fetch  # List of (index, item) tuples
        self._should_stop = False
    
    def stop(self):
        self._should_stop = True
    
    def run(self):
        import yt_dlp
        
        for i, (playlist_index, item) in enumerate(self.items_to_fetch):
            if self._should_stop:
                break
                
            try:
                opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'extract_flat': False,
                }
                
                if item.get('type') == 'bilibili':
                    opts['cookiefile'] = str(COOKIES_BILI)
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(item.get('url'), download=False)
                    duration = int(info.get('duration', 0)) if info else 0
                    self.durationReady.emit(playlist_index, duration)
                    
            except Exception as e:
                print(f"Duration fetch error for {item.get('url')}: {e}")
                self.durationReady.emit(playlist_index, 0)
            
            self.progressUpdated.emit(i + 1, len(self.items_to_fetch))       

# --- Stats heatmap widget ---
class StatsHeatmapWidget(QWidget):
    daySelected = Signal(object)  # 'YYYY-MM-DD' or None

    def __init__(self, daily_map: dict, theme: str = 'dark', parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._theme = theme or 'dark'
        import datetime as dt
        self._dt = dt
        self._today = dt.date.today()
        # start one year back aligned to Sunday
        one_year_ago = self._today.replace(year=self._today.year - 1)
        # Align to previous Sunday (GitHub-style weeks start on Sunday)
        offset = (one_year_ago.weekday() + 1) % 7  # weekday(): Mon=0..Sun=6
        self._start = one_year_ago - dt.timedelta(days=offset)
        # Parse daily seconds
        self._daily = {}
        for k, v in (daily_map or {}).items():
            try:
                y, m, d = [int(x) for x in k.split('-')]
                self._daily[self._dt.date(y, m, d)] = float(v or 0)
            except Exception:
                continue
        self._selected = None
        self._compute_levels()
        self._cell = 12
        self._gap = 2
        self._top = 24
        self._left = 36
        self.setMinimumSize(self.sizeHint())

    def sizeHint(self):
        weeks = self._weeks_count()
        width = self._left + weeks * (self._cell + self._gap)
        height = self._top + 7 * (self._cell + self._gap)
        return QSize(width, height)

    def _weeks_count(self):
        delta = self._today - self._start
        return max(1, (delta.days // 7) + 1)

    def _compute_levels(self):
        vals = [v for v in self._daily.values() if v > 0]
        self._vmax = max(vals) if vals else 0.0
        # Level thresholds at ~0, 10%, 30%, 60%, 100%
        self._thresholds = [0,
                            0.10 * self._vmax,
                            0.30 * self._vmax,
                            0.60 * self._vmax,
                            1.00 * self._vmax]

    def _level(self, v: float) -> int:
        if v <= 0:
            return 0
        for i in range(1, 5):
            if v <= self._thresholds[i]:
                return i
        return 4

    def _palette(self):
        if self._theme == 'vinyl':
            # warm light scale
            return [QColor(224, 217, 200), QColor(255, 227, 190), QColor(246, 196, 148), QColor(235, 150, 95), QColor(206, 90, 52)]
        # dark scale similar to GitHub greens
        return [QColor(32, 32, 32), QColor(40, 66, 52), QColor(48, 98, 72), QColor(64, 135, 98), QColor(88, 171, 126)]

    def _date_at(self, x: int, y: int):
        col = (x - self._left) // (self._cell + self._gap)
        row = (y - self._top) // (self._cell + self._gap)
        if col < 0 or row < 0 or row > 6:
            return None
        dt = self._start + self._dt.timedelta(days=int(col) * 7 + int(row))
        if dt > self._today:
            return None
        return dt

    def mouseMoveEvent(self, e):
        try:
            x, y = int(e.position().x()), int(e.position().y())
            gp = e.globalPosition().toPoint()
        except AttributeError:
            x, y = e.x(), e.y()
            gp = e.globalPos()
        dt = self._date_at(x, y)
        if not dt:
            QToolTip.hideText(); return
        v = self._daily.get(dt, 0)
        QToolTip.showText(gp, f"{dt.isoformat()} — {human_duration(v)}", self)

    def mousePressEvent(self, e):
        try:
            x, y = int(e.position().x()), int(e.position().y())
        except AttributeError:
            x, y = e.x(), e.y()
        dt = self._date_at(x, y)
        if dt is None:
            self._selected = None
            self.daySelected.emit(None)
        else:
            if self._selected == dt:
                self._selected = None
                self.daySelected.emit(None)
            else:
                self._selected = dt
                self.daySelected.emit(dt.isoformat())
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        pal = self._palette()
        # Month labels
        p.setPen(QColor(180, 180, 180) if self._theme != 'vinyl' else QColor(90, 70, 60))
        p.setFont(QFont(p.font().family(), 8))
        self._draw_month_labels(p)
        # Cells
        for w in range(self._weeks_count()):
            for r in range(7):
                dt = self._start + self._dt.timedelta(days=w * 7 + r)
                if dt > self._today:
                    continue
                v = self._daily.get(dt, 0)
                lvl = self._level(v)
                rect_x = self._left + w * (self._cell + self._gap)
                rect_y = self._top + r * (self._cell + self._gap)
                p.fillRect(rect_x, rect_y, self._cell, self._cell, QBrush(pal[lvl]))
                # Selection outline
                if self._selected == dt:
                    pen = QPen(QColor(255, 255, 255) if self._theme != 'vinyl' else QColor(60, 40, 30))
                    pen.setWidth(2)
                    p.setPen(pen)
                    p.drawRect(rect_x, rect_y, self._cell, self._cell)
        p.end()

    def _draw_month_labels(self, p: QPainter):
        weeks = self._weeks_count()
        seen = set()
        for w in range(weeks):
            dt = self._start + self._dt.timedelta(days=w * 7)
            if dt.month in seen or dt > self._today:
                continue
            seen.add(dt.month)
            label = dt.strftime('%b')
            x = self._left + w * (self._cell + self._gap)
            p.drawText(x, 12, label)

# --- Custom slider with hover effects ---
class HoverSlider(QSlider):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)
        self._hover_scale = 1.0

        # Animation object
        self._animation = QPropertyAnimation(self, b"hoverScale")
        self._animation.setDuration(150)  # match transitions.html
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

    def enterEvent(self, event):
        super().enterEvent(event)
        self._animation.stop()
        self._animation.setStartValue(self._hover_scale)
        self._animation.setEndValue(1.2)  # 20% bigger
        self._animation.start()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._animation.stop()
        self._animation.setStartValue(self._hover_scale)
        self._animation.setEndValue(1.0)
        self._animation.start()

    def getHoverScale(self):
        return self._hover_scale

    def setHoverScale(self, value):
        self._hover_scale = value
        self.update()

    hoverScale = Property(float, getHoverScale, setHoverScale)

    def paintEvent(self, event):
        # Draw default
        super().paintEvent(event)

        # Then overlay our scaled thumb
        from PySide6.QtWidgets import QStyleOptionSlider
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        opt = QStyleOptionSlider()
        self.initStyleOption(opt)

        handle_rect = self.style().subControlRect(
            QStyle.CC_Slider, opt, QStyle.SC_SliderHandle, self
        )

        # Scale outwards
        scale_offset = (self._hover_scale - 1.0) * (handle_rect.width() / 2)
        scaled_rect = handle_rect.adjusted(
            -scale_offset, -scale_offset, scale_offset, scale_offset
        )

        # Find the main window to get theme
        main_window = None
        widget = self
        while widget:
            if hasattr(widget, 'theme'):
                main_window = widget
                break
            widget = widget.parent()
        
        # Use theme-appropriate color
        if main_window and getattr(main_window, 'theme', 'dark') == 'dark':
            handle_color = QColor(208, 208, 208)  # #d0d0d0 - off-white grey for dark theme
        else:
            handle_color = QColor(74, 44, 42)  # #4a2c2a - brown for vinyl theme
        
        painter.setBrush(QBrush(handle_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(scaled_rect)

class ClickableSlider(HoverSlider):
    # Custom signal to indicate a seek was requested by a direct click
    seekOnClick = Signal(int)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def enterEvent(self, event):
        super().enterEvent(event)
        QToolTip.showText(QCursor.pos(), f"Volume: {self.value()}%", self)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        QToolTip.showText(QCursor.pos(), f"Volume: {self.value()}%", self)

    def mousePressEvent(self, event):
        from PySide6.QtWidgets import QStyle, QStyleOptionSlider
        if event.button() == Qt.LeftButton:
            opt = QStyleOptionSlider()
            self.initStyleOption(opt)
            
            # Get the rectangle for the slider's groove (the track)
            groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
            
            # Determine the correct position and span based on orientation
            if self.orientation() == Qt.Horizontal:
                slider_pos = event.position().x() - groove_rect.x()
                slider_span = groove_rect.width()
            else:  # Vertical
                slider_pos = event.position().y() - groove_rect.y()
                slider_span = groove_rect.height()

            # Calculate the value corresponding to the click position
            new_val = QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), slider_pos, slider_span)

            if self.sliderPosition() != new_val:
                self.setValue(new_val)
                # Emit our custom signal for the progress bar to connect to
                self.seekOnClick.emit(new_val)

        # Call the superclass method to ensure normal dragging still works
        super().mousePressEvent(event)

class ProgressSlider(HoverSlider):
    seekOnClick = Signal(int)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def _value_from_pos(self, event_pos):
        """Helper to calculate slider value from a mouse position."""
        from PySide6.QtWidgets import QStyle, QStyleOptionSlider
        opt = QStyleOptionSlider()
        self.initStyleOption(opt)
        groove_rect = self.style().subControlRect(QStyle.CC_Slider, opt, QStyle.SC_SliderGroove, self)
        
        if self.orientation() == Qt.Horizontal:
            slider_pos = event_pos.x() - groove_rect.x()
            slider_span = groove_rect.width()
        else:
            slider_pos = event_pos.y() - groove_rect.y()
            slider_span = groove_rect.height()

        if slider_span <= 0: return 0
        return QStyle.sliderValueFromPosition(self.minimum(), self.maximum(), slider_pos, slider_span, opt.upsideDown)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        hover_val = self._value_from_pos(event.position())
        QToolTip.showText(QCursor.pos(), format_time(hover_val), self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            new_val = self._value_from_pos(event.position())
            if self.sliderPosition() != new_val:
                self.setValue(new_val)
                self.seekOnClick.emit(new_val)
        super().mousePressEvent(event)

# --- Playlist tree with drag-and-drop reorder ---
class ClickableLabel(QLabel):
    clicked = Signal()
    def mousePressEvent(self, event):
        # print(f"[HEADER DEBUG] ClickableLabel mousePressEvent: button={event.button()}, Qt.LeftButton={Qt.LeftButton}, Qt.RightButton={Qt.RightButton}")
        try:
            # Only emit clicked signal for left clicks
            if event.button() == Qt.LeftButton:
                pass  
                # self.clicked.emit()
                # print(f"[HEADER DEBUG] Left click - emitted clicked signal")
            elif event.button() == Qt.RightButton:
                pass  
                # print(f"[HEADER DEBUG] Right click - passing through to context menu")
        except Exception as e:
             # print(f"[HEADER DEBUG] Exception in mousePressEvent: {e}")
             pass
        super().mousePressEvent(event)

class PlaylistTree(QTreeWidget):
    def __init__(self, player):
        super().__init__()
        self.player = player
        self.setHeaderHidden(True)
        self.setObjectName('playlistTree')
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

    def dropEvent(self, event):
            # --- KEPT FROM ORIGINAL: Confirmation logic for mass moves ---
            selected_items = self.selectedItems()
            items_being_moved = 0
            
            for item in selected_items:
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple):
                    if data[0] == 'current':
                        items_being_moved += 1
                    elif data[0] == 'group':
                        items_being_moved += item.childCount()

            MOVE_CONFIRMATION_THRESHOLD = 10 
            if items_being_moved > MOVE_CONFIRMATION_THRESHOLD:
                reply = QMessageBox.question(
                    self.player, "Confirm Move",
                    f"You are about to move {items_being_moved} items.\n\nThis action can be undone with Ctrl+Z.\n\nProceed?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply == QMessageBox.No:
                    event.ignore()
                    return

            # --- Store state for undo and for finding the item later ---
            old_playlist = list(self.player.playlist)
            was_playing = self.player._is_playing()
            old_current_index = self.player.current_index
            
            # --- NEW LOGIC: Find the unique URL of the item that is currently playing ---
            playing_item_url = None
            if was_playing and 0 <= old_current_index < len(old_playlist):
                playing_item_url = old_playlist[old_current_index].get('url')

            # --- KEPT FROM ORIGINAL: Save expansion state before reordering ---
            expansion_state = self.player._get_tree_expansion_state()

            # Perform the actual drop/reorder in the UI
            super().dropEvent(event)
            
            try:
                # Rebuild our internal playlist to match the new UI order.
                new_playlist = []
                iterator = QTreeWidgetItemIterator(self)
                while iterator.value():
                    item = iterator.value()
                    data = item.data(0, Qt.UserRole)
                    if isinstance(data, tuple) and data[0] == 'current':
                        new_playlist.append(data[2])
                    iterator += 1

                if len(new_playlist) == len(self.player.playlist) and new_playlist != old_playlist:
                    self.player.playlist = new_playlist
                    
                    # --- NEW LOGIC: Find the NEW index of the playing item and update it ---
                    if playing_item_url:
                        new_current_index = -1
                        for i, item_data in enumerate(new_playlist):
                            if item_data.get('url') == playing_item_url:
                                new_current_index = i
                                break
                        if new_current_index != -1:
                            self.player.current_index = new_current_index

                    self.player._save_current_playlist()

                    # Add the change to the undo stack
                    undo_data = { 'playlist': old_playlist, 'was_playing': was_playing, 'current_index': old_current_index }
                    self.player._add_undo_operation('move_items', undo_data)
                    self.player.status.showMessage("Playlist reordered (Ctrl+Z to undo)", 3000)

                    # --- KEPT FROM ORIGINAL: Refresh the widget to apply expansion state ---
                    self.player._refresh_playlist_widget(expansion_state=expansion_state)
                    
                    # --- HIGHLIGHT FIX: Explicitly re-apply highlight after the refresh ---
                    if was_playing:
                        self.player._highlight_current_row()
                    
                    self.player._update_up_next()

            except Exception as e:
                logger.error(f"Drag-and-drop reorder error: {e}")

class ScrollingTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scroll_timers = {}
        self._scroll_positions = {}
        self._original_texts = {}
        
    def _start_scrolling(self, item):
            """Start scrolling for an item if text is too wide"""
            if not item or item in self._scroll_timers:
                return

            original_text = item.text(0)
            self._original_texts[item] = original_text

            # --- THIS IS THE FIX ---
            # Use the widget's own fontMetrics and columnWidth
            font_metrics = self.fontMetrics()
            text_width = font_metrics.horizontalAdvance(original_text)
            available_width = self.columnWidth(0) - 30  # Adjust for padding/icons

            if text_width <= available_width:
                return  # Text fits, no need to scroll

            # --- Scrolling logic continues below ---
            
            self._scroll_positions[item] = 0
            timer = QTimer(self)
            
            def scroll_step():
                if item not in self._scroll_positions:
                    timer.stop()
                    return

                pos = self._scroll_positions[item]
                
                # Use the stored original text for animation
                text_to_scroll = self._original_texts.get(item, "")
                if not text_to_scroll:
                    timer.stop()
                    return

                scrolled = text_to_scroll[pos:] + "   " + text_to_scroll[:pos]
                item.setText(0, scrolled)
                
                self._scroll_positions[item] = (pos + 1) % (len(text_to_scroll) + 3)

            timer.timeout.connect(scroll_step)
            timer.start(150)
            self._scroll_timers[item] = timer
        
    def _stop_scrolling(self, item):
        """Stop scrolling and restore original text"""
        if not item:
            return
            
        # Stop timer
        if item in self._scroll_timers:
            self._scroll_timers[item].stop()
            del self._scroll_timers[item]
            
        # Restore original text
        if item in self._original_texts:
            item.setText(0, self._original_texts[item])
            del self._original_texts[item]
            
        # Clean up position tracking
        if item in self._scroll_positions:
            del self._scroll_positions[item]
    
    def enterEvent(self, event):
        """Handle mouse entering the widget"""
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leaving the widget - stop all scrolling"""
        super().leaveEvent(event)
        # Stop all scrolling when mouse leaves the entire widget
        for item in list(self._scroll_timers.keys()):
            self._stop_scrolling(item)
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement to detect item hover"""
        super().mouseMoveEvent(event)
        
        # Get item under mouse
        current_item = self.itemAt(event.pos())
        
        # Stop scrolling for all items except the hovered one
        for item in list(self._scroll_timers.keys()):
            if item != current_item:
                self._stop_scrolling(item)
        
        # Start scrolling for the hovered item
        if current_item and current_item.parent() is None:  # Only for top-level items
            self._start_scrolling(current_item)

# --- Player ---
class MediaPlayer(QMainWindow):
    requestTimerSignal = Signal(int, object)
    statusMessageSignal = Signal(str, int)
    
    def __init__(self):
        super().__init__()

        self._playlist_manager = None

        # Create 4 parallel workers for faster title resolution
        self.ytdl_workers = []
        for i in range(4):
            worker = YtdlManager(self)
            worker.titleResolved.connect(self._on_title_resolved)
            worker.error.connect(lambda e: print(f"Title resolution error: {e}"))
            worker.start()
            self.ytdl_workers.append(worker)
        self._worker_index = 0


        self.setWindowTitle("Silence Suzuka Player")
        self.setGeometry(100, 100, 1180, 760)

        # --- 1. Define All State Variables First ---
        self._was_maximized = False
        self.playlist = []
        self.current_index = -1
        self.playback_positions = {}
        self.saved_playlists = {}
        self.session_start_time = None
        # ... (and so on for all your state variables)
        self.log_level = 'INFO'
        self.theme = 'vinyl'
        self.show_up_next = True
        self.restore_session = True

        # This list continues from your original file, ensure they are all here
        self.playback_positions = {}
        self.saved_playlists = {}
        self.session_start_time = None
        self.last_position_update = 0
        self.auto_play_enabled = True
        self.afk_timeout_minutes = 15
        self.silence_duration_s = 300.0
        self.show_thumbnails = False
        self.minimize_to_tray = False
        self.show_today_badge = True
        self.group_singles = True
        self.shuffle_mode = False
        self.repeat_mode = False
        self.completed_percent = 95
        self.skip_completed = False
        self.unwatched_only = False
        self.monitor_system_output = True
        self.silence_threshold = 0.03
        self.resume_threshold = 0.045
        self._last_system_is_silent = True
        self.monitor_device_id = -1
        self._user_scrubbing = False
        self.completed_urls = set()
        self._title_workers = []
        self._last_resume_save = time.time()
        self._last_play_pos_ms = 0
        self._last_saved_pos_ms = {}
        self._resume_target_ms = 0
        self._resume_enforce_until = 0.0
        self._force_play_ignore_completed = False
        self.play_scope = None
        self._last_clipboard_offer = ""

        # --- 2. Initialize Timers, Fonts, and Icons ---
        self.silence_timer = QTimer(self)
        self.silence_timer.timeout.connect(self._update_silence_tooltip)
        self.silence_timer.start(1000)
        self._init_fonts()

        self.anim_press = QPropertyAnimation()
        self.anim_release = QPropertyAnimation()

        self._undo_stack = []  # Stack of undo operations
        self._max_undo_operations = 10  # Limit undo history

        # This definition now correctly happens BEFORE the UI is built
        self.icon_size = QSize(22, 22)
        try:
            play_path = APP_DIR / 'icons/play.svg'
            pause_path = APP_DIR / 'icons/pause.svg'
            prev_path = APP_DIR / 'icons/previous.svg'
            next_path = APP_DIR / 'icons/next.svg'
            shuffle_path = APP_DIR / 'icons/shuffle.svg'
            repeat_path = APP_DIR / 'icons/repeat.svg'
            icon_px = QSize(50, 50)
            self._play_icon_normal = load_svg_icon(str(play_path), icon_px) if play_path.exists() else QIcon()
            self._pause_icon_normal = load_svg_icon(str(pause_path), icon_px) if pause_path.exists() else QIcon()
            self.prev_icon_vinyl = QIcon(str(prev_path)) if prev_path.exists() else "⏮"
            self.next_icon_vinyl = QIcon(str(next_path)) if next_path.exists() else "⏭"
            self.shuffle_icon_vinyl = QIcon(str(shuffle_path)) if shuffle_path.exists() else "🔀"
            self.repeat_icon_vinyl = QIcon(str(repeat_path)) if repeat_path.exists() else "🔁"
            self.prev_icon_dark = QIcon(_render_svg_tinted(str(prev_path), self.icon_size, "#FFFFFF")) if prev_path.exists() else "⏮"
            self.next_icon_dark = QIcon(_render_svg_tinted(str(next_path), self.icon_size, "#FFFFFF")) if next_path.exists() else "⏭"
            self.shuffle_icon_dark = QIcon(_render_svg_tinted(str(shuffle_path), self.icon_size, "#FFFFFF")) if shuffle_path.exists() else "🔀"
            self.repeat_icon_dark = QIcon(_render_svg_tinted(str(repeat_path), self.icon_size, "#FFFFFF")) if repeat_path.exists() else "🔁"
            shuffle_on_path = APP_DIR / 'icons/shuffle-on.svg'
            repeat_on_path = APP_DIR / 'icons/repeat-on.svg'
            accent_color_on = "#e76f51"
            self.shuffle_on_icon_vinyl = QIcon(str(shuffle_on_path)) if shuffle_on_path.exists() else "🔀"
            self.repeat_on_icon_vinyl = QIcon(str(repeat_on_path)) if repeat_on_path.exists() else "🔁"
            self.shuffle_on_icon_dark = QIcon(_render_svg_tinted(str(shuffle_on_path), self.icon_size, accent_color_on)) if shuffle_on_path.exists() else "🔀"
            self.repeat_on_icon_dark = QIcon(_render_svg_tinted(str(repeat_on_path), self.icon_size, accent_color_on)) if repeat_on_path.exists() else "🔁"
            self.tray_icon_play = self._play_icon_normal
            self.tray_icon_pause = self._pause_icon_normal
            if play_path.exists():
                self.tray_icon_play = QIcon(_render_svg_tinted(play_path, QSize(32, 32), "#FFFFFF"))
            if pause_path.exists():
                self.tray_icon_pause = QIcon(_render_svg_tinted(pause_path, QSize(32, 32), "#FFFFFF"))
            self.volume_icon = QIcon(str(APP_DIR / 'icons/volume.svg'))
            mute_path = APP_DIR / 'icons/volume-mute.svg'
            self.volume_mute_icon = QIcon(str(mute_path)) if mute_path.exists() else "🔇"
            
            # --- FIX: Use emojis for both audio states ---
            self.icon_audio_active = "🔊"  # Sound is active
            self.icon_audio_silent = "🔇"  # System is silent
        except Exception as e:
            logger.error(f"Failed during icon creation: {e}")

        # --- 3. Connect Signals and Build the Rest of the App ---
        self.requestTimerSignal.connect(self._start_timer_from_main_thread)
        self.statusMessageSignal.connect(self._show_status_message)
        self._build_ui()

        # Override the playlist methods with enhanced versions
        def enhanced_save():
            if not self._playlist_manager:
                self._playlist_manager = EnhancedPlaylistManager(self, APP_DIR)
            return self._playlist_manager.save_current_playlist()
        
        def enhanced_load():
            if not self._playlist_manager:
                self._playlist_manager = EnhancedPlaylistManager(self, APP_DIR)
            return self._playlist_manager.load_playlist_dialog()

        # Override the methods
        self.save_playlist = enhanced_save
        self.load_playlist_dialog = enhanced_load

        self._setup_keyboard_shortcuts()
        self._init_mpv()
        self._load_files()

        # Apply chevron style after theme is loaded
        if hasattr(self, "playlist_tree"):
            if getattr(self, "theme", "dark") == "dark":
                self.playlist_tree.setStyle(LightChevronTreeStyle(color="#e0e0e0"))
            # Don't set any custom style for vinyl - let it use the native Qt style

        self._init_monitors()
        self._update_silence_indicator()
        self._init_tray()
        self.status.showMessage("Ready")

        self._undo_stack = []  # Stack of undo operations
        self._max_undo_operations = 10  # Limit undo history
        
        

    def _collapse_all_groups(self):
        """Collapses all top-level group items in the playlist tree."""
        try:
            self.playlist_tree.collapseAll()
            self.status.showMessage("All groups collapsed", 2000)
        except Exception as e:
            logger.error(f"Failed to collapse groups: {e}")

    def _expand_all_groups(self):
        """Expands all top-level group items in the playlist tree."""
        try:
            self.playlist_tree.expandAll()
            self.status.showMessage("All groups expanded", 2000)
        except Exception as e:
            logger.error(f"Failed to expand groups: {e}")    

    def _resolve_title_parallel(self, url, kind):
        """Distribute title resolution across multiple workers"""
        worker = self.ytdl_workers[self._worker_index]
        worker.resolve(url, kind)
        self._worker_index = (self._worker_index + 1) % len(self.ytdl_workers)            

    def _handle_paste(self):
        """Handle Ctrl+V paste for media URLs"""
        try:
            handled = self._maybe_offer_clipboard_url()
            
            if not handled:
                cb_text = QApplication.clipboard().text().strip()
                if cb_text:
                    self.status.showMessage("Not a media URL", 2000)
                else:
                    self.status.showMessage("Nothing to paste", 2000)
                    
        except Exception as e:
            self.status.showMessage(f"Paste failed: {e}", 3000)

    def dragEnterEvent(self, event):
        """Handle drag enter events"""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Handle drop events for files and URLs"""
        try:
            mime_data = event.mimeData()
            
            if mime_data.hasUrls():
                # Handle file drops
                for url in mime_data.urls():
                    file_path = url.toLocalFile()
                    if file_path:
                        # Local file
                        self.playlist.append({
                            'title': Path(file_path).name,
                            'url': file_path,
                            'type': 'local'
                        })
                    else:
                        # Web URL
                        self._add_url_to_playlist(url.toString())
                
            elif mime_data.hasText():
                # Handle text drops (URLs copied as text)
                text = mime_data.text().strip()
                if text.startswith(('http://', 'https://')):
                    self._add_url_to_playlist(text)
            
            # Refresh UI after adding items
            self._save_current_playlist()
            # Save expansion state before refresh
            expansion_state = self._get_tree_expansion_state()
            self._refresh_playlist_widget(expansion_state=expansion_state)
            event.acceptProposedAction()
            
        except Exception as e:
            print(f"Drop event error: {e}")
            event.ignore()

    def _flash_button_color(self, button, color, duration=100):
        """Flash button with a color tint - safer version"""
        try:
            # Create a fresh effect each time instead of reusing
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor(color))
            effect.setStrength(0.7)  # More noticeable
            button.setGraphicsEffect(effect)
            
            # Remove effect after duration
            QTimer.singleShot(duration, lambda: (
                button.setGraphicsEffect(None) if button else None
            ))
            
        except Exception as e:
            pass # print(f"Flash button color error: {e}")

    def _show_library_header_context_menu(self, pos):
        """Show context menu for the library header"""
        # print(f"[HEADER DEBUG] *** LIBRARY HEADER CONTEXT MENU TRIGGERED at pos: {pos} ***")
        try:
            menu = QMenu(self)
            self._apply_menu_theme(menu)
            
            # print(f"[HEADER DEBUG] Menu created successfully")
            
            # Reset all playback positions
            reset_action = menu.addAction("🔄 Reset All Playback Positions")
            reset_action.triggered.connect(self._reset_all_playback_positions)
            
            # Optional: Add other useful actions
            menu.addSeparator()
            clear_completed_action = menu.addAction("✅ Mark All as Unwatched")
            clear_completed_action.triggered.connect(self._mark_all_unwatched)
            
            # print(f"[HEADER DEBUG] About to exec menu with {len(menu.actions())} actions")
            
            # Show the menu
            menu.exec(self.library_header_label.mapToGlobal(pos))
            
            # print(f"[HEADER DEBUG] Menu exec completed")
            
        except Exception as e:
            # print(f"[HEADER DEBUG] Exception: {e}")
            logger.error(f"Library header context menu error: {e}") 

    def _toggle_all_groups(self):
        """Toggle between expanding and collapsing all groups"""
        try:
            # Check if any groups are expanded
            any_expanded = False
            for i in range(self.playlist_tree.topLevelItemCount()):
                item = self.playlist_tree.topLevelItem(i)
                if item and item.isExpanded():
                    any_expanded = True
                    break
            
            if any_expanded:
                self._collapse_all_groups()
                self.status.showMessage("All groups collapsed", 2000)
            else:
                self._expand_all_groups()
                self.status.showMessage("All groups expanded", 2000)
                
        except Exception as e:
            logger.error(f"Failed to toggle groups: {e}")        

    def _reset_all_playback_positions(self):
        """Reset all playback positions for items in the current playlist"""
        try:
            if not self.playlist:
                self.status.showMessage("No items in playlist", 3000)
                return
            
            # Collect URLs from current playlist
            urls_in_playlist = []
            for item in self.playlist:
                url = item.get('url')
                if url:
                    urls_in_playlist.append(url)
            
            if not urls_in_playlist:
                self.status.showMessage("No URLs found in playlist", 3000)
                return
            
            # Show confirmation dialog with more prominent warning
            reply = QMessageBox.question(
                self, 
                "Reset All Playback Positions", 
                f"Reset playback positions for ALL {len(urls_in_playlist)} items in the library?\n\n"
                "⚠️  This will permanently clear all saved resume points.\n"
                "All videos will start from the beginning when played next.\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default to No for safety
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Clear positions for playlist URLs
            cleared_count = 0
            for url in urls_in_playlist:
                # Try both exact URL and canonical URL as keys
                keys_to_try = [url, self._canonical_url_key(url)]
                
                for key in keys_to_try:
                    if key and key in self.playback_positions:
                        del self.playback_positions[key]
                        cleared_count += 1
            
            # Save the updated positions
            if cleared_count > 0:
                self._save_positions()
                self.status.showMessage(f"Cleared {cleared_count} playback positions", 4000)
            else:
                self.status.showMessage("No playback positions found to clear", 3000)
                
        except Exception as e:
            logger.error(f"Reset all playback positions error: {e}")
            self.status.showMessage(f"Reset failed: {e}", 4000)

    def _mark_all_unwatched(self):
        """Mark all items in the current playlist as unwatched"""
        try:
            if not self.playlist:
                self.status.showMessage("No items in playlist", 3000)
                return
            
            urls_in_playlist = [item.get('url') for item in self.playlist if item.get('url')]
            
            if not urls_in_playlist:
                self.status.showMessage("No URLs found in playlist", 3000)
                return
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Mark All Unwatched", 
                f"Mark all {len(urls_in_playlist)} items in the playlist as unwatched?\n\n"
                "This will remove completion status for all items.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Clear completion status
            cleared_count = 0
            for url in urls_in_playlist:
                keys_to_try = [url, self._canonical_url_key(url)]
                
                for key in keys_to_try:
                    if key and key in self.completed_urls:
                        self.completed_urls.discard(key)
                        cleared_count += 1
            
            if cleared_count > 0:
                self._save_completed()
                self.status.showMessage(f"Marked {cleared_count} items as unwatched", 4000)
                # Refresh the playlist to update any visual indicators
                self._apply_filters_to_tree()
            else:
                self.status.showMessage("No completed items found", 3000)
                
        except Exception as e:
            logger.error(f"Mark all unwatched error: {e}")
            self.status.showMessage(f"Mark unwatched failed: {e}", 4000)      

    def _reset_selected_playback_positions(self, indices):
        """Reset playback positions for selected items with confirmation"""
        try:
            if not indices:
                return
                
            # Get URLs for selected indices
            urls_to_reset = []
            for idx in indices:
                if 0 <= idx < len(self.playlist):
                    url = self.playlist[idx].get('url')
                    if url:
                        urls_to_reset.append(url)
            
            if not urls_to_reset:
                self.status.showMessage("No URLs found in selection", 3000)
                return
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Reset Playback Positions",
                f"Reset playback positions for {len(urls_to_reset)} selected items?\n\n"
                "⚠️  This will clear all saved resume points for the selected videos.\n"
                "These videos will start from the beginning when played next.\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Reset positions for selected URLs
            cleared_count = 0
            for url in urls_to_reset:
                keys_to_try = [url, self._canonical_url_key(url)]
                for key in keys_to_try:
                    if key and key in self.playback_positions:
                        del self.playback_positions[key]
                        cleared_count += 1
            
            if cleared_count > 0:
                self._save_positions()
                self.status.showMessage(f"Cleared {cleared_count} playback positions for selected items", 4000)
            else:
                self.status.showMessage("No playback positions found for selected items", 3000)
                
        except Exception as e:
            logger.error(f"Reset selected playback positions error: {e}")
            self.status.showMessage(f"Reset positions failed: {e}", 4000)

    def _mark_selected_unwatched(self, indices):
        """Mark selected items as unwatched with confirmation"""
        try:
            if not indices:
                return
                
            # Get URLs for selected indices and count completed ones
            urls_to_mark = []
            completed_count = 0
            
            for idx in indices:
                if 0 <= idx < len(self.playlist):
                    url = self.playlist[idx].get('url')
                    if url:
                        urls_to_mark.append(url)
                        # Check if this URL is completed
                        keys_to_try = [url, self._canonical_url_key(url)]
                        for key in keys_to_try:
                            if key and key in self.completed_urls:
                                completed_count += 1
                                break
            
            if not urls_to_mark:
                self.status.showMessage("No URLs found in selection", 3000)
                return
            
            # Show appropriate message based on completion status
            if completed_count == 0:
                QMessageBox.information(
                    self,
                    "Mark as Unwatched",
                    f"All {len(urls_to_mark)} selected items are already unwatched.\n\nNo changes needed.",
                    QMessageBox.Ok
                )
                return
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Mark as Unwatched",
                f"Mark {len(urls_to_mark)} selected items as unwatched?\n\n"
                f"📊 {completed_count} items are currently completed\n"
                f"📊 {len(urls_to_mark) - completed_count} items are already unwatched\n\n"
                "⚠️  This will remove completion status for the selected items.\n"
                "These videos will appear as 'unwatched' regardless of previous progress.\n\n"
                "This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Mark selected URLs as unwatched
            cleared_count = 0
            for url in urls_to_mark:
                keys_to_try = [url, self._canonical_url_key(url)]
                for key in keys_to_try:
                    if key and key in self.completed_urls:
                        self.completed_urls.discard(key)
                        cleared_count += 1
            
            if cleared_count > 0:
                self._save_completed()
                self.status.showMessage(f"Marked {cleared_count} selected items as unwatched", 4000)
                self._apply_filters_to_tree()  # Refresh to update visual indicators
            else:
                self.status.showMessage("No completed items found in selection", 3000)
                
        except Exception as e:
            logger.error(f"Mark selected unwatched error: {e}")
            self.status.showMessage(f"Mark unwatched failed: {e}", 4000)        

    def _reset_group_playback_positions(self, group_key):
        """Reset playback positions for all items in a specific group"""
        # print(f"DEBUG: _reset_group_playback_positions called with key: {group_key}")
        try:
            indices = self._iter_indices_for_group(group_key)
            if not indices:
                self.status.showMessage(f"No items found in group", 3000)
                return
            
            # Collect URLs from group items
            group_urls = []
            for idx in indices:
                if 0 <= idx < len(self.playlist):
                    url = self.playlist[idx].get('url')
                    if url:
                        group_urls.append(url)
            
            if not group_urls:
                self.status.showMessage("No URLs found in group", 3000)
                return
            
            group_name = self._scope_title_from_key(group_key)
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Reset Group Playback Positions", 
                f"Reset playback positions for all {len(group_urls)} items in '{group_name}'?\n\n"
                "This will clear all saved resume points for this group.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default to No for safety
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Clear positions for group URLs
            cleared_count = 0
            for url in group_urls:
                # Try both exact URL and canonical URL as keys
                keys_to_try = [url, self._canonical_url_key(url)]
                
                for key in keys_to_try:
                    if key and key in self.playback_positions:
                        del self.playback_positions[key]
                        cleared_count += 1
            
            # Save the updated positions
            if cleared_count > 0:
                self._save_positions()
                self.status.showMessage(f"Cleared {cleared_count} playback positions in '{group_name}'", 4000)
            else:
                self.status.showMessage(f"No playback positions found in '{group_name}'", 3000)
                
        except Exception as e:
            logger.error(f"Reset group playback positions error: {e}")
            self.status.showMessage(f"Reset failed: {e}", 4000)

    def _mark_group_unwatched_enhanced(self, group_key):
        """Mark all items in a specific group as unwatched with confirmation"""
        # print(f"DEBUG: _mark_group_unwatched_enhanced called with key: {group_key}") 
        try:
            indices = self._iter_indices_for_group(group_key)
            if not indices:
                self.status.showMessage("No items found in group", 3000)
                return
            
            # Collect URLs from group items
            group_urls = []
            for idx in indices:
                if 0 <= idx < len(self.playlist):
                    url = self.playlist[idx].get('url')
                    if url:
                        group_urls.append(url)
            
            if not group_urls:
                self.status.showMessage("No URLs found in group", 3000)
                return
                
            group_name = self._scope_title_from_key(group_key)
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Mark Group as Unwatched", 
                f"Mark all {len(group_urls)} items in '{group_name}' as unwatched?\n\n"
                "This will remove completion status for all items in this group.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Clear completion status
            cleared_count = 0
            for url in group_urls:
                keys_to_try = [url, self._canonical_url_key(url)]
                
                for key in keys_to_try:
                    if key and key in self.completed_urls:
                        self.completed_urls.discard(key)
                        cleared_count += 1
            
            if cleared_count > 0:
                self._save_completed()
                self.status.showMessage(f"Marked {cleared_count} items as unwatched in '{group_name}'", 4000)
                # Refresh the playlist to update any visual indicators
                self._apply_filters_to_tree()
            else:
                self.status.showMessage(f"No completed items found in '{group_name}'", 3000)
                
        except Exception as e:
            logger.error(f"Mark group unwatched error: {e}")
            self.status.showMessage(f"Mark unwatched failed: {e}", 4000)

    def _show_loading(self, message="Loading..."):
        """Show loading indicator as centered overlay"""
        if not hasattr(self, '_loading_overlay'):
            # Create overlay widget
            self._loading_overlay = QWidget(self)
            self._loading_overlay.setObjectName('loadingOverlay')
            
            # Semi-transparent background
            self._loading_overlay.setStyleSheet("""
                #loadingOverlay {
                    background-color: rgba(0, 0, 0, 0.7);
                    border-radius: 8px;
                }
            """)
            
            # Layout for centering content
            overlay_layout = QVBoxLayout(self._loading_overlay)
            overlay_layout.setAlignment(Qt.AlignCenter)
            
            # Spinner
            self._loading_progress = QProgressBar()
            self._loading_progress.setRange(0, 0)  # Indeterminate
            self._loading_progress.setMaximumWidth(200)
            self._loading_progress.setTextVisible(False)
            
            # Loading text
            self._loading_label = QLabel(message)
            self._loading_label.setAlignment(Qt.AlignCenter)
            self._loading_label.setStyleSheet("color: white; font-size: 14px; margin: 10px;")
            
            overlay_layout.addWidget(self._loading_progress)
            overlay_layout.addWidget(self._loading_label)
            
            # Position overlay in center of main window
            self._loading_overlay.setFixedSize(250, 100)
        
        # Update message and show
        self._loading_label.setText(message)
        self._position_loading_overlay()
        self._loading_overlay.show()
        self._loading_overlay.raise_()

    def _hide_loading(self, final_message="", timeout=3000):
        """Hide loading overlay"""
        if hasattr(self, '_loading_overlay'):
            self._loading_overlay.hide()
        
        if final_message:
            self.status.showMessage(final_message, timeout)

    def _position_loading_overlay(self):
        """Position the loading overlay in the center of the main window"""
        if hasattr(self, '_loading_overlay'):
            # Get the geometry of the central widget
            central_rect = self.centralWidget().geometry()
            overlay_size = self._loading_overlay.size()
            
            # Calculate center position
            x = central_rect.center().x() - overlay_size.width() // 2
            y = central_rect.center().y() - overlay_size.height() // 2
            
            self._loading_overlay.move(x, y)        

    def _setup_up_next_scrolling(self):
        """Setup mouse tracking and scrolling for Up Next"""
        if not hasattr(self, 'up_next'):
            return
        
        # print("[DEBUG] Setting up Up Next scrolling")
        
        # Enable mouse tracking
        self.up_next.setMouseTracking(True)
        
        # Initialize scroll state
        self._scroll_timer = QTimer(self)
        self._scroll_item = None
        self._scroll_pos = 0
        self._original_text = ""
        self._mouse_debounce_timer = QTimer(self)
        self._mouse_debounce_timer.setSingleShot(True)
        self._pending_item = None
        
        # Store original mouse event handlers
        self._original_mouse_move = self.up_next.mouseMoveEvent
        self._original_leave_event = self.up_next.leaveEvent
        
        # --- FIX: Define the handlers and ACTUALLY assign them ---
    def on_mouse_move(event):
        # Call original handler first
        self._original_mouse_move(event)
        
        # Get item under mouse
        try:
            pos = event.position().toPoint()
        except AttributeError:
            pos = event.pos()
        
        item = self.up_next.itemAt(pos)
        
        # Use debounce to prevent rapid switching
        self._pending_item = item
        self._mouse_debounce_timer.stop()
        
        # Safely disconnect previous connections
        try:
            self._mouse_debounce_timer.timeout.disconnect()
        except (RuntimeError, TypeError):
            pass
        
        self._mouse_debounce_timer.timeout.connect(lambda: self._handle_item_change(item))
        self._mouse_debounce_timer.start(150)  # 150ms debounce
                
    def on_leave(event):
        # Call original handler first
        self._original_leave_event(event)
        # Stop debounce timer and clear state
        self._mouse_debounce_timer.stop()
        try:
            self._mouse_debounce_timer.timeout.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._pending_item = None
        self._stop_scrolling()
            
        # --- FIX: Actually assign the new handlers ---
        self.up_next.mouseMoveEvent = on_mouse_move
        self.up_next.leaveEvent = on_leave
        
    def on_mouse_move(event):
        # Call original handler first
        self._original_mouse_move(event)
        
        # Get item under mouse
        try:
            pos = event.position().toPoint()
        except AttributeError:
            pos = event.pos()
        
        item = self.up_next.itemAt(pos)
        
        # Use longer debounce to prevent rapid switching
        self._pending_item = item
        self._mouse_debounce_timer.stop()
        self._mouse_debounce_timer.timeout.disconnect()
        self._mouse_debounce_timer.timeout.connect(lambda: self._handle_item_change(item))
        self._mouse_debounce_timer.start(200)  # INCREASED from 100ms to 200ms
            
        def on_leave(event):
            # Call original handler first
            self._original_leave_event(event)
            self._stop_scrolling()
            print("[DEBUG] Mouse left Up Next")
        
        # Replace event handlers
        self.up_next.mouseMoveEvent = on_mouse_move
        self.up_next.leaveEvent = on_leave

    def _handle_item_change(self, item):
        """Handle item change with better debouncing"""
        # Only process if this is genuinely a different item
        if item == self._scroll_item:
            return
            
        # Always stop current scrolling first
        if self._scroll_item:
            self._stop_scrolling()
        
        # Use debounce to prevent rapid switching
        self._pending_item = item
        self._mouse_debounce_timer.stop()
        
        # Safely disconnect previous connections
        try:
            self._mouse_debounce_timer.timeout.disconnect()
        except (RuntimeError, TypeError):
            # No connections to disconnect, that's fine
            pass
        
        # Only connect and start if we have a valid item
        if item:
            self._mouse_debounce_timer.timeout.connect(lambda: self._start_scrolling(item))
            self._mouse_debounce_timer.start(150)  # 150ms debounce

    def _start_scrolling(self, item):
        """Start scrolling for an item"""
        if not item:
            return
        
        text = item.text(0)
        original_text = text
        
        # Remove emoji prefixes for width calculation
        clean_text = text
        if text.startswith(("🔴 ", "🐟 ", "🎬 ")):
            clean_text = text[2:]
        
        # print(f"[DEBUG] Checking scroll for: '{text}' (clean: '{clean_text}')")
        
        # Check if text needs scrolling
        font_metrics = self.up_next.fontMetrics()
        text_width = font_metrics.horizontalAdvance(clean_text)
        available_width = self.up_next.columnWidth(0) - 60  # Conservative margin
        
        # print(f"[DEBUG] Text width: {text_width}, Available: {available_width}")
        
        if text_width <= available_width:
            print("[DEBUG] Text fits, no scrolling needed")
            return
        
        # Stop any existing timer and disconnect ALL connections
        if self._scroll_timer.isActive():
            self._scroll_timer.stop()
            # --- FIX: Disconnect ALL previous connections ---
            self._scroll_timer.disconnect()
        
        # Start scrolling
        self._scroll_item = item
        self._original_text = original_text
        self._scroll_pos = 0
        
        def scroll_step():
            if not self._scroll_item or self._scroll_item != item:
                # print("[DEBUG] Scroll step - item mismatch, stopping")
                return
            
            pos = self._scroll_pos
            text_to_scroll = self._original_text
            
            # Create scrolled text with proper spacing
            scrolled = text_to_scroll[pos:] + "   " + text_to_scroll[:pos]
            
            # Update text safely
            try:
                if self._scroll_item and self._scroll_item == item:
                    self._scroll_item.setText(0, scrolled)
            except:
                print("[DEBUG] Failed to update scroll text")
                return
                
            self._scroll_pos = (pos + 1) % (len(text_to_scroll) + 3)
        
        # Connect and start timer
        self._scroll_timer.timeout.connect(scroll_step)
        self._scroll_timer.start(180)
        # print(f"[DEBUG] Started scrolling for: {original_text}")

    def _update_item_text(self, item, text):
        """Safely update item text in main thread"""
        if item and item == self._scroll_item:
            item.setText(0, text)

    def _stop_scrolling(self):
        """Stop scrolling and restore text"""
        # print("[DEBUG] _stop_scrolling called")
        
        if self._scroll_timer.isActive():
            self._scroll_timer.stop()
            # print("[DEBUG] Timer stopped")
        
        if self._scroll_item and self._original_text:
            try:
                # Immediately restore text
                self._scroll_item.setText(0, self._original_text)
                # print(f"[DEBUG] Restored text immediately: {self._original_text}")
            except Exception as e:
                print(f"[DEBUG] Error restoring text: {e}")
        
        # Clear state
        self._scroll_item = None
        self._original_text = ""
        self._scroll_pos = 0
        # print("[DEBUG] Scroll state cleared")

    def _reset_silence_counter(self):
        """Reset the silence detection timer - call when app starts playing."""
        try:
            if hasattr(self, 'audio_monitor') and self.audio_monitor:
                self.audio_monitor._silence_counter = 0.0
                # print("[SILENCE] Counter reset to 0")
        except Exception as e:
            print(f"[SILENCE] Reset failed: {e}")   

    def _start_timer_from_main_thread(self, delay, function_to_call):
        """A thread-safe slot to start a QTimer."""
        try:
            # Use QTimer.singleShot, which is thread-safe and executes on the main thread
            QTimer.singleShot(delay, function_to_call)
        except Exception as e:
            print(f"Error starting timer from main thread: {e}")

    def _show_status_message(self, message: str, timeout: int):
        """A thread-safe slot to show a status bar message."""
        try:
            self.status.showMessage(message, timeout)
        except Exception as e:
            print(f"Error showing status message: {e}")        
            
    def _update_volume_icon(self, is_muted):
            """Updates the volume icon to reflect the mute state, handling both QIcon and emoji."""
            try:
                icon_to_use = self.volume_mute_icon if is_muted else self.volume_icon
                tooltip_to_use = "Unmute (Volume)" if is_muted else "Mute (Volume)"

                # Apply the icon or emoji to the QLabel
                if isinstance(icon_to_use, QIcon):
                    # It's an icon, so clear any text and set the pixmap
                    self.volume_icon_label.setText("")
                    self.volume_icon_label.setPixmap(icon_to_use.pixmap(self.icon_size))
                else:
                    # It's an emoji string, so clear any pixmap and set the text
                    self.volume_icon_label.setPixmap(QPixmap())
                    self.volume_icon_label.setText(str(icon_to_use))

                self.volume_icon_label.setToolTip(tooltip_to_use)
            except Exception:
                pass         

    def _round_video_frame_corners(self, radius=8):
        """Add rounded corners and borders to the video frame."""
        try:
            # Create a rounded rectangle mask for the video frame
            rect = self.video_frame.rect()
            rounded_rect = QPixmap(rect.size())
            rounded_rect.fill(Qt.transparent)

            painter = QPainter(rounded_rect)
            painter.setRenderHint(QPainter.Antialiasing, True)
            
            # Draw the border
            border_color = QColor("#654321")  # Brown border color
            painter.setPen(QPen(border_color, 5))  # Border thickness = 5px
            
            # Draw the rounded rectangle with a border
            painter.setBrush(Qt.black)  # Background color for the video
            painter.drawRoundedRect(rect, radius, radius)
            painter.end()

            # Apply the mask to the video frame
            self.video_frame.setMask(rounded_rect.mask())

            # Optional: Add drop shadow effect for better styling
            shadow = QGraphicsDropShadowEffect(self.video_frame)
            shadow.setBlurRadius(15)
            shadow.setOffset(5, 5)
            shadow.setColor(QColor(0, 0, 0, 120))  # Semi-transparent black
            self.video_frame.setGraphicsEffect(shadow)

        except Exception as e:
            print(f"Failed to round video frame corners: {e}")

    def export_diagnostics(self):
        """Export logs and config files for debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = APP_DIR / f"silence_suzuka_diagnostics_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add log file if it exists
                logs_dir = APP_DIR / 'logs'
                log_file = logs_dir / 'silence_player.log'
                if log_file.exists():
                    zf.write(log_file, 'logs/silence_player.log')
                
                # Add config files
                for cfg_file in [CFG_SETTINGS, CFG_CURRENT, CFG_POS, CFG_PLAYLISTS, CFG_STATS, CFG_COMPLETED]:
                    if cfg_file.exists():
                        zf.write(cfg_file, f'config/{cfg_file.name}')
                
                # Add environment info
                import platform
                env_info = {
                    'python_version': sys.version,
                    'platform': platform.platform(),
                    'app_dir': str(APP_DIR),
                    'log_level': self.log_level,
                    'theme': getattr(self, 'theme', 'unknown'),
                    'playback_model': getattr(self, 'playback_model', 'unknown'),
                    'timestamp': timestamp
                }
                zf.writestr('environment.json', json.dumps(env_info, indent=2))
            
            QMessageBox.information(self, "Diagnostics Exported", 
                                  f"Diagnostics exported to:\n{zip_path}")
            logger.info(f"Diagnostics exported to {zip_path}")
            
        except Exception as e:
            logger.error(f"Export diagnostics failed: {e}", exc_info=True)
            QMessageBox.warning(self, "Export Failed", f"Failed to export diagnostics:\n\n{str(e)}")

    def open_logs_folder(self):
        """Open the logs folder in file explorer"""
        try:
            import subprocess
            import platform
            logs_dir = APP_DIR / 'logs'
            logs_dir.mkdir(exist_ok=True)  # Ensure it exists
            
            if platform.system() == 'Windows':
                subprocess.run(['explorer', str(logs_dir)], check=False)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(logs_dir)], check=False)
            else:  # Linux
                subprocess.run(['xdg-open', str(logs_dir)], check=False)
        except Exception as e:
            logger.error(f"Open logs folder failed: {e}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to open logs folder:\n\n{str(e)}")
           
    def update_theme(self, theme):
        """Update the UI to match the current theme."""
        if theme == "dark":
            # Dark theme styling
            self.scope_dropdown.setStyleSheet("""
                QComboBox {
                    background-color: #2b2b2b;
                    color: white;
                    border: 1px solid #5a5a5a;
                    padding: 5px;
                    border-radius: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: #3a3a3a;
                    color: white;
                    selection-background-color: #505050;
                    selection-color: white;
                }
            """)
        elif theme == "light":
            # Light theme styling
            self.scope_dropdown.setStyleSheet("""
                QComboBox {
                    background-color: #ffffff;
                    color: black;
                    border: 1px solid #cccccc;
                    padding: 5px;
                    border-radius: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: #f9f9f9;
                    color: black;
                    selection-background-color: #dcdcdc;
                    selection-color: black;
                }
            """)
        elif theme == "vinyl":
            # Vinyl theme styling
            self.scope_dropdown.setStyleSheet("""
                QComboBox {
                    background-color: #f3ead3;
                    color: #4a2c2a;
                    border: 1px solid #c2a882;
                    padding: 5px;
                    border-radius: 5px;
                }
                QComboBox QAbstractItemView {
                    background-color: #faf3e0;
                    color: #4a2c2a;
                    selection-background-color: #e76f51;
                    selection-color: #f3ead3;
                }
            """)

        # Ensure other widgets are also updated dynamically
        print(f"Theme updated to: {theme}")     

    # UI
    def _build_ui(self):
        self._playlist_manager = EnhancedPlaylistManager(self, APP_DIR)

        central = QWidget(); central.setObjectName('bgRoot'); self.setCentralWidget(central)
        root = QVBoxLayout(central); root.setContentsMargins(8, 8, 8, 8); root.setSpacing(8)
        icon_size = QSize(22, 22)

        # Top bar
        top = QHBoxLayout(); top.setSpacing(8)
        title = QLabel("Silence Suzuka Player"); title.setObjectName('titleLabel'); title.setFont(self._font_serif(20, italic=True, bold=True))
        # Dropdown for Scope Selection - COMMENTED OUT FOR SIMPLICITY
        # self.scope_dropdown = QComboBox()
        # self.scope_dropdown.setObjectName('scopeDropdown')
        # self.scope_dropdown.addItem("Library", None)  # Default scope
        # self.scope_dropdown.addItem("Playlist 1", "playlist1")
        # self.scope_dropdown.addItem("Playlist 2", "playlist2")
        # self.scope_dropdown.addItem("YouTube", "youtube")
        # self.scope_dropdown.addItem("Bilibili", "bilibili")  # Add Bilibili as its own option
        # self.scope_dropdown.addItem("Local Media", "local-media")
        # self.scope_dropdown.setCurrentIndex(0)  # Default to Library
        # self.scope_dropdown.currentIndexChanged.connect(lambda idx: self._on_scope_changed(idx))

        # Add title to the top layout
        top.addWidget(title)  # Add the title on the far left
        # top.addWidget(self.scope_dropdown)  # Add the dropdown to the right of the title - COMMENTED OUT
        top.addStretch()  # Push remaining items to the right
        
        # Right: Today badge • Silence • Stats • Settings • Theme
        self.today_badge = QLabel("0s"); self.today_badge.setObjectName('statsBadge'); self.today_badge.setToolTip("Total listening time today")
        self.today_badge.setVisible(getattr(self, 'show_today_badge', True))
        top.addWidget(self.today_badge)
        
        self.silence_indicator = QLabel("🔇"); self.silence_indicator.setObjectName('silenceIndicator'); self.silence_indicator.setToolTip("System silence indicator — shows when no system audio is detected (configurable in Settings → Audio Monitor)")
        top.addWidget(self.silence_indicator)
        
        self.stats_btn = QPushButton("📊")
        self.stats_btn.setObjectName('settingsBtn')
        self.stats_btn.setToolTip("Listening Statistics")
        self.stats_btn.clicked.connect(self.open_stats)
        
        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setObjectName('settingsBtn')
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.open_settings_tabs)
    
        top.addWidget(self.stats_btn)
        top.addWidget(self.settings_btn)
        
        self.theme_btn = QPushButton("🎨"); self.theme_btn.setObjectName('settingsBtn'); self.theme_btn.setToolTip("Dark mode coming soon!"); self.theme_btn.setEnabled(False)  
        # self.theme_btn.clicked.connect(self.toggle_theme)
        top.addWidget(self.theme_btn)
        
        # Add the top layout to the root layout
        root.addLayout(top)    
        
        # Content
        content = QHBoxLayout(); content.setSpacing(8); root.addLayout(content, 1)

        # Main area: video frame + controls (now on the left, compact)
        main_col = QVBoxLayout(); 
        video_widget = QWidget(); video_widget.setMinimumWidth(300); video_widget.setMinimumWidth(300)
        video_layout = QVBoxLayout(video_widget); video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addLayout(main_col)
        content.addWidget(video_widget, 0)

        # Sidebar (now on the right, gets remaining space)
        side_widget = QWidget(); side_widget.setObjectName('sidebar'); side_layout = QVBoxLayout(side_widget); side_layout.setSpacing(10)
        side_layout.setContentsMargins(8, 8, 8, 8)
        content.addWidget(side_widget, 1)

        # ---- Split Add Media Button (Fixed) ----
        add_media_container = QWidget()
        add_media_container.setObjectName("addMediaContainer")
        add_media_container.setFixedHeight(44)
        add_media_container.setMaximumWidth(220)  # Constrain width

        add_media_layout = QHBoxLayout(add_media_container)
        add_media_layout.setContentsMargins(0, 0, 0, 0)
        add_media_layout.setSpacing(0)

        # Main button (most of the width)
        self.add_media_main = QPushButton("Add Media")
        self.add_media_main.setObjectName("addMediaMain")
        self.add_media_main.setFixedHeight(44)
        self.add_media_main.clicked.connect(self._on_add_media_clicked)

        # Dropdown button (small arrow)
        self.add_media_dropdown = QPushButton("▼")
        self.add_media_dropdown.setObjectName("addMediaDropdown")
        self.add_media_dropdown.setFixedSize(32, 44)

        # Create the menu
        menu = QMenu(self)
        menu.addAction("🔗 Add Link...", self.add_link_dialog)
        menu.addAction("📁 Add Files...", self.add_local_files)

        def show_add_media_menu():
            try:
                self._apply_menu_theme(menu)
                # Position menu below the dropdown button
                pos = self.add_media_dropdown.mapToGlobal(self.add_media_dropdown.rect().bottomRight())
                pos.setX(pos.x() - menu.sizeHint().width())  # Right-align the menu
                menu.exec(pos)
            except Exception:
                # Fallback positioning
                menu.exec(self.add_media_dropdown.mapToGlobal(self.add_media_dropdown.rect().bottomLeft()))

        # Connect the dropdown button OUTSIDE the function definition
        self.add_media_dropdown.clicked.connect(show_add_media_menu)

        # Add to layout
        add_media_layout.addWidget(self.add_media_main, 1)
        add_media_layout.addWidget(self.add_media_dropdown, 0)

        side_layout.addWidget(add_media_container)
        # ---- end Split Add Media Button ----

        opts = QHBoxLayout()
        # Front page toggles removed; configure in Settings
        side_layout.addLayout(opts)

        # Playlist controls (save/load) — Unwatched toggle with icon swap (eye / eye-off)
        controls = QHBoxLayout()
        self.save_btn = QPushButton("💾")
        self.save_btn.setObjectName('miniBtn')
        self.save_btn.setToolTip("Save current playlist")
        self.save_btn.clicked.connect(self.save_playlist)
        self.save_btn.setFixedSize(36, 28)
        self.load_btn = QPushButton("📂")
        self.load_btn.setObjectName('miniBtn')
        self.load_btn.setToolTip("Load saved playlist")
        self.load_btn.clicked.connect(self.load_playlist_dialog) 
        self.load_btn.setFixedSize(36, 28)

        self.duration_btn = QPushButton("⏱️")
        self.duration_btn.setObjectName('miniBtn')
        self.duration_btn.setToolTip("Fetch all durations")
        self.duration_btn.clicked.connect(self._fetch_all_durations)
        self.duration_btn.setFixedSize(36, 28)

        # New: icon-only Unwatched toggle (prefers icons/eye.svg + icons/eye-off.svg)
        self.unwatched_btn = QPushButton()
        self.unwatched_btn.setObjectName('miniBtn')
        self.unwatched_btn.setCheckable(True)
        try:
            self.unwatched_btn.setFixedSize(36, 28)
        except Exception:
            pass

        # Resolve SVG icons if present; otherwise fallback to emoji
        try:
            eye_on_path = APP_DIR / 'icons' / 'eye.svg'
            eye_off_path = APP_DIR / 'icons' / 'eye-off.svg'
            if eye_on_path.exists() and eye_off_path.exists():
                self._unwatched_icon_on = QIcon(str(eye_on_path))
                self._unwatched_icon_off = QIcon(str(eye_off_path))
                # icon-only, set icon size for alignment
                self.unwatched_btn.setIconSize(QSize(18, 18))
                self.unwatched_btn.setText("")  # icon-only
            else:
                self._unwatched_icon_on = None
                self._unwatched_icon_off = None
                # Emoji fallback: OFF shows 👁 (meaning show) and ON shows 🙈 (hidden)
                # set a compact emoji so button width matches others
                self.unwatched_btn.setText("👁" if not getattr(self, 'unwatched_only', False) else "🙈")
        except Exception:
            self._unwatched_icon_on = None
            self._unwatched_icon_off = None
            self.unwatched_btn.setText("👁" if not getattr(self, 'unwatched_only', False) else "🙈")

                # use themed tooltip instead of native QToolTip (keep accessible description)
        try:
            self.unwatched_btn.setAccessibleDescription("Show unwatched items only (toggle)")
        except Exception:
            pass
        self.unwatched_btn.setToolTip("")
        # Reuse existing logic
        self.unwatched_btn.toggled.connect(self._toggle_unwatched_only)
        # Update visuals (icon/text and styling)
        self.unwatched_btn.toggled.connect(self._update_unwatched_btn_visual)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # initialize state from persisted flag (set in _load_files)
        try:
            self.unwatched_btn.setChecked(bool(getattr(self, 'unwatched_only', False)))
        except Exception:
            pass
        try:
            # ensure correct initial appearance
            self._update_unwatched_btn_visual(bool(getattr(self, 'unwatched_only', False)))
        except Exception:
            pass
        try:
            # Install themed tooltip (shows app-styled tooltip and is updated by _update_unwatched_btn_visual)
            initial_txt = "Unwatched only: ON (click to turn off)" if getattr(self, 'unwatched_only', False) else "Show unwatched items only (OFF)"
            self._install_themed_tooltip(self.unwatched_btn, initial_txt)
        except Exception:
            pass   

        # Layout: Save | Load | Unwatched-icon | spacer | Group
        controls.addWidget(self.save_btn)
        controls.addWidget(self.load_btn)
        controls.addWidget(self.duration_btn)
        controls.addWidget(self.unwatched_btn)
        controls.addStretch()
        side_layout.addLayout(controls)

        try:
            self._update_group_toggle_visibility()
        except Exception:
            pass

        # Search bar container for width control
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search playlist...")
        self.search_bar.setObjectName('searchBar')
        self.search_bar.setClearButtonEnabled(True)

        # Constrain search bar width
        self.search_bar.setMaximumWidth(280)
        self.search_bar.setMinimumWidth(150)

        search_layout.addWidget(self.search_bar)
        search_layout.addStretch()  # Push search bar to the left

        self.search_bar.setObjectName('searchBar')
        self.search_bar.setClearButtonEnabled(True)  # This enables the X button

        # Install event filter to handle IME events
        self.search_bar.installEventFilter(self)
        
        # Replace textChanged with improved Japanese IME support
        self.search_bar.textChanged.connect(self._on_search_text_changed)
        self.search_bar.returnPressed.connect(lambda: self.filter_playlist(self.search_bar.text()))

        # Initialize search timer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)

        def do_filter():
            # print(f"[DEBUG] Timer fired, filtering with: '{self.search_bar.text()}'")
            self.filter_playlist(self.search_bar.text())

        self._search_timer.timeout.connect(do_filter)
        
        # Track IME composition state
        self._ime_composing = False

        # Clear with Escape key
        QShortcut(QKeySequence(Qt.Key_Escape), self.search_bar, self.search_bar.clear)
        side_layout.addWidget(search_container)

        self.library_header_label = ClickableLabel("Library (0)")
        self.library_header_label.setObjectName('libraryHeader')
        self.library_header_label.setToolTip("Double-click to play all")
        self.library_header_label.mouseDoubleClickEvent = lambda e: self._play_all_library()

        self.library_header_label.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_header_label.customContextMenuRequested.connect(self._show_library_header_context_menu)

        # ADD THIS DEBUG:
        # print(f"[HEADER DEBUG] Library header context menu policy set: {self.library_header_label.contextMenuPolicy()}")
        # print(f"[HEADER DEBUG] Signal connected: customContextMenuRequested")

        side_layout.addWidget(self.library_header_label)

        # Create a container widget to hold either the playlist or the empty state view
        self.playlist_container = QWidget()
        self.playlist_stack = QStackedLayout(self.playlist_container)
        self.playlist_stack.setContentsMargins(0, 0, 0, 0)

        # 1. The Playlist Tree (Index 0)
        self.playlist_tree = PlaylistTree(self)
        self.playlist_tree.setHeaderHidden(True)
        self.playlist_tree.setObjectName('playlistTree')
        self.playlist_tree.setAlternatingRowColors(True)
        self.playlist_tree.setIndentation(20)
        self.playlist_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.playlist_tree.itemDoubleClicked.connect(self.on_tree_item_double_clicked)
        self.playlist_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.playlist_tree.customContextMenuRequested.connect(self._show_playlist_context_menu)
        self.playlist_tree.mousePressEvent = self._create_mouse_press_handler()
        
        # Set text elide mode for single-line with ellipsis
        self.playlist_tree.setTextElideMode(Qt.ElideRight)

        # Set playlist font: Lora, italic, bold (size set dynamically)
        self.playlist_tree.setFont(self._font_serif_no_size(italic=True, bold=True))

        # --- ADD THESE LINES FOR ICON SIZE AND ROW HEIGHT ---
        self.playlist_tree.setIconSize(QSize(24, 24))  

        # Apply custom style ONLY for dark theme (let vinyl use system default)
        # We'll apply this properly after theme loads in _load_files()
        pass  # Remove the style application here for now

        self.playlist_stack.addWidget(self.playlist_tree)

         # --- ADD THESE LINES FOR ICON SIZE AND ROW HEIGHT ---
        self.playlist_tree.setIconSize(QSize(24, 24))  

        self.playing_delegate = PlayingItemDelegate(self)
        self.playlist_tree.setItemDelegate(self.playing_delegate)

        # 2. The Empty State Widget (Index 1)
        self.empty_state_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_state_widget)
        empty_layout.addStretch()
        empty_icon = QLabel()
        empty_icon.setObjectName('emptyStateIcon')
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setPixmap(load_svg_icon('icons/music-off-tabler.svg', QSize(48, 48)).pixmap(48, 48))
        empty_layout.addWidget(empty_icon)
        self.empty_state_heading = QLabel("Your Library is Empty")
        self.empty_state_heading.setObjectName('emptyStateHeading')
        self.empty_state_heading.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_state_heading)
        self.empty_state_subheading = QLabel("Click 'Add Media' to get started.")
        self.empty_state_subheading.setObjectName('emptyStateSubheading')
        self.empty_state_subheading.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(self.empty_state_subheading)
        empty_layout.addStretch()
        self.playlist_stack.addWidget(self.empty_state_widget)

        # Add the container to the sidebar
        side_layout.addWidget(self.playlist_container, 1)

        # Video frame (now in the left compact area)
        self.video_frame = QWidget(); self.video_frame.setObjectName('videoWidget')
        self.video_frame.setStyleSheet("background:#000; border-radius: 6px"); main_col.addWidget(self.video_frame, 3)

        # Now Playing and Progress Bar Layout
        now_playing_layout = QVBoxLayout()

        # Track Title Label
        self.track_label = QLabel("No track playing")
        self.track_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed) 
        self.track_label.setObjectName('trackLabel')
        self.track_label.setFont(self._font_serif_no_size(italic=True, bold=True))
        self.track_label.setWordWrap(False)  # Disable word wrap for eliding
        self.track_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.track_label.setStyleSheet("""
            color: #4a2c2a;
            background: transparent;
            margin-top: 14px;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        """)
        self._track_title_full = "No track playing"  # Store full text for eliding

        # Initialize track title scrolling components
        self._track_scroll_timer = None
        self._track_scroll_pos = 0
        self._track_original_text = ""

        # FIXED: Proper event handler setup
        def track_enter_handler(event):
            # print("[TRACK DEBUG] Mouse entered track label")
            self._start_track_title_scrolling()

        def track_leave_handler(event):
            # print("[TRACK DEBUG] Mouse left track label")
            self._stop_track_title_scrolling()

        # Enable mouse tracking and set event handlers
        self.track_label.setMouseTracking(True)
        self.track_label.enterEvent = track_enter_handler
        self.track_label.leaveEvent = track_leave_handler

        # Add mouse tracking for track title scrolling
        self.track_label.setMouseTracking(True)
        self.track_label.enterEvent = self._on_track_title_enter
        self.track_label.leaveEvent = self._on_track_title_leave

        now_playing_layout.addWidget(self.track_label)

        # Progress Bar and Time Labels
        progress_layout = QHBoxLayout()
        self.time_label = QLabel("0:00")
        self.time_label.setObjectName('timeLabel')
        self.time_label.setFont(QFont(self._ui_font))
        self.progress = ProgressSlider(Qt.Horizontal)
        self.progress.sliderPressed.connect(lambda: setattr(self, '_user_scrubbing', True))
        self.progress.sliderReleased.connect(self._on_slider_released)
        self.progress.seekOnClick.connect(self.set_position)
        self.progress.sliderMoved.connect(self._on_slider_moved)
        self.dur_label = QLabel("0:00")
        self.dur_label.setObjectName('durLabel')
        self.dur_label.setFont(QFont(self._ui_font))
        
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.progress, 1)
        progress_layout.addWidget(self.dur_label)
        now_playing_layout.addLayout(progress_layout)


        # Up Next panel (toggle via Settings)
        try:
            self.up_next_container = QWidget()
            up_layout = QVBoxLayout(self.up_next_container)
            up_layout.setContentsMargins(0,0,0,0)

            self.up_next_header = QPushButton("▼ Up Next")
            self.up_next_header.setCheckable(True)
            self.up_next_header.setChecked(True)
            self.up_next_header.setObjectName('upNextHeader')
            self.up_next_header.clicked.connect(self._on_up_next_header_clicked)
            up_layout.addWidget(self.up_next_header)

            # Create a stacked layout to switch between the list and a message
            self.up_next_stack = QStackedLayout()

            # 1. The song list (index 0)
            self.up_next = QTreeWidget()
            self.up_next.setHeaderHidden(True)
            self.up_next.setObjectName('upNext')
            # self.up_next.setFixedHeight(140)  <-- REMOVED THIS LINE
            self.up_next.setFont(self._font_serif_no_size(italic=True, bold=True))
            self.up_next.setAlternatingRowColors(True)
            self.up_next.setIndentation(12)
            self.up_next.setIconSize(QSize(24, 24))
            self.up_next.setContextMenuPolicy(Qt.CustomContextMenu)
            self.up_next.customContextMenuRequested.connect(self._show_up_next_menu)
            self.up_next.itemDoubleClicked.connect(self._on_up_next_double_clicked)
            self.up_next_stack.addWidget(self.up_next)

            # 2. The shuffle message (index 1)
            shuffle_msg_widget = QWidget()
            shuffle_msg_layout = QVBoxLayout(shuffle_msg_widget)
            shuffle_msg_layout.setAlignment(Qt.AlignCenter)
            shuffle_msg_label = QLabel("🔀 Shuffle Mode is Active")
            shuffle_msg_label.setObjectName('emptyStateSubheading')
            shuffle_msg_label.setAlignment(Qt.AlignCenter)
            shuffle_msg_layout.addWidget(shuffle_msg_label)
            self.up_next_stack.addWidget(shuffle_msg_widget)

            # 3. The repeat message (index 2) - ADD THIS NEW BLOCK
            repeat_msg_widget = QWidget()
            repeat_msg_layout = QVBoxLayout(repeat_msg_widget)
            repeat_msg_layout.setAlignment(Qt.AlignCenter)
            repeat_msg_label = QLabel("🔁 Repeat Mode is Active")
            repeat_msg_label.setObjectName('emptyStateSubheading')
            repeat_msg_label.setAlignment(Qt.AlignCenter)
            repeat_msg_layout.addWidget(repeat_msg_label)
            self.up_next_stack.addWidget(repeat_msg_widget)

            up_layout.addLayout(self.up_next_stack) # Add the stack to the panel
            main_col.addWidget(self.up_next_container, 1) # <-- MODIFIED THIS LINE
        except Exception:
            pass
        
        # Shuffle button
        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.setIconSize(self.icon_size)
        self.shuffle_btn.setObjectName('controlBtn')
        self.shuffle_btn.setToolTip("Shuffle (S)")
        self.shuffle_btn.clicked.connect(self._toggle_shuffle)
        self.shuffle_btn.setFixedSize(40, 40) 
        
        # Prev button
        self.prev_btn = QPushButton()
        self.prev_btn.setIconSize(self.icon_size)
        self.prev_btn.setObjectName('controlBtn')
        self.prev_btn.setToolTip("Previous Track (P)")
        self.prev_btn.clicked.connect(self.previous_track)
        self.shuffle_btn.setFixedSize(40, 40) 

        # Play/Pause button
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setIconSize(QSize(50, 50))
        self.play_pause_btn.setObjectName('playPauseBtn')
        self.play_pause_btn.setToolTip("Play/Pause (Space)")
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)

        # Add this test:
        def simple_test():
            # print("Play button was clicked!")
            try:
                current_size = self.play_pause_btn.iconSize()
                # print(f"Current icon size: {current_size.width()}x{current_size.height()}")
                # Test if we can change icon size
                self.play_pause_btn.setIconSize(QSize(45, 45))
                QTimer.singleShot(200, lambda: self.play_pause_btn.setIconSize(QSize(50, 50)))
            except Exception as e:
                print(f"Size test failed: {e}")

        self.play_pause_btn.clicked.connect(simple_test)

        # Test simple press feedback
        def test_press():
            pass # print("Button pressed - animation should trigger")
        def test_release():
            pass # print("Button released - animation should trigger")
        self.play_pause_btn.pressed.connect(test_press)
        self.play_pause_btn.released.connect(test_release)

        self.play_pause_btn.setFixedSize(60, 60)
        
        # Next button
        self.next_btn = QPushButton()
        self.next_btn.setIconSize(self.icon_size)
        self.next_btn.setObjectName('controlBtn')
        self.next_btn.setToolTip("Next Track (N)")
        self.next_btn.clicked.connect(self.next_track)
        self.next_btn.setFixedSize(40, 40)

        # Repeat button
        self.repeat_btn = QPushButton()
        self.repeat_btn.setCheckable(True)
        self.repeat_btn.setIconSize(self.icon_size)
        self.repeat_btn.setObjectName('controlBtn')
        self.repeat_btn.setToolTip("Repeat (R)")
        self.repeat_btn.clicked.connect(self._toggle_repeat)
        self.repeat_btn.setFixedSize(40, 40)
        
        # --- Volume icon: prefer icons/volume.svg rendered with QSvgRenderer (hi-dpi aware) ---
        # --- Volume icon: prefer icons/volume.svg rendered with QSvgRenderer (hi-dpi aware) ---
        try:
            from PySide6.QtCore import QRectF
            # create label
            self.volume_icon_label = QLabel()
            self.volume_icon_label.setObjectName('volumeIconLabel')
            self.volume_icon_label.setFixedSize(icon_size)  # icon_size defined earlier (QSize(22,22))
            self.volume_icon_label.setToolTip("Volume")
            try:
                self.volume_icon_label.setAccessibleDescription("Volume")
            except Exception:
                pass

            svg_path = APP_DIR / 'icons' / 'volume.svg'
            rendered = False
            try:
                # If QtSvg (QSvgRenderer) is available and the SVG exists, render it into a QPixmap
                if svg_path.exists() and ('QSvgRenderer' in globals()) and (QSvgRenderer is not None):
                    # Use theme-appropriate color
                    if getattr(self, 'theme', 'dark') == 'dark':
                        color = "#d0d0d0"  # off-white grey for dark theme
                    else:
                        color = "#4a2c2a"  # brown for vinyl theme
                    
                    # Use the existing _render_svg_tinted function to color the icon
                    pm = _render_svg_tinted(str(svg_path), icon_size, color)
                    if not pm.isNull():
                        self.volume_icon_label.setPixmap(pm)
                        rendered = True
            except Exception:
                rendered = False

            # Fallback: use previously loaded QIcon (self.volume_icon) if available
            if not rendered:
                try:
                    if hasattr(self, 'volume_icon') and not self.volume_icon.isNull():
                        self.volume_icon_label.setPixmap(self.volume_icon.pixmap(icon_size))
                        rendered = True
                except Exception:
                    rendered = False

            # Final fallback: emoji
            if not rendered:
                self.volume_icon_label.setText("🔇")
                self.volume_icon_label.setAlignment(Qt.AlignCenter)

            # Optional: click-to-toggle-mute handler (uncomment assignment line below to enable)
            try:
                def _vol_clicked(ev):
                    try:
                        if hasattr(self, 'mpv') and (getattr(self, 'mpv', None) is not None):
                            try:
                                cur = bool(self.mpv.mute)
                                self.mpv.mute = not cur
                            except Exception:
                                pass
                    except Exception:
                        pass
                self.volume_icon_label.mousePressEvent = _vol_clicked
            except Exception:
                pass

            
        except Exception:
            controls_bar.addWidget(QLabel("🔊"))
        # --- end volume icon block ---
        self.volume_slider = ClickableSlider(Qt.Horizontal)
        self.volume_slider.setObjectName('volumeSlider')
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setToolTip(f"Volume: 80%")  # Initial tooltip
        self.volume_slider.valueChanged.connect(self.set_volume)
        # Update tooltip on any value change
        self.volume_slider.valueChanged.connect(lambda v: self.volume_slider.setToolTip(f"Volume: {v}%"))
        # --- Corrected Centered Control Bar Layout ---
        controls_row = QGridLayout()
        controls_row.setContentsMargins(0, 0, 0, 0)

        # 1. Define the center button group
        center_controls = QHBoxLayout()
        center_controls.setSpacing(12)
        center_controls.addWidget(self.shuffle_btn)
        center_controls.addWidget(self.prev_btn)
        center_controls.addWidget(self.play_pause_btn)
        center_controls.addWidget(self.next_btn)
        center_controls.addWidget(self.repeat_btn)
        center_widget = QWidget()
        center_widget.setLayout(center_controls)

        # 2. Define the volume control group
        volume_controls = QHBoxLayout()
        volume_controls.setSpacing(6)
        volume_controls.addWidget(self.volume_icon_label)
        volume_controls.addWidget(self.volume_slider)
        volume_widget = QWidget()
        volume_widget.setLayout(volume_controls)

        # 3. Add both groups to the layout
        # The button group spans all 3 columns and is centered within them.
        controls_row.addWidget(center_widget, 0, 0, 1, 3, alignment=Qt.AlignHCenter)
        # The volume group is placed in the 3rd column (index 2) and aligned to the right.
        controls_row.addWidget(volume_widget, 0, 2, alignment=Qt.AlignRight)

        # Make the outer columns stretchable to push the volume slider to the edge.
        controls_row.setColumnStretch(0, 1)
        controls_row.setColumnStretch(2, 1)

        # Add the full-width Now Playing panel just above the controls
        root.addLayout(now_playing_layout) # <--- ADD THIS LINE

        # Add controls to root layout for full-width span
        root.addLayout(controls_row)

        self.status = QStatusBar(); self.setStatusBar(self.status)

        # UI timers
        self.badge_timer = QTimer(self); self.badge_timer.timeout.connect(self.update_badge); self.badge_timer.start(5000)
        # Apply Up Next initial visibility from settings
        try:
            _show_up = bool(getattr(self, 'show_up_next', True))
            if hasattr(self, 'up_next_container'):
                self.up_next_container.setVisible(_show_up)
            if _show_up:
                try:
                    collapsed = bool(getattr(self, 'up_next_collapsed', False))
                    self.up_next_header.setChecked(not collapsed)
                    self._toggle_up_next_visible(self.up_next_header.isChecked())
                except Exception:
                    pass
        except Exception:
            pass
        self._setup_up_next_scrolling()    

        # DEBUG: Test if undo system is set up
        # print("=== UNDO SYSTEM CHECK ===")
        # print(f"_add_undo_operation exists: {hasattr(self, '_add_undo_operation')}")
        # print(f"_perform_undo exists: {hasattr(self, '_perform_undo')}")  
        # print(f"_undo_stack exists: {hasattr(self, '_undo_stack')}")
        # print(f"Undo stack size: {len(getattr(self, '_undo_stack', []))}")
        # print("========================")

    def _play_selected_group(self):
        """Play the currently selected group when 'B' key is pressed"""
        try:
            selected_items = self.playlist_tree.selectedItems()
            if not selected_items:
                self.status.showMessage("No group selected", 2000)
                return
            
            # Find the first selected group
            for item in selected_items:
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'group':
                    raw_key = data[1] if len(data) > 1 else None
                    
                    # Use the same logic as the context menu to identify the group
                    actual_key = raw_key
                    
                    if not actual_key:
                        try:
                            actual_key = item.data(0, Qt.UserRole + 1)
                        except Exception:
                            pass
                    
                    if not actual_key:
                        item_text = item.text(0)
                        if item_text and item_text.startswith('📃 '):
                            group_name = item_text[2:].strip()
                            if '(' in group_name and group_name.endswith(')'):
                                group_name = group_name[:group_name.rfind('(')].strip()
                            
                            for playlist_item in self.playlist:
                                if (playlist_item.get('playlist') == group_name or 
                                    playlist_item.get('playlist_key') == group_name):
                                    actual_key = playlist_item.get('playlist_key') or playlist_item.get('playlist')
                                    break
                            
                            if not actual_key:
                                actual_key = group_name
                    
                    if actual_key:
                        indices = self._iter_indices_for_group(actual_key)
                        if indices:
                            print(f"[Hotkey] Playing group '{actual_key}' with {len(indices)} items")
                            self._set_scope_group(actual_key, autoplay=True)
                            return
                        else:
                            self.status.showMessage(f"No items found in group '{actual_key}'", 3000)
                            return
                    else:
                        self.status.showMessage("Unable to identify selected group", 3000)
                        return
            
            # If no group was found in selection
            self.status.showMessage("No group selected - select a group header and press 'B'", 3000)
            
        except Exception as e:
            print(f"Play selected group error: {e}")
            self.status.showMessage(f"Play group failed: {e}", 3000)    

    def _navigate_to_top(self):
        """Navigate to the top of the playlist tree and select the first item"""
        try:
            if not self.playlist:
                self.status.showMessage("Playlist is empty", 2000)
                return
                
            # Get the first item in the tree
            first_item = None
            
            # Check if we have any top-level items
            if self.playlist_tree.topLevelItemCount() > 0:
                top_item = self.playlist_tree.topLevelItem(0)
                
                # If it's a group, try to get its first child
                if top_item.childCount() > 0:
                    first_item = top_item.child(0)
                    # Expand the group to show the first item
                    top_item.setExpanded(True)
                else:
                    # It's a single item at the top level
                    first_item = top_item
            
            if first_item:
                # Clear current selection and select the first item
                self.playlist_tree.clearSelection()
                first_item.setSelected(True)
                self.playlist_tree.setCurrentItem(first_item)
                
                # Scroll to the top
                self.playlist_tree.scrollToTop()
                
                # Extract the playlist index if this is a playable item
                data = first_item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'current':
                    playlist_index = data[1]
                    title = self.playlist[playlist_index].get('title', 'Unknown')
                    self.status.showMessage(f"Top: {title}", 2000)
                else:
                    self.status.showMessage("Navigated to top of playlist", 2000)
            else:
                self.status.showMessage("No items found in playlist", 2000)
                
        except Exception as e:
            print(f"Navigate to top error: {e}")
            self.status.showMessage(f"Navigate to top failed: {e}", 3000)

    def _navigate_to_bottom(self):
        """Navigate to the bottom of the playlist tree and select the last item"""
        try:
            if not self.playlist:
                self.status.showMessage("Playlist is empty", 2000)
                return
                
            # Find the last playable item in the tree
            last_item = None
            
            # Start from the bottom and work our way up
            for i in range(self.playlist_tree.topLevelItemCount() - 1, -1, -1):
                top_item = self.playlist_tree.topLevelItem(i)
                if not top_item:
                    continue
                    
                # If it's a group with children, get the last child
                if top_item.childCount() > 0:
                    last_child = top_item.child(top_item.childCount() - 1)
                    last_item = last_child
                    # Expand the group to show the last item
                    top_item.setExpanded(True)
                    break
                else:
                    # It's a single item at the top level
                    last_item = top_item
                    break
            
            if last_item:
                # Clear current selection and select the last item
                self.playlist_tree.clearSelection()
                last_item.setSelected(True)
                self.playlist_tree.setCurrentItem(last_item)
                
                # Scroll to the bottom
                self.playlist_tree.scrollToBottom()
                
                # Extract the playlist index if this is a playable item
                data = last_item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'current':
                    playlist_index = data[1]
                    title = self.playlist[playlist_index].get('title', 'Unknown')
                    self.status.showMessage(f"Bottom: {title}", 2000)
                else:
                    self.status.showMessage("Navigated to bottom of playlist", 2000)
            else:
                self.status.showMessage("No items found in playlist", 2000)
                
        except Exception as e:
            print(f"Navigate to bottom error: {e}")
            self.status.showMessage(f"Navigate to bottom failed: {e}", 3000)        
            
    def _update_unwatched_btn_visual(self, checked: bool):
        """Swap icon/text and styling so ON vs OFF is obvious — icon + color only, no filled pill or border.
        Also update the themed tooltip text if installed."""
        try:
            # If SVG icons available, swap them
            if getattr(self, '_unwatched_icon_on', None) and getattr(self, '_unwatched_icon_off', None):
                if checked:
                    # ON = eye (show unwatched only) — green tint
                    self.unwatched_btn.setIcon(self._unwatched_icon_on)
                else:
                    # OFF = eye-off — muted tint
                    self.unwatched_btn.setIcon(self._unwatched_icon_off)
                self.unwatched_btn.setText("")  # icon-only
                # Ensure icon is sized for alignment
                try:
                    self.unwatched_btn.setIconSize(QSize(18, 18))
                except Exception:
                    pass
            else:
                # Emoji fallback: ON = 🙈 (filter active), OFF = 👁 (show all)
                if checked:
                    self.unwatched_btn.setText("🙈")
                else:
                    self.unwatched_btn.setText("👁")

            # Simple color-only styling (transparent background, no border)
            if checked:
                # ON -> green tint on icon/text, transparent background
                self.unwatched_btn.setStyleSheet(
                    "background-color: transparent; color: #1DB954; border: none; padding: 0; margin: 0;"
                )
                native_tip = "Unwatched only: ON (click to turn off)"
            else:
                # OFF -> muted grey icon/text, transparent background
                self.unwatched_btn.setStyleSheet(
                    "background-color: transparent; color: #B3B3B3; border: none; padding: 0; margin: 0;"
                )
                native_tip = "Show unwatched items only (OFF)"

            # keep accessible description for assistive tech, hide native tooltip visually
            try:
                self.unwatched_btn.setAccessibleDescription(native_tip)
            except Exception:
                pass
            try:
                self.unwatched_btn.setToolTip("")
            except Exception:
                pass

            # If we installed a themed tooltip widget, update its text too
            try:
                if hasattr(self, '_themed_tooltips'):
                    pair = self._themed_tooltips.get(self.unwatched_btn)
                    if pair and isinstance(pair, tuple):
                        tip_label, _ = pair
                        if tip_label:
                            tip_label.setText(native_tip)
            except Exception:
                pass

        except Exception:
            pass            


    
    def _install_themed_tooltip(self, widget, text: str, duration: int = 3500):
        """Install a small themed tooltip for a single widget (shows on hover).
        Force the light (vinyl/cream) styling so all app tooltips look the same."""
        try:
            # Ensure storage exists
            if not hasattr(self, '_themed_tooltips'):
                self._themed_tooltips = {}

            # If a tooltip already exists for this widget, update and return
            existing = self._themed_tooltips.get(widget)
            if existing:
                try:
                    existing[0].setText(text)
                except Exception:
                    pass
                return

            # Create a tooltip QLabel (one per widget)
            tip = QLabel(text, self)
            tip.setObjectName('customTooltip')
            tip.setWindowFlags(Qt.ToolTip)
            tip.setAttribute(Qt.WA_TransparentForMouseEvents)
            tip.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            tip.setContentsMargins(8, 6, 8, 6)
            tip.hide()

            # FORCE light / vinyl style so all tooltips are cream + dark text (matches your preferred screenshot)
            tip_style = (
                "background-color: #fff6d9; color: #4a2c2a; "
                "border: 1px solid #c2a882; border-radius: 6px; padding: 6px;"
                "font-size: 9pt;"
            )
            tip.setStyleSheet(tip_style)

            # Store widget -> (label, duration)
            self._themed_tooltips[widget] = (tip, int(duration))

            # Install event filter to show/hide on enter/leave
            widget.installEventFilter(self)

        except Exception:
            pass    
            
    def eventFilter(self, obj, event):
            # Themed tooltip handling
            try:
                if hasattr(self, '_themed_tooltips') and (obj in self._themed_tooltips):
                    tip, duration = self._themed_tooltips[obj]
                    if event.type() == QEvent.Enter:
                        try:
                            # New logic to center the tooltip horizontally
                            obj_pos = obj.mapToGlobal(obj.rect().topLeft())
                            obj_width = obj.width()
                            tip_width = tip.sizeHint().width()
                            
                            x = obj_pos.x() + (obj_width - tip_width) / 2
                            y = obj_pos.y() + obj.height() + 6
                            
                            tip.move(int(x), int(y))
                            tip.show()
                            QTimer.singleShot(duration, lambda: tip.hide())
                        except Exception:
                            tip.show()
                        return False
                    elif event.type() == QEvent.Leave or event.type() == QEvent.FocusOut:
                        try:
                            tip.hide()
                        except Exception:
                            pass
                        return False
            except Exception:
                pass

            return super().eventFilter(obj, event)
    
    def _set_track_title(self, text):
        """Set track title with eliding support and scrolling"""
        self._track_title_full = text or ""
        self._update_track_label_elide()

    def _on_track_title_enter(self, event):
        """Handle mouse enter on track title"""
        self._start_track_title_scrolling()

    def _on_track_title_leave(self, event):
        """Handle mouse leave on track title"""
        self._stop_track_title_scrolling()

    def _start_track_title_scrolling(self):
        """Start scrolling the track title if it's too long"""
        if not hasattr(self, '_track_title_full') or not self._track_title_full:
            return
            
        # Check if text needs scrolling
        font_metrics = self.track_label.fontMetrics()
        text_width = font_metrics.horizontalAdvance(self._track_title_full)
        available_width = self.track_label.width() - 40  # Conservative margin
        
        # print(f"[TRACK DEBUG] Title width: {text_width}, Available: {available_width}")
        
        if text_width <= available_width:
            # print("[TRACK DEBUG] Title fits, no scrolling needed")
            return
        
        # Stop any existing timer safely
        if hasattr(self, '_track_scroll_timer') and self._track_scroll_timer:
            self._track_scroll_timer.stop()
            self._track_scroll_timer = None
        
        # Initialize scrolling
        self._track_scroll_timer = QTimer(self)
        self._track_scroll_pos = 0
        self._track_original_text = self._track_title_full
        
        def scroll_step():
            if not self._track_original_text:
                return
                
            text = self._track_original_text
            pos = self._track_scroll_pos
            
            # Create scrolled text
            scrolled = text[pos:] + "   " + text[:pos]
            self.track_label.setText(scrolled)
            
            self._track_scroll_pos = (pos + 1) % (len(text) + 3)
        
        self._track_scroll_timer.timeout.connect(scroll_step)
        self._track_scroll_timer.start(200)
        # print(f"[TRACK DEBUG] Started scrolling: {self._track_title_full}")

    def _stop_track_title_scrolling(self):
        """Stop scrolling and restore original text"""
        # print("[TRACK DEBUG] _stop_track_title_scrolling called")
        
        # Check timer state
        if hasattr(self, '_track_scroll_timer'):
            # print(f"[TRACK DEBUG] _track_scroll_timer exists: {self._track_scroll_timer}")
            if self._track_scroll_timer:
                # print("[TRACK DEBUG] Stopping timer...")
                self._track_scroll_timer.stop()
                # print(f"[TRACK DEBUG] Timer active after stop: {self._track_scroll_timer.isActive()}")
                self._track_scroll_timer = None
                # print("[TRACK DEBUG] Timer set to None")
            else:
               pass # print("[TRACK DEBUG] Timer was None")
        else:
            pass # print("[TRACK DEBUG] _track_scroll_timer attribute doesn't exist")
            
        if hasattr(self, '_track_title_full') and self._track_title_full:
            # print(f"[TRACK DEBUG] Restoring text: {self._track_title_full}")
            self.track_label.setText(self._track_title_full)
            self._update_track_label_elide()
            # print("[TRACK DEBUG] Text restored")
        else:
            pass # print("[TRACK DEBUG] No title to restore")
    
    def _set_track_title(self, text):
        """Set track title with eliding support"""
        self._track_title_full = text or ""
        self._update_track_label_elide()

    def _update_track_label_elide(self):
        """Update track label with proper eliding based on current width"""
        try:
            if not hasattr(self, '_track_title_full'):
                return
            
            metrics = QFontMetrics(self.track_label.font())
            available_width = self.track_label.width() - 20  # margin for safety
            if available_width <= 0:
                available_width = 200  # fallback width
            
            elided_text = metrics.elidedText(self._track_title_full, Qt.ElideRight, available_width)
            self.track_label.setText(elided_text)
        except Exception:
            # Fallback: just set the text directly
            if hasattr(self, '_track_title_full'):
                self.track_label.setText(self._track_title_full)

    def resizeEvent(self, event):
        """Handle window resize to update elided text and loading overlay position"""
        super().resizeEvent(event)
        try:
            self._update_track_label_elide()
            # Reposition loading overlay if visible
            if hasattr(self, '_loading_overlay') and self._loading_overlay.isVisible():
                self._position_loading_overlay()
            # Scale video to 40% of window width
            video_widget = self.video_frame.parent() if hasattr(self, 'video_frame') else None
            if video_widget:
                new_width = min(600, int(self.width() * 0.4))
                video_widget.setMaximumWidth(new_width)
        except Exception:
            pass

    def _font_serif(self, size, italic=False, bold=False):
        """Create a serif font with proper styling and letter spacing"""
        font = QFont(self._serif_font, size)
        font.setItalic(italic)
        if bold:
            font.setWeight(QFont.Bold)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        return font

    def _font_serif_no_size(self, italic=False, bold=False):
        """Create a serif font with styling but no fixed size (for dynamic scaling)"""
        font = QFont(self._serif_font)
        font.setItalic(italic)
        if bold:
            font.setWeight(QFont.Bold)
        font.setStyleStrategy(QFont.PreferAntialias)
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        return font
        
    def center_on_screen(self):
        screen = self.screen() if hasattr(self, "screen") and self.screen() else QApplication.primaryScreen()
        if screen:
            available = screen.availableGeometry()
            window_size = self.size()
            x = available.x() + (available.width() - window_size.width()) // 2
            y = available.y() + (available.height() - window_size.height()) // 2
            self.move(x, y)    

    def _apply_dynamic_fonts(self):
        """Apply dynamic font scaling based on application font size.

        Note: We do NOT set explicit point sizes on playlist_tree or up_next so they inherit
        QSS-driven font-size from TypographyManager (Ctrl hotkeys will scale them).
        """
        try:
            app_font = QApplication.instance().font()
            base_size = app_font.pointSizeF()
            if base_size <= 0:
                base_size = 10.0  # fallback default

            # Title font ~1.7x base, keep serif, italic, bold
            title_size = round(base_size * 1.7)
            title_font = self._font_serif_no_size(italic=True, bold=True)
            title_font.setPointSize(title_size)
            self.track_label.setFont(title_font)

            # Ensure list widgets keep serif/bold/italic but NO explicit size
            try:
                self.playlist_tree.setFont(self._font_serif_no_size(italic=True, bold=True))
            except Exception:
                pass
            try:
                if hasattr(self, 'up_next'):
                    self.up_next.setFont(self._font_serif_no_size(italic=True, bold=True))
            except Exception:
                pass

            # Update eliding after font change
            self._update_track_label_elide()

        except Exception as e:
            print(f"Dynamic font scaling failed: {e}")
            # Best-effort to keep the title readable even if we failed above
            try:
                self._update_track_label_elide()
            except Exception:
                pass

            # Update eliding after font change
            self._update_track_label_elide()
        except Exception as e:
            print(f"Dynamic font scaling failed: {e}")

            # Update eliding after font change
            self._update_track_label_elide()
        except Exception as e:
            print(f"Dynamic font scaling failed: {e}")

    def _get_scaled_serif_font(self, italic=False, bold=False):
        """Get a dynamically scaled serif font for playlist items"""
        try:
            app_font = QApplication.instance().font()
            base_size = app_font.pointSizeF()
            if base_size <= 0:
                base_size = 10.0  # fallback default
            
            list_size = round(base_size * 1.1)
            font = self._font_serif_no_size(italic=italic, bold=bold)
            font.setPointSize(list_size)
            return font
        except Exception:
            # Fallback to old method
            return self._font_serif(14, italic=italic, bold=bold)

    def _init_fonts(self):
        # Set proper defaults as specified in requirements
        self._ui_font = 'Segoe UI'
        self._serif_font = 'Georgia'
        self._jp_font = 'Noto Sans JP'
        self._jp_serif_font = 'Noto Serif JP'
        
        try:
            fonts_dir = APP_DIR / 'assets' / 'fonts'
            added_families = []
            
            # Load any fonts present under APP_DIR/assets/fonts (ttf/otf) and collect families
            if fonts_dir.exists():
                for ext in ['*.ttf', '*.otf']:
                    for font_path in fonts_dir.glob(ext):
                        try:
                            font_id = QFontDatabase.addApplicationFont(str(font_path))
                            if font_id != -1:
                                families = QFontDatabase.applicationFontFamilies(font_id)
                                added_families.extend(families)
                        except Exception:
                            pass
            
            # Get all available font families
            all_families = set(QFontDatabase.families())
            
            # Helper to pick families, favoring newly-added and "Regular" weights
            def _pick_family(base_name: str):
                # First try exact match
                if base_name in all_families:
                    return base_name
                
                # Look for families containing the base name
                candidates = []
                
                # Prefer newly added families first
                for family in added_families:
                    if base_name.lower() in family.lower():
                        candidates.append(family)
                
                # If not found in added families, search all families
                if not candidates:
                    for family in all_families:
                        if base_name.lower() in family.lower():
                            candidates.append(family)
                
                if candidates:
                    # Sort by preference: Regular weights first, then shorter names
                    candidates.sort(key=lambda s: (
                        'regular' not in s.lower(),  # Regular weights first
                        len(s)  # Shorter names preferred
                    ))
                    return candidates[0]
                
                return None
            
            # Ensure Japanese fonts are registered explicitly if present
            # Try to load Noto Sans JP
            noto_sans_jp = _pick_family('Noto Sans JP')
            if noto_sans_jp:
                self._jp_font = noto_sans_jp
            
            # Try to load Noto Serif JP
            noto_serif_jp = _pick_family('Noto Serif JP')
            if noto_serif_jp:
                self._jp_serif_font = noto_serif_jp
            
            # Ensure Lora is selected for serif font even if Inter is unavailable
            lora_font = _pick_family('Lora')
            
            # If Lora not found, call _bootstrap_fonts() and retry once
            if not lora_font:
                try:
                    self._bootstrap_fonts()
                    # Reload families after bootstrap
                    added_families = []
                    if fonts_dir.exists():
                        for ext in ['*.ttf', '*.otf']:
                            for font_path in fonts_dir.glob(ext):
                                try:
                                    font_id = QFontDatabase.addApplicationFont(str(font_path))
                                    if font_id != -1:
                                        families = QFontDatabase.applicationFontFamilies(font_id)
                                        added_families.extend(families)
                                except Exception:
                                    pass
                    all_families = set(QFontDatabase.families())
                    lora_font = _pick_family('Lora')
                except Exception:
                    pass
            
            # Set Lora for serif if found
            if lora_font:
                self._serif_font = lora_font
            
            # Pick Inter if present for UI font; otherwise leave Segoe UI
            inter_font = _pick_family('Inter')
            if inter_font:
                self._ui_font = inter_font
            
            # Set QFont substitutions so JP glyphs fall back correctly
            try:
                QFont.insertSubstitution(self._serif_font, self._jp_serif_font)
                QFont.insertSubstitution(self._ui_font, self._jp_font)
            except Exception:
                pass
            
            # Set QApplication font to UI font at size 14
            try:
                app_font = QFont(self._ui_font, 14)
                QApplication.instance().setFont(app_font)
            except Exception:
                pass
                
        except Exception:
            pass

    def _bootstrap_fonts(self):
        try:
            if not HAVE_REQUESTS:
                print("Font bootstrap skipped: requests not available")
                return
            fonts_dir = APP_DIR / 'assets' / 'fonts'
            fonts_dir.mkdir(parents=True, exist_ok=True)
            
            # Required fonts for serif typography
            required_targets = [
                ("Lora[wght].ttf", "https://github.com/google/fonts/raw/main/ofl/lora/Lora[wght].ttf"),
                ("Lora-Italic[wght].ttf", "https://github.com/google/fonts/raw/main/ofl/lora/Lora-Italic[wght].ttf"),
                ("NotoSerifJP[wght].ttf", "https://github.com/google/fonts/raw/main/ofl/notoserifjp/NotoSerifJP[wght].ttf"),
                ("NotoSansJP[wght].ttf", "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP[wght].ttf"),
            ]
            
            # Optional fonts for UI
            optional_targets = [
                ("Inter[opsz,wght].ttf", "https://github.com/google/fonts/raw/main/ofl/inter/Inter[opsz,wght].ttf"),
            ]
            
            # Download required fonts first
            for fname, url in required_targets:
                path = fonts_dir / fname
                if not path.exists():
                    print(f"Downloading font: {fname} ...")
                    r = requests.get(url, timeout=20)
                    if r.status_code == 200 and r.content:
                        with open(path, 'wb') as f:
                            f.write(r.content)
                        rid = QFontDatabase.addApplicationFont(str(path))
                        fams_for = QFontDatabase.applicationFontFamilies(rid) if rid != -1 else []
                        print(f"✓ Installed {fname}: {list(fams_for) or 'n/a'}")
                    else:
                        print(f"✗ Failed to download {fname}: HTTP {r.status_code}")
            
            # Download optional fonts (failures are not critical)
            for fname, url in optional_targets:
                path = fonts_dir / fname
                if not path.exists():
                    print(f"Downloading optional font: {fname} ...")
                    try:
                        r = requests.get(url, timeout=20)
                        if r.status_code == 200 and r.content:
                            with open(path, 'wb') as f:
                                f.write(r.content)
                            rid = QFontDatabase.addApplicationFont(str(path))
                            fams_for = QFontDatabase.applicationFontFamilies(rid) if rid != -1 else []
                            print(f"✓ Installed optional {fname}: {list(fams_for) or 'n/a'}")
                        else:
                            print(f"⚠ Optional font {fname} not available: HTTP {r.status_code}")
                    except Exception as e:
                        print(f"⚠ Optional font {fname} download failed: {e}")
                        
        except Exception as e:
            print(f"Font bootstrap error: {e}")

    def _clear_background_pattern(self):
        try:
            cw = self.centralWidget()
            if cw:
                pal = cw.palette()
                pal.setBrush(cw.backgroundRole(), QBrush())
                cw.setPalette(pal)
                cw.setAutoFillBackground(False)
        except Exception:
            pass

    def _apply_vinyl_background_pattern(self):
        try:
            if 'QSvgRenderer' in globals() and QSvgRenderer is not None:
                svg_path = str(APP_DIR / 'vinyl_pattern.svg')
                renderer = QSvgRenderer(svg_path)
                tile = QPixmap(160, 160)
                tile.fill(Qt.transparent)
                p = QPainter(tile)
                renderer.render(p)
                p.end()
                pal = self.centralWidget().palette()
                pal.setBrush(self.centralWidget().backgroundRole(), QBrush(tile))
                self.centralWidget().setPalette(pal)
                self.centralWidget().setAutoFillBackground(True)
            else:
                # Fallback: clear pattern (no SVG support)
                self._clear_background_pattern()
        except Exception as e:
            print(f"Vinyl bg pattern failed: {e}")

    def _apply_dark_theme(self):
        style = """
        QMainWindow, QDialog { background-color: #1e1e1e; color: #f3f3f3; font-family: '{self._ui_font}'; }
        #titleLabel { color: #f3f3f3; font-size: 20px; font-weight: bold; font-style: italic; font-family: '{self._serif_font}'; }
        #scopeDropdown {
            background-color: #2a2a2a;
            color: #f3f3f3;
            border: 1px solid #4a4a4a;
            padding: 4px 8px;
            border-radius: 6px;
            font-family: '{self._ui_font}';
            font-size: 13px;
        }
        #scopeDropdown::drop-down {
            border: none;
            width: 20px;
        }
        #scopeDropdown::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #b3b3b3;
            margin-right: 5px;
        }
        #scopeDropdown:hover {
            background-color: #3a3a3a;
            border-color: #5a5a5a;
        }
        #scopeDropdown QAbstractItemView {
            background-color: #2a2a2a;
            color: #f3f3f3;
            selection-background-color: #e76f51;
            selection-color: #f3f3f3;
            border: 1px solid #4a4a4a;
        }        
        #settingsBtn { background: transparent; color: #b3b3b3; font-size: 18px; border: none; padding: 2px 6px; min-width: 32px; min-height: 28px; border-radius: 6px; }
        #settingsBtn:hover { background-color: rgba(255,255,255,0.08); color: #f3f3f3; }
        #settingsBtn:pressed { background-color: rgba(255,255,255,0.2); }
        #scopeChip { background-color: rgba(48,48,48,0.9); color: #f3f3f3; border: 1px solid #4a4a4a; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-left: 8px; }
        #statsBadge { background-color: transparent; color: #b3b3b3; border: 1px solid #4a4a4a; padding: 4px 12px; margin-left: 8px; margin-right: 8px; border-radius: 10px; font-size: 12px; }
        #sidebar { background-color: rgba(30, 30, 30, 0.85); border: 1px solid rgba(80, 80, 80, 0.5); border-radius: 8px; padding: 16px; }
        #addBtn { 
                background-color: #e76f51; 
                color: #f3f3f3; 
                border: none; 
                padding: 8px 12px; 
                border-radius: 8px; 
                font-weight: bold; 
                margin-bottom: 8px; 
                text-align: left;
                qproperty-text: "  + Add Media";
            }
        #addBtn::menu-indicator {
                image: url(icons/chevron-down-light.svg);
                subcontrol-position: right top;
                subcontrol-origin: padding;
                right: 10px;
                top: 2px;
            }
        #addBtn:hover { background-color: #d86a4a; }
        #addBtn:pressed { background-color: #d1603f; }
        #miniBtn { background: transparent; color: #b3b3b3; border: none; font-size: 16px; }
        #miniBtn:hover { color: #ffffff; }
        #miniBtn:pressed { color: #888888; }
        #playlistTree { background-color: transparent; border: none; color: #f3f3f3; font-family: '{self._serif_font}'; alternate-background-color: #2a2a2a; margin-left: 8px; }
        #playlistTree::item {
            min-height: 32px;
            height: 32px;
            padding: 8px 16px 8px 12px;
            color: #c9c9c9;
        }
        /* NEW: Add this rule for the playing item border */
        #playlistTree::item[playing="true"] {
            border-left: 3px solid #1DB954;  /* Spotify green */
            padding-left: 9px;               /* Compensate for border width */
            background-color: rgba(29, 185, 84, 0.1);  /* Subtle background tint */
        }
        #playlistTree::item:!selected {
            border-bottom: 1px solid #3a3a3a;
        }
        #playlistTree::item:hover { background-color: rgba(255, 85, 85, 0.15); }
        #playlistTree::item:selected { background-color: #e76f51; color: #ffffff; }
        #playlistTree::item[loading="true"] {
            color: #888888;
            font-style: italic;
        }
        #videoWidget { background-color: #000; border-radius: 8px; border: 10px solid #1e1e1e; }
        #playPauseBtn { background-color: #e76f51; color: #f3f3f3; font-size: 26px; border: none; border-radius: 30px; width: 60px; height: 60px; padding: 0px; }
        #playPauseBtn:hover { background-color: #d86a4a; }
        #playPauseBtn:pressed { background-color: #d1603f; }
        #controlBtn { background: transparent; color: #b3b3b3; font-size: 20px; border: none; border-radius: 20px; width: 40px; height: 40px; padding: 0px; }
        #controlBtn:hover { background-color: rgba(255,255,255,0.1); color: #f3f3f3; }
        #controlBtn:pressed { background-color: rgba(255,255,255,0.2); }
        QSlider::groove:horizontal { height: 6px; background-color: #4a4a4a; border-radius: 3px; }
        QSlider::handle:horizontal { 
            width: 18px; 
            height: 18px; 
            background-color: #d0d0d0; 
            border-radius: 9px; 
            margin: -6px 0; 
        }
        QSlider::sub-page:horizontal { background-color: #e76f51; border-radius: 3px; }
        #timeLabel, #durLabel { font-family: '{self._ui_font}'; font-size: 13px; color: #b3b3b3; }
        #silenceIndicator { color: #e76f51; font-size: 18px; margin: 0 8px; padding-bottom: 3px; }
        #upNext::item { 
            min-height: 26px;        /* Slightly smaller */
            height: 26px; 
            padding: 5px 8px;        /* Tighter padding */
            line-height: 1.3;        /* Add consistent line height */
        }
        #upNext::item:hover { background-color: rgba(255, 85, 85, 0.08); }
        #upNext::item:selected { background-color: #e76f51; color: #f3f3f3; }
        #upNext { 
            background-color: #2a2a2a; 
            border: 1px solid #4a4a4a; 
            border-radius: 6px; 
            font-family: '{self._serif_font}'; 
            alternate-background-color: #353535;
        }
        #upNextHeader { background-color: rgba(48,48,48,0.9); color: #f3f3f3; border: 1px solid #4a4a4a; border-radius: 6px; padding: 4px 8px; text-align:left; }
        #upNextHeader:hover { background-color: #2a2a2a; }
        #upNextHeader:pressed { background-color: #1e1e1e; }
        #upNext { 
            background-color: #2a2a2a; 
            border: 1px solid #4a4a4a; 
            border-radius: 6px; 
            font-family: '{self._serif_font}'; 
            alternate-background-color: #353535;
            color: #d0d0d0;
        }
        QProgressBar { background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 4px; text-align: center; color: #f3f3f3; }
        QProgressBar::chunk { background-color: #e76f51; border-radius: 4px; }
        QStatusBar { color: #f3f3f3; }
        QMenu { background-color: #2a2a2a; color: #f3f3f3; border: 1px solid #4a4a4a; font-size: 13px; }
        QMenu::item { padding: 6px 12px; }
        QMenu::item:selected { background-color: #e76f51; color: #f3f3f3; }
        QToolTip { background-color: #1e1e1e; color: #f3f3f3; border: 1px solid #3a3a3a; padding: 4px 8px; border-radius: 6px; font-size: 9pt; }
        QScrollBar:vertical { background: transparent; width: 12px; margin: 0px; }
        QScrollBar::handle:vertical { background: #4a4a4a; min-height: 24px; border-radius: 6px; }
        QScrollBar::handle:vertical:hover { background: #5a5a5a; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { background: transparent; height: 12px; margin: 0px; }
        QScrollBar::handle:horizontal { background: #4a4a4a; min-width: 24px; border-radius: 6px; }
        QScrollBar::handle:horizontal:hover { background: #5a5a5a; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QTabWidget::pane { border: 1px solid #4a4a4a; border-radius: 6px; }
        QTabBar::tab { background-color: rgba(48,48,48,0.9); color: #f3f3f3; padding: 6px 10px; border: 1px solid #4a4a4a; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
        QTabBar::tab:selected { background-color: #2a2a2a; color: #f3f3f3; }
        QTabBar::tab:hover { background-color: #2a2a2a; }
        #timeLabel, #durLabel { font-family: '{self._ui_font}'; font-size: 13px; color: #b3b3b3; }
        QLineEdit#searchBar { background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 6px; padding: 4px 8px; margin: 8px 0; color: #f3f3f3; selection-background-color: #e76f51; }
        #addMediaBtn {
            background-color: #e76f51;
            color: #f3f3f3;
            border: none;
            border-radius: 8px;
            padding: 0 18px;
            font-weight: bold;
            font-size: 1.1em;
            text-align: left;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        #addMediaBtn:hover {
            background-color: #d86a4a;
        }
        #addMediaBtn:pressed {
            background-color: #d1603f;
            opacity: 0.8;
        }
        #addMediaBtn::menu-indicator {
        image: none;
        width: 0;
        height: 0;
        }
        QPushButton:focus { outline: none; }
        #playPauseBtn:focus {
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 30px;
            padding: 0px;
        }    
        QHBoxLayout#top {
        border-bottom: 1.5px solid #3a3a3a;
        padding-bottom: 6px;
        margin-bottom: 8px;
        }
        #playlistTree::item:selected, #playlistTree::item:focus {
        background-color: #e76f51;
        color: #f3f3f3;
        font-weight: bold;
        }
        #libraryHeader {
            background: linear-gradient(135deg, #e76f51 0%, #d86a4a 100%);
            color: #b3b3b3;
            font-weight: 700;
            padding: 8px 16px 8px 20px;
            min-height: 32px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            font-family: '{self._serif_font}';
        }
        #emptyStateLabel {
            color: #b3b3b3;
            font-size: 14px;
            font-family: '{self._ui_font}';
        }
        #noTrackPlayingLabel {
            color: #b3b3b3;
            font-size: 14px;
            font-family: '{self._ui_font}';
            margin-top: 10px;
        }
                #addMediaContainer {
            max-width: 220px;
        }
        #addMediaMain {
            background-color: #e76f51;
            color: #f3f3f3;
            border: none;
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;
            padding: 8px 16px;
            font-weight: bold;
            text-align: center;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        }
        #addMediaMain:hover {
            background-color: #d86a4a;
        }
        #addMediaMain:pressed {
            background-color: #d1603f;
        }
        #addMediaDropdown {
            background-color: #d86a4a;
            color: #f3f3f3;
            border: none;
            border-left: 1px solid #c85f47;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            font-size: 11px;
            font-weight: bold;
        }
        #addMediaDropdown:hover {
            background-color: #c85f47;
        }
        #addMediaDropdown:pressed {
            background-color: #b8543e;
        }
        """
        style = style.replace("{self._ui_font}", self._ui_font).replace("{self._serif_font}", self._serif_font)
        self.setStyleSheet(style)

        try:
            eff = QGraphicsDropShadowEffect(self.video_frame)
            eff.setBlurRadius(20)
            eff.setOffset(0, 0)
            eff.setColor(QColor(0, 0, 0, 160))
            self.video_frame.setGraphicsEffect(eff)
        except Exception:
            pass

        # Apply dark background pattern by drawing it programmatically
        try:
            bg = self.centralWidget()
            if bg:
                # FIRST: Clear any existing styling completely
                bg.setStyleSheet("#bgRoot { background: none; border-image: none; }")
                bg.setAutoFillBackground(False)
                
                # Clear existing palette
                pal = bg.palette()
                pal.setBrush(bg.backgroundRole(), QBrush())
                bg.setPalette(pal)
                
                # NOW: Apply dark theme background
                # Define colors
                background_color = QColor("#1e1e1e")
                pattern_color = QColor("#242424") # The subtle gray for the stars

                # Create a pixmap for one tile of the pattern
                tile_size = 40
                tile = QPixmap(tile_size, tile_size)
                tile.fill(background_color)

                # Draw the star/cross pattern onto the tile
                p = QPainter(tile)
                p.setPen(QPen(pattern_color, 1.5))
                center = tile_size / 2
                length = tile_size / 8
                # Draw horizontal and vertical lines for the plus shape
                p.drawLine(int(center - length), int(center), int(center + length), int(center))
                p.drawLine(int(center), int(center - length), int(center), int(center + length))
                p.end()

                # Set the tiled pixmap as the background
                pal = bg.palette()
                pal.setBrush(QPalette.Window, QBrush(tile))
                bg.setPalette(pal)
                bg.setAutoFillBackground(True)

        except Exception as e:
            logger.error(f"Failed to apply dark background pattern: {e}")
            bg = self.centralWidget()
            if bg:
                bg.setStyleSheet("#bgRoot { background-color: #1e1e1e; }")

        self._update_widget_themes()
        self._setup_button_animations()

        # FORCE: Ensure all widgets are properly updated after theme change
        try:
            # Force style refresh on main components
            if hasattr(self, 'video_frame'):
                self.video_frame.update()
            if hasattr(self, 'track_label'):
                self.track_label.update()
            if hasattr(self, 'progress'):
                self.progress.update()
            
            # Update main window
            self.update()
            
        except Exception:
            pass

    def _set_background_pattern(self, dark_theme=False):
        # Read the SVG content
        try:
            with open("background_pattern.svg", "r") as f:
                svg_content = f.read()
        except FileNotFoundError:
            print("background_pattern.svg not found.")
            return

        if dark_theme:
            # Replace light colors with dark theme colors
            # Assuming original SVG has light gray for background and white for stars
            svg_content = svg_content.replace("#F3F3F3", "#1e1e1e") # Main background color
            svg_content = svg_content.replace("#FFFFFF", "#2a2a2a") # Star/cross pattern color
            svg_content = svg_content.replace("#E0E0E0", "#2a2a2a") # Another potential light gray
        else:
            # Revert to original light theme colors (if needed, otherwise can be default)
            svg_content = svg_content.replace("#1e1e1e", "#F3F3F3")
            svg_content = svg_content.replace("#2a2a2a", "#FFFFFF")
            
        # Create a QPixmap from the modified SVG
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        # Set the pixmap as the background for the central widget
        palette = self.central_widget.palette()
        palette.setBrush(QPalette.Background, QBrush(pixmap))
        self.central_widget.setAutoFillBackground(True)
        self.central_widget.setPalette(palette)
        
    def _apply_vinyl_theme(self):
        style = """
        QMainWindow, QDialog { background-color: #f3ead3; color: #4a2c2a; font-family: '{self._ui_font}'; }
        #titleLabel { color: #4a2c2a; font-size: 20px; font-weight: bold; font-style: italic; font-family: '{self._serif_font}'; }
        #scopeDropdown {
            background-color: #f0e7cf;
            color: #4a2c2a;
            border: 1px solid #c2a882;
            padding: 4px 8px;
            border-radius: 6px;
            font-family: '{self._ui_font}';
            font-size: 13px;
        }
        #scopeDropdown::drop-down {
            border: none;
            width: 20px;
        }
        #scopeDropdown::down-arrow {
            image: url(icons/chevron-down-dark.svg);
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #654321;
            margin-right: 5px;
        }
        #scopeDropdown:hover {
            background-color: #e9e0c8;
            border-color: #b6916d;
        }
        #scopeDropdown QAbstractItemView {
            background-color: #faf3e0;
            color: #4a2c2a;
            selection-background-color: #e76f51;
            selection-color: #f3ead3;
            border: 1px solid #c2a882;
        }        
        #settingsBtn { background: transparent; color: #654321; font-size: 18px; border: none; padding: 2px 6px; min-width: 32px; min-height: 28px; border-radius: 6px; }
        #settingsBtn:hover { background-color: rgba(0,0,0,0.03); color: #4a2c2a; }
        #settingsBtn:pressed { background-color: rgba(0,0,0,0.08); }
        #scopeChip { background-color: rgba(250,243,224,0.9); color: #4a2c2a; border: 1px solid #c2a882; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-left: 8px; }
        #statsBadge { background-color: transparent; color: #654321; border: 1px solid #c2a882; padding: 4px 12px; margin-left: 8px; margin-right: 8px; border-radius: 10px; font-size: 12px; }
        #sidebar { background-color: rgba(250, 243, 224, 0.85); border: 1px solid rgba(194, 168, 130, 0.5); border-radius: 8px; padding: 16px; }
        #addBtn { 
                background-color: #e76f51; 
                color: #f3ead3; 
                border: none; 
                padding: 8px 12px; 
                border-radius: 8px; 
                font-weight: bold; 
                margin-bottom: 8px; 
                text-align: left;
                qproperty-text: "  + Add Media";
            }
        #addBtn::menu-indicator {
                image: url(icons/chevron-down-dark.svg);
                subcontrol-position: right top;
                subcontrol-origin: padding;
                right: 10px;
                top: 2px;
            }
        #addBtn:hover { background-color: #d86a4a; }
        #addBtn:pressed { background-color: #d1603f; }
        #miniBtn { background: transparent; color: #654321; border: none; font-size: 16px; }
        #miniBtn:hover { color: #4a2c2a; }
        #miniBtn:pressed { color: #654321; }
        #playlistTree { background-color: transparent; border: none; color: #4a2c2a; font-family: '{self._serif_font}'; alternate-background-color: #f0e7cf; margin-left: 8px; }
        #playlistTree::item {
            min-height: 30px;        /* Reduced from 32px */
            height: 30px;            /* Reduced from 32px */
            padding: 6px 12px 6px 8px;  /* Tighter: 6px vertical, 8px left (was 8px, 12px) */
            color: #3d2318;          /* Warmer brown (was #3b2d1a) */
            line-height: 1.3;        /* Add this line for tighter text */
        }

        /* NEW: Add this rule for the playing item border */
        #playlistTree::item[playing="true"] {
            border-left: 3px solid #e76f51;  /* Your orange accent */
            padding-left: 9px;               /* Compensate for border width */
            background-color: rgba(231, 111, 81, 0.1);  /* Subtle background tint */
        }

        #playlistTree::item:!selected {
            border-bottom: 1px solid #e5d5b8;
        }

        #playlistTree::item:selected {
            background-color: #e76f51;
            color: #fff6d9;
            font-weight: bold;
        }
        #playlistTree::item:hover { background-color: rgba(239, 227, 200, 0.5); }
        #playlistTree::item:selected { background-color: #e76f51; color: #f3ead3; }
        #playlistTree::item[loading="true"] {
            color: #888888;
            font-style: italic;
        }
        #videoWidget { background-color: #000; border-radius: 8px; border: 10px solid #faf3e0; }
        /* REMOVED: #trackLabel styling - let _update_widget_themes() handle it */
        #playPauseBtn { background-color: #e76f51; color: #f3ead3; font-size: 26px; border: none; border-radius: 30px; width: 60px; height: 60px; padding: 0px; }
        #playPauseBtn:hover {
        background-color: #d86a4a;
    }
        #playPauseBtn:pressed { background-color: #d1603f; }
        #controlBtn { background: transparent; color: #654321; font-size: 20px; border: none; border-radius: 20px; width: 40px; height: 40px; padding: 0px; }
        #controlBtn:hover { background-color: rgba(0,0,0,0.04); color: #4a2c2a; }
        #controlBtn:pressed { background-color: rgba(0,0,0,0.08); }
        QSlider::groove:horizontal { height: 6px; background-color: #c2a882; border-radius: 3px; }
        QSlider::handle:horizontal { 
            width: 18px; 
            height: 18px; 
            background-color: #4a2c2a; 
            border-radius: 9px; 
            margin: -6px 0; 
        }
        QSlider::sub-page:horizontal { background-color: #e76f51; border-radius: 3px; }
        #timeLabel, #durLabel { font-family: '{self._ui_font}'; font-size: 13px; color: #654321; }
        #silenceIndicator { color: #b00000; font-size: 18px; margin: 0 8px; padding-bottom: 3px; }
        #upNext::item { min-height: 28px; height: 28px; padding: 6px 12px; }
        #upNext::item:hover { background-color: rgba(239, 227, 200, 0.4); }
        #upNext::item:selected { background-color: #e76f51; color: #f3ead3; }
        #upNextHeader { 
            background-color: rgba(250,243,224,0.9); 
            color: #4a2c2a; 
            border: 1px solid rgba(194, 168, 130, 0.3); 
            border-radius: 6px; 
            padding: 4px 8px; 
            text-align:left; 
        }
        #upNextHeader:hover { background-color: #f0e7cf; }
        #upNextHeader:pressed { background-color: #e9e0c8; }
        #upNext { 
            background-color: #faf3e0; 
            border: 1px solid rgba(194, 168, 130, 0.3); 
            border-radius: 6px; 
            font-family: '{self._serif_font}'; 
            alternate-background-color: #f0e7cf;
        }
        QProgressBar { background-color: #f0e7cf; border: 1px solid #c2a882; border-radius: 4px; text-align: center; color: #4a2c2a; }
        QProgressBar::chunk { background-color: #e76f51; border-radius: 4px; }
        QStatusBar { color: #4a2c2a; }
        QMenu { background-color: #faf3e0; color: #4a2c2a; border: 1px solid #c2a882; font-size: 13px; }
        QMenu::item { padding: 6px 12px; }
        QMenu::item:selected { background-color: #e76f51; color: #f3ead3; }
        QToolTip { background-color: #fff6d9; color: #4a2c2a; border: 1px solid #c2a882; padding: 4px 8px; border-radius: 6px; font-size: 9pt; }
        QScrollBar:vertical { background: transparent; width: 12px; margin: 0px; }
        QScrollBar::handle:vertical { background: #c2a882; min-height: 24px; border-radius: 6px; }
        QScrollBar::handle:vertical:hover { background: #b6916d; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { background: transparent; height: 12px; margin: 0px; }
        QScrollBar::handle:horizontal { background: #c2a882; min-width: 24px; border-radius: 6px; }
        QScrollBar::handle:horizontal:hover { background: #b6916d; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QTabWidget::pane { border: 1px solid #c2a882; border-radius: 6px; }
        QTabBar::tab { background-color: rgba(250,243,224,0.9); color: #4a2c2a; padding: 6px 10px; border: 1px solid #c2a882; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
        QTabBar::tab:selected { background-color: #f0e7cf; color: #4a2c2a; }
        QTabBar::tab:hover { background-color: #f0e7cf; }
        #upNext { font-family: '{self._serif_font}'; alternate-background-color: #f0e7cf; }
        #timeLabel, #durLabel { font-family: '{self._ui_font}'; font-size: 13px; color: #654321; }
        QLineEdit#searchBar { 
            background-color: #f0e7cf; 
            border: 1px solid #c2a882; 
            border-radius: 6px; 
            padding: 6px 10px;              /* Slightly more comfortable */
            margin: 10px 0;                 /* More breathing room */
            color: #3d2318;                 /* Warmer text color */
            selection-background-color: #e76f51;
            font-size: 13px;                /* Ensure readable size */
        }
        /* REMOVED: #emptyStateIcon, #emptyStateHeading, #emptyStateSubheading - let _update_widget_themes() handle them */
        #addMediaBtn {
        background-color: #e76f51;
        color: #f3ead3;
        border: none;
        border-radius: 8px;
        padding: 0 18px;
        font-weight: bold;
        font-size: 1.1em;
        text-align: left;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    #addMediaBtn:hover {
        background-color: #d86a4a;
    }
    #addMediaBtn:pressed {
        background-color: #d1603f;
        opacity: 0.8;
    }
    #addMediaBtn::menu-indicator {
    image: none;
    width: 0;
    height: 0;
    }
    /* Focus styling: keep keyboard-accessibility but hide default outline */
    QPushButton:focus { outline: none; }
    /* Themed focus ring for play/pause in vinyl theme (soft warm accent) */
    #playPauseBtn:focus {
        border: 2px solid rgba(231,111,81,0.18); /* soft e76f51 tint */
        border-radius: 30px;
        padding: 0px;
    }    
    QHBoxLayout#top {
    border-bottom: 1.5px solid #e5d5b8;
    padding-bottom: 6px;
    margin-bottom: 8px;
    }
    #playlistTree::item:selected, #playlistTree::item:focus {
    background-color: #e76f51;
    color: #fff6d9;
    font-weight: bold;
    }
    #libraryHeader {
        background: #4a2c2a;
        color: #f3ead3;
        font-weight: 600;
        padding: 12px 16px 12px 20px;  /* Increased from 8px to 12px vertical */
        min-height: 36px;              /* Increased from 32px to 36px */
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-family: '{self._serif_font}';
        margin-bottom: 4px;            /* Add space below header */
    }
    #addMediaContainer {
        max-width: 220px;
    }
    #addMediaMain {
        background-color: #e76f51;
        color: #f3ead3;
        border: none;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
        border-top-right-radius: 0px;
        border-bottom-right-radius: 0px;
        padding: 8px 16px;
        font-weight: bold;
        text-align: center;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    #addMediaMain:hover {
        background-color: #d86a4a;
    }
    #addMediaMain:pressed {
        background-color: #d1603f;
    }
    #addMediaDropdown {
        background-color: #d86a4a;
        color: #f3ead3;
        border: none;
        border-left: 1px solid #c85f47;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        font-size: 11px;
        font-weight: bold;
    }
    #addMediaDropdown:hover {
        background-color: #c85f47;
    }
    #addMediaDropdown:pressed {
        background-color: #b8543e;
    }
    """
        style = style.replace("{self._ui_font}", self._ui_font).replace("{self._serif_font}", self._serif_font)
        self.setStyleSheet(style)
        try:
            eff = QGraphicsDropShadowEffect(self.video_frame)
            eff.setBlurRadius(25)
            eff.setOffset(0, 0)
            eff.setColor(QColor(0, 0, 0, 110))
            self.video_frame.setGraphicsEffect(eff)
        except Exception:
            pass
        # Apply tiled vinyl background on central widget and hide scope chip to match iconic mock
        try:
            bg = self.centralWidget()
            if bg:
                path = str(APP_DIR / 'vinyl_pattern.svg').replace('\\','/')
                bg.setStyleSheet(f"#bgRoot {{ background-color: #f3ead3; border-image: url('{path}') 0 0 0 0 repeat repeat; }}")
                bg.setAutoFillBackground(True)
        except Exception:
            pass
        try:
            if hasattr(self, 'scope_label'):
                self.scope_dropdown.setVisible(False)
        except Exception:
            pass 
        # Call _update_widget_themes() AFTER setting the main stylesheet
        self._update_widget_themes()
        self._setup_button_animations()
            
    def _update_widget_themes(self):
            """Force-apply theme-specific styles and icons to widgets."""
            try:
                is_dark = self.theme == 'dark'

                if is_dark:
                    # Dark theme colors and base icons
                    text_color, sub_color, icon_color = "#e0e0e0", "#b3b3b3", "#4a4a4a"
                    prev_icon, next_icon = self.prev_icon_dark, self.next_icon_dark
                    # CORRECTED: Assign the correct 'on' and 'off' icons for dark theme
                    shuffle_icon_on, shuffle_icon_off = self.shuffle_on_icon_dark, self.shuffle_icon_dark
                    repeat_icon_on, repeat_icon_off = self.repeat_on_icon_dark, self.repeat_icon_dark
                else:
                    # Vinyl theme colors and base icons
                    text_color, sub_color, icon_color = "#4a2c2a", "#654321", "#c2a882"
                    prev_icon, next_icon = self.prev_icon_vinyl, self.next_icon_vinyl
                    # CORRECTED: Assign the correct 'on' and 'off' icons for vinyl theme
                    shuffle_icon_on, shuffle_icon_off = self.shuffle_on_icon_vinyl, self.shuffle_icon_vinyl
                    repeat_icon_on, repeat_icon_off = self.repeat_on_icon_vinyl, self.repeat_icon_vinyl

                # ADD THIS BLOCK FOR VOLUME ICON
                # Update volume icon color based on theme
                try:
                    svg_path = APP_DIR / 'icons' / 'volume.svg'
                    if svg_path.exists():
                        color = "#d0d0d0" if is_dark else "#4a2c2a"
                        pm = _render_svg_tinted(str(svg_path), self.icon_size, color)
                        if not pm.isNull():
                            self.volume_icon_label.setPixmap(pm)
                except Exception:
                    pass    

                # Apply text colors to labels
                if hasattr(self, 'track_label'):
                    self.track_label.setStyleSheet(f"color: {text_color}; background: transparent; margin-top: 14px; margin-bottom: 12px; letter-spacing: 0.5px; font-weight: bold; font-style: italic; font-family: '{self._serif_font}';")
                if hasattr(self, 'empty_state_heading'):
                    self.empty_state_heading.setStyleSheet(f"color: {text_color}; font-family: '{self._serif_font}'; font-size: 15px; font-weight: bold;")
                if hasattr(self, 'empty_state_subheading'):
                    self.empty_state_subheading.setStyleSheet(f"color: {sub_color}; font-size: 13px;")
                if hasattr(self, 'empty_state_widget'):
                    empty_icon = self.empty_state_widget.findChild(QLabel, 'emptyStateIcon')
                    if empty_icon:
                        empty_icon.setStyleSheet(f"color: {icon_color}; font-size: 48px; padding-bottom: 10px;")

                # Apply standard control icons
                for btn, icon in [(self.prev_btn, prev_icon), (self.next_btn, next_icon)]:
                    btn.setIcon(icon)
                    btn.setText("")

                # Set play/pause icon based on playback state
                if self._is_playing():
                    self.play_pause_btn.setIcon(self._pause_icon_normal)
                else:
                    self.play_pause_btn.setIcon(self._play_icon_normal)
                self.play_pause_btn.setText("")

                # --- LOGIC for Shuffle/Repeat icons ---
                # Set the shuffle icon based on its on/off state
                self.shuffle_btn.setIcon(shuffle_icon_on if self.shuffle_mode else shuffle_icon_off)

                # Set the repeat icon based on its on/off state
                self.repeat_btn.setIcon(repeat_icon_on if self.repeat_mode else repeat_icon_off)

                # Update button styling to show active state
                if self.repeat_mode:
                    self.repeat_btn.setStyleSheet("background-color: rgba(231, 111, 81, 0.3); border-radius: 20px;")
                else:
                    self.repeat_btn.setStyleSheet("")

                if self.shuffle_mode:
                    self.shuffle_btn.setStyleSheet("background-color: rgba(231, 111, 81, 0.3); border-radius: 20px;")
                else:
                    self.shuffle_btn.setStyleSheet("")

            except Exception as e:
                logger.warning(f"Failed to force-apply theme to widgets: {e}")

    def _play_all_library(self):
        """Plays the entire library from the beginning."""
        if self.playlist:
            self.status.showMessage("Playing all media in library...", 3000)
            self.play_scope = None
            self._update_scope_label()
            self.current_index = 0
            self.play_current()                

    def toggle_theme(self):
        self.theme = 'vinyl' if getattr(self, 'theme', 'dark') != 'vinyl' else 'dark'
        
        # IMPORTANT: Clear any existing background styling first
        try:
            bg = self.centralWidget()
            if bg:
                # Clear any previous background styling
                bg.setStyleSheet("#bgRoot { background: none; border-image: none; }")
                bg.setAutoFillBackground(False)
                
                # Clear any existing palette background
                pal = bg.palette()
                pal.setBrush(bg.backgroundRole(), QBrush())
                bg.setPalette(pal)
        except Exception:
            pass
        
        # Apply the new theme
        if self.theme == 'vinyl':
            self._apply_vinyl_theme()
        else:
            self._apply_dark_theme()
        
        # Apply dynamic font scaling after theme change
        self._apply_dynamic_fonts()

        # Update playlist tree chevron style for new theme
        if hasattr(self, "playlist_tree"):
            if getattr(self, "theme", "dark") == "dark":
                self.playlist_tree.setStyle(LightChevronTreeStyle(color="#e0e0e0"))
            else:
                # Remove custom style to use native Qt arrows in vinyl
                self.playlist_tree.setStyle(None)
                # Force a style refresh
                self.playlist_tree.style().unpolish(self.playlist_tree)
                self.playlist_tree.style().polish(self.playlist_tree)
        
        # Force a complete repaint to ensure all styling takes effect
        try:
            self.update()
            self.centralWidget().update()
            if hasattr(self, 'video_frame'):
                self.video_frame.update()
        except Exception:
            pass
        
        try:
            if hasattr(self, 'theme_btn') and self.theme_btn:
                self.theme_btn.setToolTip("Toggle Theme")
        except Exception:
            pass
        self._save_settings()
        self.status.showMessage(f"Theme toggled to {self.theme.capitalize()}", 3000)
    # mpv
    def _init_mpv(self):
        try:
            self.mpv = MPV(
                wid=str(int(self.video_frame.winId())),
                ytdl=True,
                hwdec='no',
                osc=False
            )
            
            # Add padding around video content (optional)
            try:
                pass  # Keep the try block valid, even if empty
            except ValueError as e:
                print(f"Failed to apply 'expand' filter: {e}")
                
            # Limit the initial data read to speed up stream startup
            self.mpv['demuxer-max-bytes'] = '500k'
            
            # Defaults optimized for fast start
            self.mpv['ytdl-format'] = 'best[height<=720]/bv*[height<=720]+ba/best'
            self.mpv['prefetch-playlist'] = 'yes'
            self.mpv['cache'] = 'yes'
            self.mpv['cache-secs'] = '60'
            self.mpv['demuxer-max-bytes'] = '50M'
            self.mpv['demuxer-readahead-secs'] = '10'
            self.mpv['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
            self.mpv['hr-seek'] = 'yes'
            self.mpv['gapless-audio'] = 'yes'

            @self.mpv.property_observer('eof-reached')
            def _eof(_name, value):
                if value:
                    if self.repeat_mode and 0 <= self.current_index < len(self.playlist):
                        self.play_current()
                    else:
                        self.next_track()

            @self.mpv.property_observer('duration')
            def _dur(_name, value):
                try:
                    dur = float(value or 0)
                    dur_ms = int(max(0, dur) * 1000)
                    if dur_ms > 0:
                        self.progress.setRange(0, dur_ms)
                        self.dur_label.setText(format_time(dur_ms))
                except Exception:
                    pass

            @self.mpv.property_observer('time-pos')
            def _time(_name, value):
                try:
                    pos = float(value or 0.0)
                    pos_ms = int(max(0.0, pos) * 1000)
                    self._last_play_pos_ms = pos_ms
                    if not self._user_scrubbing:
                        self.progress.setValue(pos_ms)
                        self.time_label.setText(format_time(pos_ms))
                except Exception:
                    pass

            @self.mpv.property_observer('file-loaded')
            def _loaded(_name, value):
                try:
                    if value:
                        self._maybe_reapply_resume('file-loaded')
                except Exception:
                    pass

            @self.mpv.property_observer('demuxer-cache-state')
            def _cache(_name, value):
                try:
                    if value and isinstance(value, dict):
                        cached = value.get('cache-end', 0)
                        # Only show if buffered more than 10 seconds ahead
                        if cached > 10:
                            # Only update every 5 seconds to avoid spam
                            now = time.time()
                            if not hasattr(self, '_last_buffer_msg') or now - self._last_buffer_msg > 5:
                                self.statusMessageSignal.emit(f"Buffered: {format_time(int(cached * 1000))}", 1000) # <-- FIX
                                self._last_buffer_msg = now
                except Exception:
                    pass
                    
            @self.mpv.property_observer('mute')
            def _mute(_name, value):
                self._update_volume_icon(value)                    

            self.pos_timer = QTimer(self); self.pos_timer.timeout.connect(self._update_position_tick); self.pos_timer.start(500)
        except Exception as e:
            QMessageBox.critical(self, "mpv error", f"Failed to initialize mpv.\n{e}\n\nEnsure mpv-2.dll/libmpv is on PATH or MPV_DLL_PATH is set.")
            raise
            
            # Set initial volume icon state
            self._update_volume_icon(self.mpv.mute)

    # Monitors
    def _init_monitors(self):
        # System-wide silence detection
        try:
            dev_id = getattr(self, 'monitor_device_id', None)
            if not isinstance(dev_id, int) or dev_id < 0:
                dev_id = None
        except Exception:
            dev_id = None

        self.audio_monitor = SystemAudioMonitor(
            silence_duration_s=self.silence_duration_s,
            silence_threshold=self.silence_threshold,
            resume_threshold=getattr(self, 'resume_threshold', self.silence_threshold * 1.5),
            monitor_system_output=self.monitor_system_output,
            device_id=dev_id
        )
        self.audio_monitor.silenceDetected.connect(self.on_silence_detected)
        self.audio_monitor.audioStateChanged.connect(self._update_silence_indicator)
        self.audio_monitor.start()
        # AFK monitor
        self.afk_monitor = AFKMonitor(self.afk_timeout_minutes)
        self.afk_monitor.userIsAFK.connect(self.on_user_afk)
        self.afk_monitor.start()


    def _update_silence_indicator(self, is_silent: bool = None):
        """Update the silence indicator - simplified version."""
        if is_silent is not None:
            self._last_system_is_silent = bool(is_silent)
        
        # Always keep visible to prevent layout shifts
        self.silence_indicator.setVisible(True)
        
        # Simple check: if we have a current track, assume we're active
        has_track = (self.current_index >= 0 and self.current_index < len(self.playlist))
        
        if has_track:
            # Any time we have a loaded track, show playing icon
            icon_text = "🎵"
            tooltip = "Media player is active"
            # Reset timer when we have an active track
            self._reset_silence_counter()
        else:
            # No track loaded: show system audio state
            if self._last_system_is_silent:
                icon_text = "🔇"
                remaining = max(0, self.audio_monitor.silence_duration_s - self.audio_monitor._silence_counter)
                tooltip = f"System is silent. Auto-play in {human_duration(remaining)}."
            else:
                icon_text = "🔊"
                tooltip = "System audio is active."
        
        # Always update
        self.silence_indicator.setPixmap(QPixmap())
        self.silence_indicator.setText(icon_text)
        self.silence_indicator.setToolTip(tooltip)
        
    def _force_update_silence_indicator_after_delay(self):
        """Force update the silence indicator after mpv has time to initialize."""
        try:
            QTimer.singleShot(500, lambda: self._update_silence_indicator())
        except Exception:
            pass    

    def _is_playing(self):
        """Clean playing detection."""
        try:
            return not bool(self.mpv.pause) and (self.current_index >= 0)
        except Exception:
            return False
    
    def _update_silence_tooltip(self):
        """Update only the tooltip, not the icon - called by timer every second."""
        if not hasattr(self, 'silence_indicator'):
            return
            
        is_app_playing = self._is_playing()
        
        if is_app_playing:
            tooltip = "Media player is active"
        elif self._last_system_is_silent:
            remaining_time = max(0, self.audio_monitor.silence_duration_s - self.audio_monitor._silence_counter)
            tooltip = f"System is silent. Auto-play in {human_duration(remaining_time)}."
        else:
            tooltip = "System audio is active."
        
        # Only update tooltip, don't touch the icon
        self.silence_indicator.setToolTip(tooltip)

    # Tray
    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("⚠ System tray not available")
            self.tray_icon = None
            return
        icon = self.tray_icon_play
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Silence Suzuka Player")
        tray_menu = QMenu()
        self.tray_play_pause = tray_menu.addAction("Play")
        self.tray_play_pause.triggered.connect(self.toggle_play_pause)
        tray_menu.addAction("Next").triggered.connect(self.next_track)
        tray_menu.addAction("Previous").triggered.connect(self.previous_track)
        tray_menu.addSeparator()
        tray_menu.addAction("Show Player").triggered.connect(self._show_player)
        tray_menu.addAction("Quit").triggered.connect(QApplication.instance().quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self._show_player()

    def _setup_button_animations(self):
        """Button feedback with proper circular glow"""
        try:
            buttons = [
                # Main controls
                (self.play_pause_btn, QSize(50, 50)),
                (self.prev_btn, QSize(22, 22)),
                (self.next_btn, QSize(22, 22)),
                (self.shuffle_btn, QSize(22, 22)),
                (self.repeat_btn, QSize(22, 22)),
                
                # Top bar buttons
                (self.stats_btn, QSize(18, 18)),
                (self.settings_btn, QSize(18, 18)),
                (self.theme_btn, QSize(18, 18)),  # Remove the duplicate
                
                # Playlist controls
                (self.save_btn, QSize(16, 16)),
                (self.load_btn, QSize(16, 16)),
                (self.duration_btn, QSize(16, 16)),
                (self.unwatched_btn, QSize(16, 16)),
                (self.duration_btn, QSize(16, 16)),
            ]
            
            # Icon button animations
            for btn, normal_size in buttons:
                def make_press_handler(button, n_size):
                    def on_press():
                        shrink_size = QSize(int(n_size.width() * 0.85), int(n_size.height() * 0.85))
                        button.setIconSize(shrink_size)
                        
                        btn_size = min(button.width(), button.height())
                        radius = btn_size // 2
                        
                        if self.theme == 'dark':
                            button.setStyleSheet(f"background-color: rgba(231, 111, 81, 0.4); border-radius: {radius}px;")
                        else:
                            button.setStyleSheet(f"background-color: rgba(231, 111, 81, 0.3); border-radius: {radius}px;")
                    return on_press
                
                def make_release_handler(button, n_size):
                    def on_release():
                        bounce_size = QSize(int(n_size.width() * 1.1), int(n_size.height() * 1.1))
                        button.setIconSize(bounce_size)
                        button.setStyleSheet("")
                        QTimer.singleShot(80, lambda: button.setIconSize(n_size))
                    return on_release
                
                btn.pressed.connect(make_press_handler(btn, normal_size))
                btn.released.connect(make_release_handler(btn, normal_size))
            
            # Text button animations (Add Media buttons)
            text_buttons = [self.add_media_main, self.add_media_dropdown, self.duration_btn]
            
            for btn in text_buttons:
                def make_text_press_handler(button):
                    def on_press():
                        self._flash_button_color(button, "#ff6b47", 150)
                    return on_press
                
                btn.pressed.connect(make_text_press_handler(btn))
                
        except Exception as e:
            print(f"Button animation error: {e}")
            
    def _flash_button_press(self, button):
        """Enhanced color flash using QGraphicsColorizeEffect"""
        try:
            from PySide6.QtWidgets import QGraphicsColorizeEffect
            
            # Create or reuse colorize effect
            if not hasattr(button, '_flash_effect'):
                button._flash_effect = QGraphicsColorizeEffect()
                button._flash_effect.setStrength(0.0)
                
                # Set flash color based on button type
                if button == self.play_pause_btn:
                    button._flash_effect.setColor(QColor("#ff4444"))  # Bright red
                else:
                    button._flash_effect.setColor(QColor("#ff8566"))  # Orange
            
            # Apply effect and animate
            button.setGraphicsEffect(button._flash_effect)
            
            if not hasattr(button, '_flash_anim'):
                button._flash_anim = QPropertyAnimation(button._flash_effect, b"strength")
                button._flash_anim.setDuration(150)
            
            # Animate: invisible -> strong -> invisible
            button._flash_anim.finished.connect(lambda: button.setGraphicsEffect(None))
            button._flash_anim.setKeyValueAt(0.0, 0.0)    # Start
            button._flash_anim.setKeyValueAt(0.4, 0.8)    # Peak flash
            button._flash_anim.setKeyValueAt(1.0, 0.0)    # Fade out
            button._flash_anim.start()
            
        except Exception as e:
            print(f"Button flash error: {e}")

    def _restore_button_style(self, button):
        """Remove graphics effect to restore normal appearance"""
        try:
            button.setGraphicsEffect(None)
        except Exception:
            pass

    def _show_player(self):
            # Restore the window intelligently
            if getattr(self, '_was_maximized', False):
                # If it was maximized before, restore it to maximized.
                self.showMaximized()
            else:
                # Otherwise, use the existing logic for normal windows.
                if getattr(self, 'center_on_restore', True):
                    self.center_on_screen()
                self.showNormal()
            
            # Activate and raise the window regardless of state
            self.activateWindow()
            self.raise_()

    def closeEvent(self, e):
        # Gracefully stop monitors/threads and persist settings
        try:
            if getattr(self, 'audio_monitor', None):
                self.audio_monitor.stop()
                try:
                    self.audio_monitor.wait(2000)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if getattr(self, 'afk_monitor', None):
                self.afk_monitor.stop()
                try:
                    self.afk_monitor.wait(2000)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self._save_session()
            self._save_settings()
        except Exception:
            pass
        super().closeEvent(e)

    def _update_tray(self):
        if not getattr(self, 'tray_icon', None):
            return
        if self._is_playing():
            self.tray_play_pause.setText("Pause")
            self.tray_icon.setIcon(self.tray_icon_pause) # Use the new white pause icon
        else:
            self.tray_play_pause.setText("Play")
            self.tray_icon.setIcon(self.tray_icon_play) # Use the new white play icon
        if 0 <= self.current_index < len(self.playlist):
            self.tray_icon.setToolTip(f"Silence Suzuka Player\nNow Playing: {self.playlist[self.current_index].get('title','Unknown')}")
        else:
            self.tray_icon.setToolTip("Silence Suzuka Player")

    # Persistence
    def _load_files(self):
        # Settings
        if CFG_SETTINGS.exists():
            try:
                s = json.load(open(CFG_SETTINGS, 'r', encoding='utf-8'))
                self.center_on_restore = bool(s.get('center_on_restore', True))
                self.auto_play_enabled = bool(s.get('auto_play_enabled', self.auto_play_enabled))
                self.afk_timeout_minutes = int(s.get('afk_timeout_minutes', self.afk_timeout_minutes))
                self.silence_duration_s = float(s.get('silence_duration_s', self.silence_duration_s))
                self.show_thumbnails = bool(s.get('show_thumbnails', self.show_thumbnails))
                self.volume_slider.setValue(int(s.get('volume', self.volume_slider.value())))
                self.theme = s.get('theme', self.theme)
                self.shuffle_mode = bool(s.get('shuffle_mode', self.shuffle_mode))
                self.repeat_mode = bool(s.get('repeat_mode', self.repeat_mode))
                self.grouped_view = bool(s.get('grouped_view', getattr(self, 'grouped_view', False)))
                self.monitor_system_output = bool(s.get('monitor_system_output', self.monitor_system_output))
                self.silence_threshold = float(s.get('silence_threshold', self.silence_threshold))
                self.resume_threshold = float(s.get('resume_threshold', self.resume_threshold))
                self.monitor_device_id = int(s.get('monitor_device_id', self.monitor_device_id))
                self.completed_percent = int(s.get('completed_percent', self.completed_percent))
                self.skip_completed = bool(s.get('skip_completed', self.skip_completed))
                self.unwatched_only = bool(s.get('unwatched_only', self.unwatched_only))
                self.show_up_next = bool(s.get('show_up_next', self.show_up_next))  
                self.restore_session = bool(s.get('restore_session', True))
                self.log_level = s.get('log_level', self.log_level)
                self.show_today_badge = bool(s.get('show_today_badge', True))
                self.group_singles = bool(s.get('group_singles', False))
                # Update logging level immediately
                try:
                    logging.getLogger().setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
                    # logger.info(f"Logging level set to {self.log_level}") # 
                except Exception:
                    pass
                # Restore scope if available
                try:
                    sk = s.get('scope_kind'); skey = s.get('scope_key')
                    if sk and (skey is not None):
                        self.play_scope = (sk, skey)
                except Exception:
                    pass
                # Apply theme with proper initialization
                if self.theme == 'vinyl':
                    self._apply_vinyl_theme()
                else:
                    # IMPORTANT: Clear any residual styling before applying dark theme
                    try:
                        bg = self.centralWidget()
                        if bg:
                            # Clear any existing styling completely
                            bg.setStyleSheet("#bgRoot { background: none; border-image: none; }")
                            bg.setAutoFillBackground(False)
                            
                            # Clear existing palette
                            pal = bg.palette()
                            pal.setBrush(bg.backgroundRole(), QBrush())
                            bg.setPalette(pal)
                    except Exception:
                        pass
                    
                    self._apply_dark_theme()
                
                # Apply dynamic font scaling after theme
                self._apply_dynamic_fonts()
                
                # Force update to ensure styling takes effect
                try:
                    self.update()
                    if hasattr(self, 'centralWidget') and self.centralWidget():
                        self.centralWidget().update()
                except Exception:
                    pass
                # Restore window state
                try:
                    win = s.get('window') or {}
                    if isinstance(win, dict):
                        w = win.get('w')
                        h = win.get('h')
                        
                        # THIS IS KEY: Restore the previous width and height first.
                        # This ensures the centered window has the size you expect.
                        if w is not None and h is not None:
                            self.resize(int(w), int(h))

                        # If centering is enabled, center it. Otherwise, restore the old position.
                        if self.center_on_restore and not win.get('maximized'):
                            self.center_on_screen()
                        else:
                            x = win.get('x')
                            y = win.get('y')
                            if x is not None and y is not None:
                                self.move(int(x), int(y))
                        
                        if win.get('maximized'):
                            self.showMaximized()
                except Exception:
                    pass
            except Exception as e:
                print(f"Settings load error: {e}")
                
        # --- FIX: Apply theme and fonts AFTER loading settings, but ALWAYS ---
        # This ensures the theme is set on first launch using the default value.
        if self.theme == 'vinyl':
            self._apply_vinyl_theme()
        else:
            self._apply_dark_theme()
        
        # Apply dynamic font scaling after theme
        self._apply_dynamic_fonts()

        # Force update to ensure styling takes effect
        try:
            self.update()
            if hasattr(self, 'centralWidget') and self.centralWidget():
                self.centralWidget().update()
        except Exception:
            pass
        # --- END FIX ---
               
    # ...rest of your function unchanged...
        # Front page auto-play checkbox removed; use Settings dialog
        # Apply persisted UI toggle states
        if hasattr(self, 'shuffle_btn'):
            self.shuffle_btn.setChecked(self.shuffle_mode)
        if hasattr(self, 'repeat_btn'):
            self.repeat_btn.setChecked(self.repeat_mode)
        # Ensure group toggle reflects current playback model visibility
        try:
            self._update_group_toggle_visibility()
        except Exception:
            pass

        # listening stats
        if CFG_STATS.exists():
            try:
                self.listening_stats = json.load(open(CFG_STATS, 'r', encoding='utf-8'))
            except Exception:
                self.listening_stats = {'daily': {}, 'overall': 0}
        else:
            self.listening_stats = {'daily': {}, 'overall': 0}

        # current playlist
        if CFG_CURRENT.exists():
            try:
                data = json.load(open(CFG_CURRENT, 'r', encoding='utf-8'))
                self.playlist = data.get('current_playlist', [])
            except Exception:
                self.playlist = []
        # positions
        if CFG_POS.exists():
            try:
                with open(CFG_POS, 'r', encoding='utf-8') as f:
                    self.playback_positions = json.load(f)
            except Exception as e:
                print(f"Resume positions load error: {e}")
                self.playback_positions = {}
        # saved playlists
        if CFG_PLAYLISTS.exists():
            try:
                self.saved_playlists = json.load(open(CFG_PLAYLISTS, 'r', encoding='utf-8'))
            except Exception:
                self.saved_playlists = {}
        # completed URLs
        if CFG_COMPLETED.exists():
            try:
                data = json.load(open(CFG_COMPLETED, 'r', encoding='utf-8'))
                if isinstance(data, list):
                    self.completed_urls = set(self._canonical_url_key(u) for u in data if u)
                elif isinstance(data, dict):
                    self.completed_urls = set(self._canonical_url_key(k) for k, v in data.items() if v and k)
            except Exception:
                self.completed_urls = set()
        self._refresh_playlist_widget()
        try:
            self._update_scope_label()
        except Exception:
            pass
        # Ensure Up Next visibility matches loaded settings on startup
        try:
            if hasattr(self, 'up_next_container'):
                self.up_next_container.setVisible(bool(getattr(self, 'show_up_next', True)))
            if hasattr(self, 'up_next_header'):
                self.up_next_header.setChecked(not bool(getattr(self, 'up_next_collapsed', False)))
                self._toggle_up_next_visible(self.up_next_header.isChecked())
        except Exception:
            pass

        self._load_session()
        
    def _save_settings(self):
        s = {
            'auto_play_enabled': self.auto_play_enabled,
            'afk_timeout_minutes': self.afk_timeout_minutes,
            'silence_duration_s': self.silence_duration_s,
            'show_thumbnails': self.show_thumbnails,
            'volume': self.volume_slider.value(),
            'theme': self.theme,
            'shuffle_mode': self.shuffle_mode,
            'repeat_mode': self.repeat_mode,
            'grouped_view': getattr(self, 'grouped_view', False),
            'monitor_system_output': bool(getattr(self, 'monitor_system_output', True)),
            'silence_threshold': float(getattr(self, 'silence_threshold', 0.03)),
            'resume_threshold': float(getattr(self, 'resume_threshold', max(0.03, getattr(self, 'silence_threshold', 0.03) * 1.5))),
            'monitor_device_id': int(getattr(self, 'monitor_device_id', 46)),
            'completed_percent': int(getattr(self, 'completed_percent', 95)),
            'skip_completed': bool(getattr(self, 'skip_completed', False)),
            'unwatched_only': bool(getattr(self, 'unwatched_only', False)),
            'show_up_next': bool(getattr(self, 'show_up_next', True)),
            'scope_kind': (getattr(self, 'play_scope', None)[0] if isinstance(getattr(self, 'play_scope', None), tuple) else None),
            'scope_key': (getattr(self, 'play_scope', None)[1] if isinstance(getattr(self, 'play_scope', None), tuple) else None),
            'log_level': getattr(self, 'log_level', 'INFO'),
            'center_on_restore': bool(getattr(self, 'center_on_restore', True)),
            'minimize_to_tray': self.minimize_to_tray,
            'show_today_badge': self.show_today_badge,
            'group_singles': bool(getattr(self, 'group_singles', False)),
            'restore_session': bool(getattr(self, 'restore_session', True)),
            'window': {
                'x': int(self.geometry().x()),
                'y': int(self.geometry().y()),
                'w': int(self.geometry().width()),
                'h': int(self.geometry().height()),
                'maximized': bool(self.isMaximized())
            }
        }
        try:
            json.dump(s, open(CFG_SETTINGS, 'w', encoding='utf-8'))
        except Exception:
            pass

    def _save_current_playlist(self):
        try:
            json.dump({'current_playlist': self.playlist}, open(CFG_CURRENT, 'w', encoding='utf-8'))
        except Exception:
            pass

    def _save_positions(self):
        try:
            with open(CFG_POS, 'w', encoding='utf-8') as f:
                json.dump(self.playback_positions, f)
        except Exception as e:
            print(f"Resume positions save error: {e}")

    def _save_playlists_file(self):
        try:
            json.dump(self.saved_playlists, open(CFG_PLAYLISTS, 'w', encoding='utf-8'))
        except Exception:
            pass

    def _save_completed(self):
        try:
            json.dump(sorted(list(self.completed_urls)), open(CFG_COMPLETED, 'w', encoding='utf-8'))
        except Exception:
            pass

    def _save_session(self):
        """Saves the current application state to session.json."""
        if not getattr(self, 'restore_session', True):
            # If the setting is off, ensure no session file exists
            if CFG_SESSION.exists():
                try:
                    CFG_SESSION.unlink()
                except Exception as e:
                    logger.error(f"Could not remove session file: {e}")
            return

        try:
            current_pos_ms = 0
            # Get the most up-to-date position if playing
            if self._is_playing() and 0 <= self.current_index < len(self.playlist):
                current_pos_ms = int(getattr(self, '_last_play_pos_ms', 0))

            session_data = {
                'playlist': self.playlist,
                'current_index': self.current_index,
                'last_position_ms': current_pos_ms,
                'play_scope': self.play_scope,
                'expansion_state': self._get_tree_expansion_state(),
                'version': 1.0
            }
            with open(CFG_SESSION, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            logger.info("Session state saved.")
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")

    def _load_session(self):
            """Loads the last saved session if the setting is enabled."""
            if not getattr(self, 'restore_session', True):
                logger.info("Session restore is disabled in settings.")
                return
            if not CFG_SESSION.exists():
                logger.info("No session file found to restore.")
                return

            try:
                logger.info("Attempting to restore previous session...")
                with open(CFG_SESSION, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # --- Data Validation ---
                if not isinstance(session_data, dict): raise ValueError("Session data is not a valid dictionary.")
                playlist = session_data.get('playlist');
                if not isinstance(playlist, list): raise ValueError("Playlist in session data is not a valid list.")
                current_index = session_data.get('current_index', -1)
                if not isinstance(current_index, int): current_index = -1
                expansion_state = session_data.get('expansion_state', {});
                if not isinstance(expansion_state, dict): expansion_state = {}

                # --- Apply State ---
                self.playlist = playlist
                self.current_index = current_index
                self.play_scope = session_data.get('play_scope')

                # --- Restore UI ---
                self._refresh_playlist_widget(expansion_state=expansion_state)
                self._update_scope_label()

                # --- Load the last track but don't play it yet ---
                if 0 <= self.current_index < len(self.playlist):
                    pos_ms = session_data.get('last_position_ms', 0)
                    try: pos_ms = int(pos_ms or 0)
                    except (ValueError, TypeError): pos_ms = 0
                    
                    # --- Call the new unified method to prepare the track ---
                    self._prepare_and_load_track(self.current_index, start_pos_ms=pos_ms, should_play=False)

                    # --- Update UI specific to restoring a session ---
                    self.play_pause_btn.setIcon(self._play_icon_normal)
                    QTimer.singleShot(500, self._update_restored_duration)

                self.status.showMessage("Restored last session. Press Play to resume.", 5000)

            except Exception as e:
                import traceback
                logger.error(f"Failed to load session state: {e}\n{traceback.format_exc()}")
                self.status.showMessage("Could not restore session: file may be corrupt.", 5000)
                if CFG_SESSION.exists():
                    try: CFG_SESSION.unlink()
                    except Exception as e_del: logger.error(f"Failed to delete corrupt session file: {e_del}")

    def _update_restored_duration(self):
        """Safely update duration label after a session restore."""
        try:
            duration_ms = int((self.mpv.duration or 0) * 1000)
            if duration_ms > 0:
                self.dur_label.setText(format_time(duration_ms))
        except Exception:
            pass # Ignore if mpv is not ready

    # UI data binding
    def _refresh_playlist_widget(self, expansion_state=None, incremental_update=False):
        """Optimized playlist refresh with incremental updates"""
        if expansion_state is None:
            expansion_state = {}

        # For small playlists or major changes, do full refresh
        if not incremental_update or len(self.playlist) < 200:
            self._refresh_playlist_widget_full(expansion_state)
            return

        # For larger playlists, try incremental update
        try:
            self._refresh_playlist_widget_incremental(expansion_state)
        except Exception:
            # Fallback to full refresh if incremental fails
            self._refresh_playlist_widget_full(expansion_state)

    def _refresh_playlist_widget_full(self, expansion_state=None):
        """Full playlist refresh - your existing logic"""
        if expansion_state is None:
            expansion_state = {}

        self.playlist_tree.clear()
        # Update the header
        self.library_header_label.setText(f"Library ({len(self.playlist)})")

        # [Keep all your existing grouping logic here - it's fine]
        items_with_playlist = []
        single_items = []
        for idx, it in enumerate(self.playlist):
            if isinstance(it, dict) and (it.get('playlist') or it.get('playlist_key')):
                items_with_playlist.append((idx, it))
            else:
                single_items.append((idx, it))

        # --- Render items belonging to a playlist ---
        group_map = {}
        for idx, it in items_with_playlist:
            key = it.get('playlist_key') or it.get('playlist')
            g = group_map.setdefault(key, {'title': it.get('playlist') or str(key), 'items': []})
            g['items'].append((idx, it))

        for key, g in group_map.items():
            ptitle = g.get('title') or str(key)
            arr = g.get('items') or []
            # Add group nodes as top-level items
            gnode = QTreeWidgetItem(self.playlist_tree, [f"📃 {ptitle} ({len(arr)})"])
            gnode.setFont(0, self._font_serif_no_size(italic=True, bold=True))
            norm_key = key if key else (g.get('title') or ptitle)
            gnode.setData(0, Qt.UserRole, ('group', norm_key))
            gnode.setData(0, Qt.UserRole + 1, norm_key)
            
            # Restore expansion state
            is_expanded = expansion_state.get(norm_key, False)
            gnode.setExpanded(is_expanded)
            
            try:
                chevron_color = self.playlist_chevron_color()
                chev_px = make_chevron_pixmap_svg(px_size=20, stroke_color=chevron_color)
                gnode.setIcon(0, QIcon(chev_px))
            except Exception:
                pass
            for idx, it in arr:
                icon = playlist_icon_for_type(it.get('type'))
                node = QTreeWidgetItem([it.get('title', 'Unknown')])
                if isinstance(icon, QIcon):
                    node.setIcon(0, icon)
                else:
                    node.setText(0, f"{icon} {it.get('title', 'Unknown')}")
                node.setFont(0, self._font_serif_no_size(italic=True, bold=True))
                node.setData(0, Qt.UserRole, ('current', idx, it))
                gnode.addChild(node)

        # --- Render single items ---
        if single_items:
            if getattr(self, 'group_singles', False):
                gnode = QTreeWidgetItem(self.playlist_tree, [f"🎵 Miscellaneous ({len(single_items)})"])
                gnode.setFont(0, self._font_serif_no_size(italic=True, bold=True))
                gnode.setData(0, Qt.UserRole, ('group', 'miscellaneous'))
                gnode.setData(0, Qt.UserRole + 1, 'miscellaneous')
                
                is_expanded = expansion_state.get('miscellaneous', False)
                gnode.setExpanded(is_expanded)
                
                for idx, it in single_items:
                    icon = playlist_icon_for_type(it.get('type'))
                    node = QTreeWidgetItem([it.get('title', 'Unknown')])
                    if isinstance(icon, QIcon):
                        node.setIcon(0, icon)
                    else:
                        node.setText(0, f"{icon} {it.get('title', 'Unknown')}")
                    node.setFont(0, self._font_serif_no_size(italic=True, bold=True))
                    node.setData(0, Qt.UserRole, ('current', idx, it))
                    gnode.addChild(node)
            else:
                for idx, it in single_items:
                    icon = playlist_icon_for_type(it.get('type'))
                    node = QTreeWidgetItem(self.playlist_tree, [it.get('title', 'Unknown')])
                    if isinstance(icon, QIcon):
                        node.setIcon(0, icon)
                    else:
                        node.setText(0, f"{icon} {it.get('title', 'Unknown')}")
                    node.setFont(0, self._font_serif_no_size(italic=True, bold=True))
                    node.setData(0, Qt.UserRole, ('current', idx, it))

        # Show empty state if needed
        if not self.playlist:
            self.playlist_stack.setCurrentIndex(1)
        else:
            self.playlist_stack.setCurrentIndex(0)

    def _refresh_playlist_widget_incremental(self, expansion_state=None):
        """Incremental update - only update what changed"""
        # This is a more complex optimization - for now, just do full refresh
        # You could implement this later if needed for very large playlists
        self._refresh_playlist_widget_full(expansion_state)


    def _get_tree_expansion_state(self):
        """Saves the expansion state of all group items in the playlist tree."""
        state = {}
        try:
            iterator = QTreeWidgetItemIterator(self.playlist_tree)
            while iterator.value():
                item = iterator.value()
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'group':
                    # Use the same effective key logic as context menus
                    raw_key = data[1] if len(data) > 1 else None
                    key = self._group_effective_key(raw_key, item)
                    if key:
                        state[key] = item.isExpanded()
                iterator += 1
        except Exception as e:
            logger.error(f"Failed to get tree expansion state: {e}")
        return state 


    def _get_tree_expansion_state(self):
        """Saves the expansion state of all group items in the playlist tree."""
        state = {}
        try:
            iterator = QTreeWidgetItemIterator(self.playlist_tree)
            while iterator.value():
                item = iterator.value()
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'group':
                    # Use the same effective key logic as context menus
                    raw_key = data[1] if len(data) > 1 else None
                    key = self._group_effective_key(raw_key, item)
                    if key:
                        state[key] = item.isExpanded()
                iterator += 1
        except Exception as e:
            logger.error(f"Failed to get tree expansion state: {e}")
        return state            

    def _display_text(self, item):
        icon = "🔴" if item.get('type') == 'youtube' else "🐟" if item.get('type') == 'bilibili' else "🎬"
        return f"{icon} {item.get('title','Unknown')}"

    def _apply_menu_theme(self, menu: QMenu):
        try:
            try:
                menu.setFont(QFont(self._ui_font))
            except Exception:
                pass
            if getattr(self, 'theme', 'dark') == 'vinyl':
                menu.setStyleSheet(
                    "QMenu { background-color: #faf3e0; color: #4a2c2a; border: 1px solid #c2a882; } "
                    "QMenu::item { padding: 6px 12px; } "
                    "QMenu::item:selected { background-color: #e76f51; color: #f3ead3; }"
                )
            else:
                menu.setStyleSheet(
                    "QMenu { background-color: #282828; color: #B3B3B3; border: 1px solid #535353; } "
                    "QMenu::item { padding: 6px 12px; } "
                    "QMenu::item:selected { background-color: #404040; color: #1DB954; }"
                )
        except Exception:
            pass

    def _apply_dialog_theme(self, dialog: QDialog):
        """Applies a consistent dark or vinyl theme to any dialog."""
        try:
            is_dark = getattr(self, 'theme', 'dark') == 'dark'
            
            if is_dark:
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #2a2a2a; color: #f3f3f3;
                    }
                    QLabel, QCheckBox, QGroupBox::title {
                        color: #f3f3f3;
                    }
                    QLineEdit, QTextEdit, QListWidget, QTreeWidget, QScrollArea {
                        background-color: #1e1e1e; color: #f3f3f3; border: 1px solid #4a4a4a;
                        selection-background-color: #e76f51;
                    }
                    QGroupBox {
                        border: 1px solid #4a4a4a; margin-top: 6px; padding: 10px 5px 5px 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;
                    }
                    QComboBox {
                        background-color: #1e1e1e; border: 1px solid #4a4a4a; padding: 4px; color: #f3f3f3;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #1e1e1e; border: 1px solid #4a4a4a;
                        selection-background-color: #e76f51; color: #f3f3f3; selection-color: #ffffff;
                    }
                    /* --- FINAL FIX for Header --- */
                    QHeaderView::section {
                        background-color: #2a2a2a; color: #f3f3f3; padding: 4px;
                        border-top: 0px; border-right: 0px; border-left: 1px solid #4a4a4a; border-bottom: 1px solid #4a4a4a;
                    }
                    /* --- FINAL FIX for Scrollbars --- */
                    QScrollBar:vertical {
                        background: #2a2a2a; width: 12px; margin: 0px; border-left: 1px solid #4a4a4a;
                    }
                    QScrollBar::handle:vertical {
                        background: #4a4a4a; min-height: 24px; border-radius: 6px;
                    }
                    QScrollBar::handle:vertical:hover { background: #5a5a5a; }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
                    
                    QPushButton {
                        background-color: #3a3a3a; color: #f3f3f3; border: 1px solid #5a5a5a;
                        padding: 6px 12px; border-radius: 4px;
                    }
                    QPushButton:hover { background-color: #4a4a4a; }
                    QPushButton:pressed { background-color: #5a5a5a; }
                """)
            else: # Vinyl theme
                dialog.setStyleSheet("""
                    QDialog {
                        background-color: #faf3e0; color: #4a2c2a;
                    }
                    /* --- FIX: Style the content widget inside the scroll area --- */
                    QScrollArea QWidget {
                        background-color: #faf3e0;
                    }
                    QLabel, QCheckBox, QGroupBox::title {
                        color: #4a2c2a;
                    }
                    QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                        background-color: #fff6d9; color: #4a2c2a; border: 1px solid #c2a882;
                        selection-background-color: #e76f51;
                    }
                    QGroupBox {
                        border: 1px solid #c2a882; margin-top: 6px; padding: 10px 5px 5px 5px;
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px;
                    }
                    QComboBox {
                        background-color: #fff6d9; border: 1px solid #c2a882; padding: 4px; color: #4a2c2a;
                    }
                    QComboBox QAbstractItemView {
                        background-color: #fff6d9; border: 1px solid #c2a882;
                        selection-background-color: #e76f51; color: #4a2c2a; selection-color: #ffffff;
                    }
                    QHeaderView::section {
                        background-color: #f0e7cf; color: #4a2c2a; padding: 4px; border: 1px solid #c2a882;
                    }
                    QScrollBar:vertical {
                        background: #faf3e0; width: 12px; margin: 0px; border-left: 1px solid #c2a882;
                    }
                    QScrollBar::handle:vertical {
                        background: #c2a882; min-height: 24px; border-radius: 6px;
                    }
                    QScrollBar::handle:vertical:hover { background: #b6916d; }
                    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
                    
                    QPushButton {
                        background-color: #f0e7cf; color: #4a2c2a; border: 1px solid #c2a882;
                        padding: 6px 12px; border-radius: 4px;
                    }
                    QPushButton:hover { background-color: #e9e0c8; }
                    QPushButton:pressed { background-color: #e0d9bf; }
                """)
        except Exception as e:
            print(f"Failed to apply dialog theme: {e}")

    def _is_completed_url(self, url):
        try:
            if not url:
                return False
            key = self._canonical_url_key(url)
            return (key in self.completed_urls) or (url in self.completed_urls)
        except Exception:
            return False

    def _apply_filters_to_tree(self, *_args):
        try:
            root = self.playlist_tree.topLevelItem(0)
            if not root:
                return
            text = (self.search_bar.text() if hasattr(self, 'search_bar') else '') or ''
            text = text.strip().lower()
            uw = bool(getattr(self, 'unwatched_only', False))
            def apply(node):
                data = node.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'current':
                    idx, it = data[1], data[2]
                    show = True
                    if text:
                        try:
                            s = (it.get('title','') + ' ' + it.get('url','')).lower()
                            show = (text in s)
                        except Exception:
                            show = False
                    if show and uw:
                        show = not self._is_completed_url(it.get('url'))
                    node.setHidden(not show)
                    return show
                # group or root
                any_visible = False
                for i in range(node.childCount()):
                    if apply(node.child(i)):
                        any_visible = True
                # hide empty groups
                if isinstance(data, tuple) and data[0] == 'group':
                    node.setHidden(not any_visible)
                return any_visible
            apply(root)
        except Exception:
            pass

    def _process_with_yield(self, items: list, processor_func, batch_size: int = 25, progress_callback=None):
            """Process a large list in batches to keep UI responsive."""
            total_items = len(items)
            processed = 0
            
            def process_batch():
                nonlocal processed
                batch_end = min(processed + batch_size, total_items)
                batch = items[processed:batch_end]
                
                try:
                    processor_func(batch, processed)
                    processed = batch_end
                    
                    if progress_callback:
                        progress_callback(processed, total_items)
                    
                    if processed < total_items:
                        # Schedule next batch
                        QTimer.singleShot(1, process_batch)
                    
                except Exception as e:
                    print(f"Batch processing error: {e}")
            
            process_batch()

    def _toggle_unwatched_only(self, checked):
        try:
            self.unwatched_only = bool(checked)
            self._save_settings()
            self._apply_filters_to_tree()
            self._update_up_next()
        except Exception:
            pass

    def _toggle_up_next_visible(self, show: bool):
        try:
            if hasattr(self, 'up_next_stack'):
                # This now correctly controls the entire container below the header
                self.up_next_stack.setVisible(bool(show))
            # Also rotate the header caret
            if hasattr(self, 'up_next_header'):
                self.up_next_header.setText(("▼ Up Next" if show else "▶ Up Next"))
        except Exception:
            pass

    def _on_up_next_header_clicked(self):
        """Smarter handler that only toggles if the button is checkable."""
        try:
            # Only process the toggle if the button is in its interactive, checkable state.
            # This prevents any action when it's disabled during shuffle mode.
            if self.up_next_header.isCheckable():
                # The button's state has already changed, so we just sync the UI.
                self._toggle_up_next_visible(self.up_next_header.isChecked())
        except Exception:
            pass    

    def _update_up_next(self):
        try:
            # --- FIX: Stop any scrolling animations before clearing the list ---
            self._stop_scrolling()

            if not hasattr(self, 'up_next'):
                return

            # Show message for both shuffle AND repeat mode
            if self.shuffle_mode:
                self.up_next_stack.setCurrentIndex(1) # Show shuffle message
                self.up_next_header.setCheckable(False)
                self.up_next_header.setChecked(True)
                self._toggle_up_next_visible(True)
                return
            elif self.repeat_mode:
                self.up_next_stack.setCurrentIndex(2) # Show repeat message
                self.up_next_header.setCheckable(False)
                self.up_next_header.setChecked(True)
                self._toggle_up_next_visible(True)
                return
            else:
                # Normal mode - show the song list
                self.up_next_header.setCheckable(True)
                self.up_next_stack.setCurrentIndex(0) # Show the song list

                # Respect the settings toggle
                if not bool(getattr(self, 'show_up_next', True)):
                    if hasattr(self, 'up_next_container'):
                        self.up_next_container.setVisible(False)
                    return
                else:
                    if hasattr(self, 'up_next_container'):
                        self.up_next_container.setVisible(True)

                # Rest of your existing code for populating the song list...
                self.up_next.clear()
                indices = self._scope_indices()

                if not indices:
                    return

                try:
                    curpos = indices.index(self.current_index) if self.current_index in indices else -1
                except Exception:
                    curpos = -1

                upcoming = []
                if curpos >= 0:
                    upcoming = indices[curpos + 1:curpos + 6]
                else:
                    upcoming = indices[:5]

                if getattr(self, 'unwatched_only', False):
                    upcoming = [i for i in upcoming if not self._is_completed_url(self.playlist[i].get('url'))]

                for i in upcoming:
                    if 0 <= i < len(self.playlist):
                        it = self.playlist[i]
                        title = it.get('title', 'Unknown')
                        icon = playlist_icon_for_type(it.get('type'))

                        node = QTreeWidgetItem()

                        if isinstance(icon, QIcon):
                            node.setText(0, title)
                            node.setIcon(0, icon)
                        else:
                            node.setText(0, f"{icon} {title}")

                        node.setData(0, Qt.UserRole, ('next', i))
                        node.setData(0, Qt.UserRole + 1, title)
                        self.up_next.addTopLevelItem(node)
        except Exception:
            pass
        
    def _on_up_next_double_clicked(self, item, column):
        try:
            data = item.data(0, Qt.UserRole)
            if isinstance(data, tuple) and data[0] == 'next':
                idx = data[1]
                self._play_index(idx)
        except Exception:
            pass

    def _show_up_next_menu(self, pos):
        try:
            item = self.up_next.itemAt(pos)
            if not item:
                return
            data = item.data(0, Qt.UserRole)
            if not (isinstance(data, tuple) and data[0] == 'next'):
                return
            idx = data[1]
            menu = QMenu(); self._apply_menu_theme(menu)
            menu.addAction('▶ Play').triggered.connect(lambda i=idx: self._play_index(i))
            menu.addAction('🗑️ Remove').triggered.connect(lambda i=idx: self._remove_index(i))
            menu.exec(self.up_next.viewport().mapToGlobal(pos))
        except Exception:
            pass

    def _selected_current_indices(self):
        try:
            nodes = self.playlist_tree.selectedItems()
            idxs = []
            for n in nodes:
                data = n.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'current':
                    idxs.append(int(data[1]))
            return sorted(set([i for i in idxs if 0 <= i < len(self.playlist)]))
        except Exception:
            return []

    def _bulk_remove_selected(self):
        try:
            idxs = self._selected_current_indices()
            if not idxs:
                return
            was_playing = self._is_playing()
            
            # Sort in reverse order so we delete from end to beginning
            # This prevents index shifting issues
            for i in sorted(idxs, reverse=True):
                if 0 <= i < len(self.playlist):
                    del self.playlist[i]
                    # Update current_index if affected
                    if self.current_index == i:
                        self.current_index = -1
                    elif i < self.current_index:
                        self.current_index -= 1
            
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            self.status.showMessage(f"Removed {len(idxs)} items", 3000)
        except Exception as e:
            self.status.showMessage(f"Remove failed: {e}", 4000)

    def _bulk_clear_resume_selected(self):
        try:
            idxs = self._selected_current_indices()
            if not idxs:
                return
            for i in idxs:
                u = self.playlist[i].get('url')
                if u and (u in self.playback_positions):
                    del self.playback_positions[u]
            self._save_positions()
            self.status.showMessage('Cleared resume for selected', 3000)
        except Exception:
            pass

    def _bulk_mark_unwatched_selected(self):
        try:
            idxs = self._selected_current_indices()
            if not idxs:
                return
            changed = 0
            for i in idxs:
                u = self.playlist[i].get('url')
                if u:
                    for k in (u, self._canonical_url_key(u)):
                        if k in self.completed_urls:
                            self.completed_urls.discard(k); changed += 1
            if changed:
                self._save_completed()
            self.status.showMessage('Marked selected as unwatched', 3000)
            self._apply_filters_to_tree()
        except Exception:
            pass

    def _highlight_current_row(self):
        """Highlight the currently playing item with icon and bold text"""
        try:
            # Get fonts
            default_font = self._font_serif_no_size(italic=True, bold=True)
            playing_font = self._font_serif_no_size(italic=True, bold=True)
            playing_font.setWeight(QFont.ExtraBold)

            iterator = QTreeWidgetItemIterator(self.playlist_tree)
            item_to_scroll_to = None

            while iterator.value():
                item = iterator.value()
                data = item.data(0, Qt.UserRole)

                if isinstance(data, tuple) and data[0] == 'current':
                    idx = data[1]
                    
                    # Get the original text without any playing indicators
                    original_text = item.text(0)
                    if original_text.startswith('▶ '):
                        original_text = original_text[2:]

                    if idx == self.current_index:
                        item.setText(0, f"▶ {original_text}")
                        item.setFont(0, playing_font)
                        text_color = QColor("#d1603f")      # Slightly deeper orange
                        item.setForeground(0, text_color)
                        # Add subtle background highlight
                        item.setBackground(0, QColor(231, 111, 81, 25))  # Very subtle orange background

                        # Set the theme-appropriate highlight color
                        text_color = QColor("#e76f51") # Same for both themes
                        item.setForeground(0, text_color)
                        
                        # Mark this item to scroll to it later
                        item_to_scroll_to = item

                    else:
                        # Not the current item - restore normal appearance
                        item.setText(0, original_text)
                        item.setFont(0, default_font)
                        item.setForeground(0, QBrush()) # Resets to default color

                iterator += 1

            # Scroll to the highlighted item after all styling is applied
            if item_to_scroll_to:
                self.playlist_tree.scrollToItem(item_to_scroll_to, QAbstractItemView.PositionAtCenter)

        except Exception as e:
            logger.error(f"Highlight row failed: {e}")
        
    def _on_title_resolved(self, url: str, title: str):
        try:
            # Update the playlist item
            for item in self.playlist:
                if item.get('url') == url:
                    item['title'] = title
                    break
            
            # Update the UI
            self._update_tree_item_title(url, title)

            # Update the "Now Playing" label if this is the current track
            if 0 <= self.current_index < len(self.playlist) and self.playlist[self.current_index].get('url') == url:
                self._set_track_title(title)

            # Save playlist to reflect updated titles
            self._save_current_playlist()
        except Exception as e:
            print(f"Error updating title: {e}")

    def _update_item_title(self, url: str, title: str):
        """Update item title with optimized tree search"""
        updated = False
        for it in self.playlist:
            if it.get('url') == url:
                it['title'] = title
                updated = True
                break
        
        if updated:
            self._save_current_playlist()
            # OPTIMIZED: Find and update specific tree item instead of walking entire tree
            self._update_tree_item_title(url, title)
            
            # Update now playing label if this is current
            if 0 <= self.current_index < len(self.playlist):
                if self.playlist[self.current_index].get('url') == url:
                    self._set_track_title(title)

    def _update_tree_item_title(self, url: str, title: str):
        """Update specific tree item title without full refresh"""
        try:
            iterator = QTreeWidgetItemIterator(self.playlist_tree)
            while iterator.value():
                item = iterator.value()
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'current':
                    _, idx, item_data = data
                    if isinstance(item_data, dict) and item_data.get('url') == url:
                        # Update the tree item
                        icon = playlist_icon_for_type(item_data.get('type'))
                        if isinstance(icon, QIcon):
                            item.setText(0, title)
                            item.setIcon(0, icon)
                        else:
                            item.setText(0, f"{icon} {title}")

                        # Reset the item's style from its loading state
                        font = item.font(0)
                        font.setItalic(False)
                        item.setFont(0, font)
                        item.setForeground(0, QBrush()) # Resets to default color
                        
                        # Update the data reference
                        item_data['title'] = title
                        item.setData(0, Qt.UserRole, ('current', idx, item_data))
                        break
                iterator += 1
        except Exception as e:
            print(f"Update tree item title failed: {e}")

    def _toggle_group(self, checked):
        """Toggle grouped view and refresh the playlist tree."""
        self.grouped_view = bool(checked)
        self._refresh_playlist_widget()
        self._save_settings()
        
    # URL canonicalization for consistent resume keys (instance methods)
    def _canonical_url_key(self, url: str) -> str:
        try:
            import urllib.parse as up, re
            if not url:
                return url
            lo = url.lower()
            if ('youtube.com' in lo) or ('youtu.be' in lo):
                u = up.urlsplit(url)
                vid = None
                if 'youtu.be' in lo:
                    p = u.path or ''
                    vid = p.strip('/').split('/')[0].split('?')[0]
                else:
                    qs = up.parse_qs(u.query or '')
                    vid = (qs.get('v') or [''])[0]
                if vid:
                    return f"https://www.youtube.com/watch?v={vid}"
            if 'bilibili.com' in lo:
                m = re.search(r'/video/([A-Za-z0-9]+)', url)
                if m:
                    return f"https://www.bilibili.com/video/{m.group(1)}"
            # default: strip fragment and trailing slash
            u = up.urlsplit(url)
            u2 = up.urlunsplit((u.scheme, u.netloc, (u.path or '').rstrip('/'), u.query or '', ''))
            return u2
        except Exception:
            return url

    def _is_local_file(self, url):
        """
        Returns True if the url refers to a local file path or file:// URL.
        Handles file:///C:/... (Windows), file:///home/... (Unix), and plain file paths.
        """
        import os
        from urllib.parse import urlparse, unquote

        if not url:
            return False
        if url.startswith('file://'):
            parsed = urlparse(url)
            path = unquote(parsed.path)
            # On Windows, path often starts with a slash: /C:/Users/...
            if os.name == 'nt' and path.startswith('/'):
                path = path[1:]  # Remove leading slash for Windows
            return os.path.isfile(path)
        if url.startswith('http://') or url.startswith('https://'):
            return False
        return os.path.isfile(url) or (os.path.exists(url) and not url.startswith(('http://', 'https://')))       

    def _find_resume_key_for_url(self, url: str):
        try:
            key = self._canonical_url_key(url)
            if key in self.playback_positions:
                return key
            import re
            lo = (url or '').lower()
            youid = None; bilibid = None
            # extract identifiers
            if ('youtube.com' in lo) or ('youtu.be' in lo):
                try:
                    youid = self._canonical_url_key(url).split('=')[-1]
                except Exception:
                    youid = None
            if 'bilibili.com' in lo:
                try:
                    m = re.search(r'/video/([A-Za-z0-9]+)', url)
                    bilibid = m.group(1) if m else None
                except Exception:
                    bilibid = None
            for k in list(self.playback_positions.keys()):
                kl = k.lower()
                if youid and youid in kl:
                    return k
                if bilibid and (bilibid and bilibid.lower() in kl):
                    return k
            return None
        except Exception:
            return None

    # Scoped Library helpers
    def _scope_indices(self):
        try:
            if not self.playlist:
                return list(range(len(self.playlist)))
            if not getattr(self, 'play_scope', None):
                return list(range(len(self.playlist)))
            kind, key = self.play_scope
            if kind == 'group':
                # Primary: match either playlist_key OR playlist title
                has_playlist_match = any(((it.get('playlist_key') == key) or (it.get('playlist') == key)) for it in self.playlist)
                if has_playlist_match:
                    return [i for i, it in enumerate(self.playlist) if ((it.get('playlist_key') == key) or (it.get('playlist') == key))]
                
                # Handle special groups
                if key == 'miscellaneous':
                    # Return indices of items without playlist_key or playlist
                    return [i for i, it in enumerate(self.playlist) if not (it.get('playlist_key') or it.get('playlist'))]
                elif key in ('youtube', 'bilibili', 'local'):
                    # Fallback: source-type grouping
                    return [i for i, it in enumerate(self.playlist) if it.get('type') == key]
                return []
            return list(range(len(self.playlist)))
        except Exception:
            return list(range(len(self.playlist)))
    
    def _get_visible_indices(self):
        indices = []
        root = self.playlist_tree.topLevelItem(0)
        def walk(node):
            for i in range(node.childCount()):
                child = node.child(i)
                data = child.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'current':
                    indices.append(data[1])
                walk(child)
        if root:
            walk(root)
        return indices

    def _scope_title_from_key(self, key):
        try:
            for it in self.playlist:
                if (it.get('playlist_key') or it.get('playlist')) == key:
                    return it.get('playlist') or str(key)
        except Exception:
            pass
        # Fallback naming for source-type groups
        names = {'youtube': 'YouTube', 'bilibili': 'Bilibili', 'local': 'Local', 'miscellaneous': 'Miscellaneous'}
        if key in names:
            return names[key]
        # Avoid showing 'False' or empty
        if not key or key is False:
            return 'Library'
        return str(key)
            
    def _on_scope_changed(self, index):
        """Handle changes to the dropdown selection."""
        try:
            key = self.scope_dropdown.itemData(index)  # Get the selected data (e.g., "playlist1")
            name = self.scope_dropdown.currentText()  # Get the visible name (e.g., "Playlist 1")

            # Debug logging
            print(f"[ScopeChanged] key={key!r} name={name!r}")

            if key is None:
                # Selected "Library"
                self._set_scope_library(autoplay=False)  # Clear scope to Library
                print(f"[PlayGroup] key=None name='Library' count={len(self.playlist)} model={self.playback_model}")
            elif key in ('youtube', 'bilibili', 'local-media'):
                # Handle YouTube, Bilibili, and Local Media
                indices = self._iter_indices_for_group(key)
                print(f"[PlayGroup] key={key!r} name={name!r} count={len(indices)} model={self.playback_model}")
                if not indices:
                    self.status.showMessage(f"No items found for group '{name}'", 4000)
                    return
                self._set_scope_group(key, autoplay=False)  # Set scope to the selected group
            else:
                # Handle other playlists
                indices = self._iter_indices_for_group(key)
                print(f"[PlayGroup] key={key!r} name={name!r} count={len(indices)} model={self.playback_model}")
                if not indices:
                    self.status.showMessage(f"No items found for group '{name}'", 4000)
                    return
                self._set_scope_group(key, autoplay=False)

            # Update UI to reflect the change
            self._refresh_playlist_widget()  # Refresh playlist tree to show correct scope
            self._highlight_current_row()  # Highlight the current row if applicable
            self._update_up_next()  # Update the "Up Next" panel based on the new scope
        except Exception as e:
            # Handle any errors (e.g., invalid dropdown index)
            print(f"[PlayGroup] exception: {e}")
            self.status.showMessage(f"Error: Unable to set scope ({e})", 5000)

    def _update_group_toggle_visibility(self):
        """Update visibility of group-related UI elements based on playback model"""
        # Currently this is a placeholder - add any group UI updates here
        pass

    def _update_scope_label(self):
            """Update the dropdown to reflect the current playback scope."""
            try:
                # --- FIX: Check if the attribute exists before using it ---
                if not hasattr(self, 'scope_dropdown'):
                    return

                if self.play_scope is None:
                    # No specific group selected, default to "Library"
                    self.scope_dropdown.setCurrentText("Library")
                else:
                    # A group is selected (e.g., playlist or media type)
                    kind, key = self.play_scope
                    if kind == 'group':
                        # Update dropdown to show the correct group name
                        name = self._scope_title_from_key(key)
                        self.scope_dropdown.setCurrentText(name)
            except Exception as e:
                # Log any errors for debugging
                print(f"[ScopeLabel] Error updating scope label: {e}")   

    def _group_effective_key(self, raw_key, item=None):
        try:
            # Prefer normalized key stashed on the item
            if item is not None:
                try:
                    stored = item.data(0, Qt.UserRole + 1)
                    if stored:
                        return stored
                except Exception:
                    pass
            if raw_key in (None, False, '') and item is not None:
                txt = item.text(0) if hasattr(item, 'text') else ''
                if txt:
                    s = txt.strip()
                    if s.startswith('📃'):
                        s = s[1:].strip()
                    if s.endswith(')') and '(' in s:
                        s = s[:s.rfind('(')].strip()
                    if s:
                        return s
            return raw_key
        except Exception:
            return raw_key

    def _first_index_of_group(self, key):
        try:
            idxs = self._iter_indices_for_group(key)
            if idxs:
                return idxs[0]
        except Exception:
            pass
        return None

    def _set_scope_library(self, autoplay=False):
        self.play_scope = None
        self._update_scope_label()
        if autoplay and self.playlist:
            self.current_index = 0
            self.play_current()

    def _set_scope_group(self, key, autoplay=False):
        """Set the playback scope to a specific group and optionally autoplay."""
        try:
            indices = self._iter_indices_for_group(key)
            
            print(f"[PlayGroup] Setting scope for group '{key}' with {len(indices)} items")
            
            if not indices:
                print(f"[PlayGroup] No items found for group '{key}'")
                self.status.showMessage(f"No items found in group '{key}'", 4000)
                return
            
            # FIXED: Use play_scope not scope
            self.play_scope = ('group', key)
            self._update_scope_label()
            
            # If autoplay is enabled, start playback from the first item in the group
            if autoplay:
                print(f"[PlayGroup] Starting autoplay from index {indices[0]}")
                self.current_index = indices[0]
                self.play_current()
            
            # Update UI
            self._refresh_playlist_widget()
            self._update_up_next()
            
            print(f"[PlayGroup] Successfully set scope to group '{key}'")

        except Exception as e:
            print(f"[PlayGroup] Failed to set scope group '{key}': {e}")
            self.status.showMessage(f"Error playing group: {e}", 4000)

    def _recover_current_after_change(self, was_playing: bool):
        try:
            if not self.playlist:
                self.current_index = -1
                if was_playing:
                    try:
                        self.mpv.pause = True
                    except Exception:
                        pass
                self._update_tray();
                return
            indices = self._scope_indices()
            if not indices:
                # Fallback to entire list
                indices = list(range(len(self.playlist)))
            if self.current_index not in indices or not (0 <= self.current_index < len(self.playlist)):
                self.current_index = indices[0]
                if was_playing:
                    self.play_current()
                else:
                    self._highlight_current_row()
            else:
                # Still valid; no action
                pass
        except Exception:
            pass

    # Watched/completion utilities
    def _iter_indices_for_group(self, key):
        """Get all playlist indices for the given group key."""
        try:
            # print(f"[GroupIndices] Searching for key: {repr(key)}")
            
            # Primary: match either playlist_key OR playlist title
            indices = []
            for i, it in enumerate(self.playlist):
                playlist_key = it.get('playlist_key')
                playlist_name = it.get('playlist')
                
                if playlist_key == key or playlist_name == key:
                    indices.append(i)
            
            if indices:
                # print(f"[GroupIndices] Found {len(indices)} items via playlist matching")
                return indices

            # Fallback: Group by source type
            if key == 'youtube':
                indices = [i for i, it in enumerate(self.playlist) if it.get('type') == 'youtube']
            elif key == 'bilibili':
                indices = [i for i, it in enumerate(self.playlist) if it.get('type') == 'bilibili']
            elif key == 'local-media' or key == 'local':
                indices = [i for i, it in enumerate(self.playlist) if it.get('type') == 'local']
            elif key == 'miscellaneous':
                # Items without playlist_key AND without playlist
                indices = [i for i, it in enumerate(self.playlist) 
                        if not (it.get('playlist_key') or it.get('playlist'))]
            else:
                # Try case-insensitive matching as last resort
                key_lower = str(key).lower()
                for i, it in enumerate(self.playlist):
                    playlist_key = it.get('playlist_key') or ''
                    playlist_name = it.get('playlist') or ''
                    if (playlist_key.lower() == key_lower or 
                        playlist_name.lower() == key_lower):
                        indices.append(i)

            print(f"[GroupIndices] Final result for '{key}': {len(indices)} items")
            return indices
            
        except Exception as e:
            print(f"[GroupIndices] Error: {e}")
            return []

    def _debug_print_groups(self):
        try:
            from collections import Counter
            umb = Counter()
            types = Counter()
            for it in self.playlist:
                if not isinstance(it, dict):
                    continue
                k = it.get('playlist_key') or it.get('playlist')
                if k:
                    umb[k] += 1
                t = it.get('type')
                if t:
                    types[t] += 1
            if umb:
                print("[groups] playlist umbrellas:")
                for k, c in list(umb.items())[:10]:
                    print("   ", repr(k), c)
            else:
                print("[groups] no playlist umbrellas detected")
            if types:
                print("[groups] source types:")
                for k, c in types.items():
                    print("   ", k, c)
        except Exception as e:
            try:
                print(f"[groups] debug error: {e}")
            except Exception:
                pass

    def _clear_watched_in_library(self):
        try:
            was_playing = self._is_playing()
            before = len(self.playlist)
            self.playlist = [it for it in self.playlist if ((self._canonical_url_key(it.get('url')) not in self.completed_urls) and (it.get('url') not in self.completed_urls))]
            removed = before - len(self.playlist)
            if removed:
                self._save_current_playlist(); self._refresh_playlist_widget()
                self._recover_current_after_change(was_playing)
                self.status.showMessage(f"Removed {removed} watched items from Library", 5000)
            else:
                self.status.showMessage("No watched items to remove in Library", 3000)
        except Exception as e:
            self.status.showMessage(f"Clear watched failed: {e}", 4000)

    def _clear_watched_in_group(self, key):
        print(f"DEBUG: _clear_watched_in_group called with key: {key}")
        try:
            indices = set(self._iter_indices_for_group(key))
            if not indices:
                self.status.showMessage("No items found for this group", 3000)
                return
                
            # Count watched items in this group
            watched_count = 0
            total_count = len(indices)
            for i in indices:
                if 0 <= i < len(self.playlist):
                    url = self.playlist[i].get('url')
                    if url and ((self._canonical_url_key(url) in self.completed_urls) or (url in self.completed_urls)):
                        watched_count += 1
            
            if watched_count == 0:
                group_name = self._scope_title_from_key(key)
                self.status.showMessage(f"No watched items found in '{group_name}'", 3000)
                return
                
            group_name = self._scope_title_from_key(key)
            
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Remove Watched Videos", 
                f"Remove all watched videos from '{group_name}'?\n\n"
                f"📊 {watched_count} watched videos will be removed\n"
                f"📊 {total_count - watched_count} unwatched videos will remain\n\n"
                f"⚠️  This will delete the watched videos from this group.\n"
                f"You'll need to re-add them if you want them back.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # Default to No for safety
            )
            
            if reply != QMessageBox.Yes:
                return
                
            # Proceed with original logic
            was_playing = self._is_playing()
            before = len(self.playlist)
            self.playlist = [it for i, it in enumerate(self.playlist) if not (i in indices and ((self._canonical_url_key(it.get('url')) in self.completed_urls) or (it.get('url') in self.completed_urls)))]
            removed = before - len(self.playlist)
            if removed:
                self._save_current_playlist()
                self._refresh_playlist_widget()
                self._recover_current_after_change(was_playing)
                self.status.showMessage(f"Removed {removed} watched items from {group_name}", 5000)
            else:
                self.status.showMessage("No watched items to remove in group", 3000)
        except Exception as e:
            self.status.showMessage(f"Clear watched failed: {e}", 4000)

    def _play_unwatched_in_group(self, key):
        try:
            idxs = self._iter_indices_for_group(key)
            for i in idxs:
                u = self.playlist[i].get('url')
                if (not u) or ((self._canonical_url_key(u) not in self.completed_urls) and (u not in self.completed_urls)):
                    self.play_scope = ('group', key)
                    self._update_scope_label()
                    self.current_index = i
                    self.play_current()
                    return
            name = self._scope_title_from_key(key)
            self.status.showMessage(f"No unwatched items in {name}", 4000)
        except Exception as e:
            try:
                self.status.showMessage(f"Play unwatched failed: {e}", 4000)
            except Exception:
                pass

    def _mark_group_unwatched(self, key):
        try:
            urls = []
            for i in self._iter_indices_for_group(key):
                u = self.playlist[i].get('url')
                if u:
                    urls.append(u)
            changed = 0
            for u in urls:
                if u in self.completed_urls:
                    self.completed_urls.discard(u)
                    changed += 1
            if changed:
                self._save_completed(); self.status.showMessage(f"Marked {changed} items unwatched", 4000)
            else:
                self.status.showMessage("No items needed changes", 3000)
        except Exception as e:
            self.status.showMessage(f"Mark group unwatched failed: {e}", 4000)

    def _mark_item_unwatched(self, url):
        try:
            removed = False
            keys = [url, self._canonical_url_key(url)]
            for k in keys:
                if k and k in self.completed_urls:
                    self.completed_urls.discard(k); removed = True
            # Fallback fuzzy match on video id
            if not removed:
                import re
                lo = (url or '').lower()
                vid = None
                if ('youtube.com' in lo) or ('youtu.be' in lo):
                    try:
                        vid = self._canonical_url_key(url).split('=')[-1]
                    except Exception:
                        vid = None
                elif 'bilibili.com' in lo:
                    try:
                        m = re.search(r'/video/([A-Za-z0-9]+)', url)
                        vid = m.group(1) if m else None
                    except Exception:
                        vid = None
                if vid:
                    for k in list(self.completed_urls):
                        if vid.lower() in k.lower():
                            self.completed_urls.discard(k); removed = True
            if removed:
                self._save_completed(); self.status.showMessage("Item marked unwatched", 3000)
            else:
                self.status.showMessage("Item already unwatched", 3000)
        except Exception as e:
            self.status.showMessage(f"Mark unwatched failed: {e}", 4000)

    def _play_from_beginning(self, idx: int, url: str):
        try:
            self._clear_resume_for_url(url)
        except Exception:
            pass
        # Force playing even if item is marked completed (one-off)
        self._force_play_ignore_completed = True
        self._play_index(idx)

    def _play_from_here_in_group(self, idx: int):
        try:
            if not (0 <= idx < len(self.playlist)):
                return
            it = self.playlist[idx]
            key = it.get('playlist_key') or it.get('playlist') or it.get('type')
            if not key:
                # No sensible group; just play the item
                self.current_index = idx; self.play_current(); return
            # Set scope and play this index
            self.play_scope = ('group', key)
            self._update_scope_label()
            self.current_index = idx
            self.play_current()
        except Exception:
            pass

    def _open_in_browser(self, url: str):
        """Opens the given URL in the default web browser."""
        try:
            if not url:
                self.status.showMessage("No URL to open", 2000)
                return
                
            import webbrowser
            import subprocess
            import platform
            
            # Clean the URL
            url = str(url).strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                if 'youtube.com' in url or 'youtu.be' in url or 'bilibili.com' in url:
                    url = 'https://' + url
                else:
                    self.status.showMessage("Invalid URL format", 3000)
                    return
            
            logger.info(f"Opening URL in browser: {url}")
            
            # Try multiple methods for better compatibility
            try:
                # Method 1: webbrowser module (most reliable)
                webbrowser.open(url)
                self.status.showMessage("Opened in browser", 2000)
                return
            except Exception as e1:
                logger.warning(f"webbrowser.open failed: {e1}")
                
            # Method 2: Platform-specific commands
            system = platform.system()
            try:
                if system == 'Windows':
                    subprocess.run(['start', url], shell=True, check=True)
                elif system == 'Darwin':  # macOS
                    subprocess.run(['open', url], check=True)
                else:  # Linux and others
                    subprocess.run(['xdg-open', url], check=True)
                self.status.showMessage("Opened in browser", 2000)
                return
            except Exception as e2:
                logger.warning(f"Platform-specific open failed: {e2}")
                
            # If all methods fail
            raise Exception("All browser opening methods failed")
            
        except Exception as e:
            logger.error(f"Failed to open URL in browser: {e}")
            self.status.showMessage(f"Open in browser failed: {str(e)}", 3000)

    def _copy_url(self, url: str):
        """Copies the given URL to the system clipboard."""
        try:
            # print(f"[DEBUG] _copy_url called with URL: {repr(url)}")
            
            if not url:
                print("[DEBUG] URL is empty or None")
                self.status.showMessage("No URL to copy", 2000)
                return
                
            url_str = str(url).strip()
            # print(f"[DEBUG] Processed URL string: {repr(url_str)}")
            
            # Try QGuiApplication first, fallback to QApplication
            clipboard = None
            try:
                clipboard = QGuiApplication.clipboard()
                # print("[DEBUG] Using QGuiApplication.clipboard()")
            except Exception as e1:
                # print(f"[DEBUG] QGuiApplication.clipboard() failed: {e1}")
                try:
                    clipboard = QApplication.clipboard()
                    # print("[DEBUG] Using QApplication.clipboard()")
                except Exception as e2:
                    pass
                    # print(f"[DEBUG] QApplication.clipboard() failed: {e2}")
                    
            if not clipboard:
                raise Exception("Could not access system clipboard")
                
            # print(f"[DEBUG] Clipboard object obtained: {type(clipboard)}")
            
            # Set the text
            clipboard.setText(url_str)
            # print(f"[DEBUG] setText() called successfully")
            
            # Verify the copy worked
            copied_text = clipboard.text()
            # print(f"[DEBUG] Verification - clipboard now contains: {repr(copied_text)}")
            
            if copied_text == url_str:
                self.status.showMessage("URL copied to clipboard", 2000)
                logger.info(f"Successfully copied URL to clipboard: {url_str[:50]}...")
            else:
                self.status.showMessage("Copy may have failed - clipboard content differs", 3000)
                # print(f"[DEBUG] WARNING: Expected {repr(url_str)}, got {repr(copied_text)}")
                
        except Exception as e:
            # print(f"[DEBUG] Exception in _copy_url: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to copy URL to clipboard: {e}")
            self.status.showMessage(f"Copy failed: {str(e)}", 3000)

    def _expand_all_groups(self, expand: bool):
        try:
            root = self.playlist_tree.topLevelItem(0)
            if not root:
                return
            def visit(node):
                data = node.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'group':
                    node.setExpanded(bool(expand))
                for i in range(node.childCount()):
                    visit(node.child(i))
            for i in range(root.childCount()):
                visit(root.child(i))
        except Exception:
            pass

    def _export_m3u(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            if not self.playlist:
                QMessageBox.information(self, "Export", "No items to export."); return
            path, _ = QFileDialog.getSaveFileName(self, "Export M3U", "playlist.m3u8", "M3U Playlists (*.m3u *.m3u8)")
            if not path:
                return
            with open(path, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for it in self.playlist:
                    title = it.get('title') or it.get('url') or ''
                    url = it.get('url') or ''
                    f.write(f"#EXTINF:-1,{title}\n{url}\n")
            self.status.showMessage(f"Exported to {Path(path).name}", 4000)
        except Exception as e:
            self.status.showMessage(f"Export failed: {e}", 4000)

    def _import_m3u(self):
        try:
            from PySide6.QtWidgets import QFileDialog
            path, _ = QFileDialog.getOpenFileName(self, "Import M3U", "", "M3U Playlists (*.m3u *.m3u8)")
            if not path:
                return
            added = 0
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    s = line.strip()
                    if not s or s.startswith('#'):
                        continue
                    u = s
                    # Guess type
                    t = 'local'
                    lo = u.lower()
                    if 'youtube.com' in lo or 'youtu.be' in lo:
                        t = 'youtube'
                    elif 'bilibili.com' in lo:
                        t = 'bilibili'
                    title = Path(u).name if t == 'local' and '://' not in u else u
                    # Deduplicate by URL
                    if any(it.get('url') == u for it in self.playlist):
                        continue
                    self.playlist.append({'title': title, 'url': u, 'type': t})
                    added += 1
            if added:
                self._save_current_playlist(); self._refresh_playlist_widget()
            self.status.showMessage(f"Imported {added} items", 4000)
        except Exception as e:
            self.status.showMessage(f"Import failed: {e}", 4000)

    def _move_to_top(self, idx: int):
        try:
            if not (0 <= idx < len(self.playlist)):
                return
            it = self.playlist.pop(idx)
            self.playlist.insert(0, it)
            if self.current_index == idx:
                self.current_index = 0
            elif idx < self.current_index:
                self.current_index -= 1
            self._save_current_playlist(); self._refresh_playlist_widget()
            self._highlight_current_row()
        except Exception:
            pass

    def _move_to_bottom(self, idx: int):
        try:
            if not (0 <= idx < len(self.playlist)):
                return
            it = self.playlist.pop(idx)
            self.playlist.append(it)
            if self.current_index == idx:
                self.current_index = len(self.playlist) - 1
            elif idx < self.current_index:
                self.current_index -= 1
            self._save_current_playlist(); self._refresh_playlist_widget()
            self._highlight_current_row()
        except Exception:
            pass

    # Actions
    def _maybe_offer_clipboard_url(self):
            """
            Check clipboard for a media URL and add it directly to the playlist.
            Returns True if a URL was added, False otherwise.
            """
            try:
                cb_text = QApplication.clipboard().text() or ""
                url = cb_text.strip()
                if not url:
                    return False

                # Basic validation for media URLs
                url_lower = url.lower()
                is_media = ('youtube.com' in url_lower or 'youtu.be' in url_lower or 
                            'bilibili.com' in url_lower or self._is_local_file(url))
                if not is_media:
                    return False

                # Avoid re-adding the same URL from the clipboard repeatedly
                if getattr(self, '_last_clipboard_offer', "") == url:
                    return True # Act as if handled to prevent "not a media url" message

                # Avoid duplicates already in the playlist
                if any(isinstance(it, dict) and it.get('url') == url for it in self.playlist):
                    self.status.showMessage("This item is already in the playlist", 3000)
                    self._last_clipboard_offer = url
                    return True

                # --- Optimistic Add ---
                self._add_url_to_playlist(url)
                self.status.showMessage("Added from clipboard (Ctrl+Z to undo)", 3500)
                self._last_clipboard_offer = url
                return True

            except Exception as e:
                self.status.showMessage(f"Clipboard check failed: {e}", 4000)
                return False

    def _add_url_to_playlist(self, url: str):
        try:
            url_lower = url.lower()
            if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                media_type = 'youtube'
            elif 'bilibili.com' in url_lower:
                media_type = 'bilibili'
            else:
                media_type = 'local'

            # Check if this is a playlist URL
            if media_type == 'youtube':
                is_playlist = ('list=' in url or '/playlist' in url_lower)
            elif media_type == 'bilibili':
                is_playlist = (
                    'list=' in url or '/playlist' in url_lower or '/series' in url_lower or
                    'space.bilibili.com' in url_lower  # Add support for Bilibili space URLs
                )
            else:
                is_playlist = False

            if is_playlist:
                # Handle playlist loading in the background
                self._show_loading("Loading playlist entries...")
                loader = PlaylistLoaderThread(url, media_type)
                self._playlist_loader = loader  # Keep a reference
                loader.itemsReady.connect(self._on_playlist_items_ready)
                loader.error.connect(lambda e: self._hide_loading(f"Playlist load failed: {e}", 5000))
                loader.finished.connect(loader.deleteLater)
                loader.start()
            else:
                # --- Fast path for single videos ---
                # Use a placeholder title to show something is happening
                item = {'title': f"[Loading...] {Path(url).name}", 'url': url, 'type': media_type}

                # Add item to the end of the list
                new_index = len(self.playlist)
                self.playlist.append(item)

                # Add to undo stack
                self._add_undo_operation('delete_items', {
                    'items': [{'index': new_index, 'item': item}],
                    'was_playing': self._is_playing(),
                    'old_current_index': self.current_index
                })

                # Update UI and save (non-blocking)
                self._add_single_item_to_tree(new_index, item)
                self._schedule_save_current_playlist()

                # Use parallel workers
                worker = self.ytdl_workers[self._worker_index]
                worker.resolve(url, media_type)
                self._worker_index = (self._worker_index + 1) % len(self.ytdl_workers)

        except Exception as e:
            self.status.showMessage(f"Failed to add media: {e}", 4000)

    def _fetch_all_durations(self):
        """Fetch durations for all items in playlist with cancel support"""
        if not self.playlist:
            return
        
        # Count items that need duration fetching
        items_needing_duration = [(i, item) for i, item in enumerate(self.playlist) 
                                if item.get('type') in ('youtube', 'bilibili') 
                                and not item.get('duration')]
        
        if not items_needing_duration:
            self.status.showMessage("All items already have duration info", 3000)
            return
        
        reply = QMessageBox.question(
            self, "Fetch Durations",
            f"Fetch durations for {len(items_needing_duration)} videos?\n\nThis may take several minutes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Create duration fetcher with cancel support
            self._duration_fetcher = DurationFetcher(items_needing_duration, self)
            self._duration_fetcher.progressUpdated.connect(self._on_duration_progress)
            self._duration_fetcher.durationReady.connect(self._on_duration_ready)
            self._duration_fetcher.finished.connect(self._on_duration_fetch_complete)
            
            # Show cancellable progress dialog
            self._show_duration_progress(len(items_needing_duration))
            self._duration_fetcher.start()

    def _show_duration_progress(self, total):
        """Show cancellable progress dialog for duration fetching"""
        from PySide6.QtWidgets import QProgressDialog
        self._duration_progress = QProgressDialog("Fetching durations...", "Cancel", 0, total, self)
        self._duration_progress.setWindowModality(Qt.WindowModal)
        self._duration_progress.canceled.connect(self._cancel_duration_fetch)
        self._duration_progress.show()

    def _cancel_duration_fetch(self):
        """Cancel the duration fetching operation"""
        if hasattr(self, '_duration_fetcher'):
            self._duration_fetcher.stop()

    def _on_duration_progress(self, current, total):
        """Update progress dialog"""
        if hasattr(self, '_duration_progress'):
            self._duration_progress.setValue(current)
            self._duration_progress.setLabelText(f"Fetching durations... ({current}/{total})")

    def _on_duration_ready(self, index, duration):
        """Store duration when it's fetched"""
        if 0 <= index < len(self.playlist):
            self.playlist[index]['duration'] = duration
            # Save to persistence
            self._save_current_playlist()

    def _on_duration_fetch_complete(self):
        """Clean up after duration fetching"""
        if hasattr(self, '_duration_progress'):
            self._duration_progress.close()
        self.status.showMessage("Duration fetching complete", 3000)

    def _schedule_save_current_playlist(self):
        """Schedule saving the current playlist with debounce."""
        if not hasattr(self, '_save_timer'):
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self._save_current_playlist)
        self._save_timer.start(2000)  # Save after 2 seconds of inactivity

    def _add_single_item_to_tree(self, index: int, item: dict):
        """Add a single item to the tree without full refresh - MUCH faster"""
        try:
            icon = playlist_icon_for_type(item.get('type'))
            
            # Check if this should go in a group
            has_playlist = item.get('playlist') or item.get('playlist_key')
            should_group_singles = getattr(self, 'group_singles', False)
            
            if has_playlist:
                # This item belongs to a specific playlist group
                
                # --- FIX: Save the expansion state before refreshing ---
                expansion_state = self._get_tree_expansion_state()
                self._refresh_playlist_widget_full(expansion_state=expansion_state)
            elif should_group_singles:
                # Add to miscellaneous group
                misc_group = self._find_or_create_misc_group()
                node = QTreeWidgetItem([item.get('title', 'Unknown')])
                if isinstance(icon, QIcon):
                    node.setIcon(0, icon)
                else:
                    node.setText(0, f"{icon} {item.get('title', 'Unknown')}")
                node.setFont(0, self._font_serif_no_size(italic=True, bold=True))
                node.setData(0, Qt.UserRole, ('current', index, item))
                # Set loading style directly on the item
                font = node.font(0)
                font.setItalic(True)
                node.setFont(0, font)
                node.setForeground(0, QColor("#888888"))
                misc_group.addChild(node)
                # Update group header count
                misc_group.setText(0, f"🎵 Miscellaneous ({misc_group.childCount()})")
            else:
                # Add as top-level item
                node = QTreeWidgetItem(self.playlist_tree, [item.get('title', 'Unknown')])
                if isinstance(icon, QIcon):
                    node.setIcon(0, icon)
                else:
                    node.setText(0, f"{icon} {item.get('title', 'Unknown')}")
                node.setFont(0, self._font_serif_no_size(italic=True, bold=True))
                node.setData(0, Qt.UserRole, ('current', index, item))
                # Set loading style directly on the item
                font = node.font(0)
                font.setItalic(True)
                node.setFont(0, font)
                node.setForeground(0, QColor("#888888"))
            
            # Show main content if we were showing empty state
            if self.playlist_stack.currentIndex() == 1:
                self.playlist_stack.setCurrentIndex(0)
                
        except Exception as e:
            print(f"Add single item to tree failed: {e}")
            # Fallback to full refresh
            self._refresh_playlist_widget_full()

    def _find_or_create_misc_group(self):
        """Find existing miscellaneous group or create it"""
        # Look for existing misc group
        for i in range(self.playlist_tree.topLevelItemCount()):
            item = self.playlist_tree.topLevelItem(i)
            if item:
                data = item.data(0, Qt.UserRole)
                if isinstance(data, tuple) and data[0] == 'group' and data[1] == 'miscellaneous':
                    return item
        
        # Create new misc group
        gnode = QTreeWidgetItem(self.playlist_tree, [f"🎵 Miscellaneous (0)"])
        gnode.setFont(0, self._font_serif_no_size(italic=True, bold=True))
        gnode.setData(0, Qt.UserRole, ('group', 'miscellaneous'))
        gnode.setData(0, Qt.UserRole + 1, 'miscellaneous')
        gnode.setExpanded(True)  # Expand by default for new items
        return gnode

    def _resolve_title_background(self, item: dict, media_type: str):
        """Resolve title in background without blocking UI."""
        try:
            worker = TitleResolveWorker([item], media_type)
            self._title_workers.append(worker)
            worker.titleResolved.connect(self._on_title_resolved)
            worker.error.connect(lambda e: print(f"Background title resolve error: {e}"))
            worker.finished.connect(lambda: self._cleanup_title_worker(worker))
            worker.start()
        except Exception as e:
            print(f"Background title resolve setup failed: {e}")

    def _cleanup_title_worker(self, worker):
        """Clean up finished title worker."""
        try:
            if worker in self._title_workers:
                self._title_workers.remove(worker)
            worker.deleteLater()
        except Exception:
            pass        
        
    def add_link_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(self, "Add Media Link", "Enter YouTube or Bilibili URL or Playlist:")
        if ok and url:
            t = 'youtube' if ('youtube.com' in url or 'youtu.be' in url) else ('bilibili' if 'bilibili.com' in url else 'local')
            # Try to detect if this is a playlist and load entries in background
        if t == 'youtube':
            will_try_playlist = ('list=' in url or '/playlist' in url.lower())
        elif t == 'bilibili':
            will_try_playlist = (
                'list=' in url or '/playlist' in url.lower() or '/series' in url.lower() or
                'space.bilibili.com' in url.lower()
            )
        else:
            will_try_playlist = False
            if will_try_playlist:
                self._show_loading("Loading playlist entries...")
                loader = PlaylistLoaderThread(url, t)
                self._playlist_loader = loader
                loader.itemsReady.connect(self._on_playlist_items_ready)
                loader.error.connect(lambda e: self.status.showMessage(e, 5000))
                loader.finished.connect(loader.deleteLater)
                loader.start()
            else:
                # Single item: append immediately but resolve title async
                title = url
                item = {'title': title, 'url': url, 'type': t}
                self.playlist.append(item)
                self._save_current_playlist()
                self._refresh_playlist_widget()
                # Spawn TitleResolveWorker for this single item
                try:
                    w = TitleResolveWorker([item], t)
                    self._title_workers.append(w)
                    w.titleResolved.connect(self._on_title_resolved)
                    w.error.connect(lambda e: self.status.showMessage(e, 5000))
                    w.finished.connect(lambda w=w: (self._title_workers.remove(w) if w in self._title_workers else None))
                    w.start()
                except Exception:
                    pass

    def _on_add_media_clicked(self):
        """Handler for the Add Media button. Checks clipboard first, then opens dialog."""
        # Try to offer the clipboard URL. The function returns True if it handled it.
        was_handled = self._maybe_offer_clipboard_url()
        
        # If the clipboard was empty or the user declined, open the standard dialog.
        if not was_handled:
            self.add_link_dialog()            

    def add_local_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Media Files", "", "Media Files (*.mp4 *.avi *.mkv *.mov *.mp3 *.wav *.flac)")
        if not files:
            return
        for f in files:
            self.playlist.append({'title': Path(f).name, 'url': f, 'type': 'local'})
        self._save_current_playlist(); self._refresh_playlist_widget()

    def save_playlist(self):
        """Enhanced save playlist - replaces the old method"""
        if not hasattr(self, '_playlist_manager'):
            self._playlist_manager = EnhancedPlaylistManager(self, APP_DIR)
        
        return self._playlist_manager.save_current_playlist()

    def load_playlist_dialog(self):
        print("DEBUG: load_playlist_dialog called - which version?")
        """Enhanced load playlist - replaces the old method"""
        if not hasattr(self, '_playlist_manager'):
            self._playlist_manager = EnhancedPlaylistManager(self, APP_DIR)
        
        return self._playlist_manager.load_playlist_dialog()
        def _unique_playlist_name(self, base):
            base = (base or 'Playlist').strip()
            if base not in self.saved_playlists:
                return base
            i = 2
            while f"{base} ({i})" in self.saved_playlists:
                i += 1
            return f"{base} ({i})"

    def on_tree_item_double_clicked(self, item, column):

        data = item.data(0, Qt.UserRole)
        if not isinstance(data, tuple):
            return

        kind = data[0]
        if kind == 'current':
            idx = data[1]
            self.play_scope = None
            self._update_scope_label()
            self._save_current_position()
            self.current_index = idx
            self.play_current()
            self._highlight_current_row()
            self._update_up_next()
        elif kind == 'group':
            try:
                # --- ADD THIS BLOCK to save the expansion state ---
                # Get the current state of all groups
                expansion_state = self._get_tree_expansion_state()
                raw_key = data[1]
                key = self._group_effective_key(raw_key, item)
                
                # Force the clicked group to be marked as EXPANDED in our state object
                if key:
                    expansion_state[key] = True
                # --- END of new block ---

                self.play_scope = ('group', key)
                self._update_scope_label()

                # --- MODIFY THIS LINE to use the saved state ---
                self._refresh_playlist_widget(expansion_state=expansion_state)

                # This playback logic remains the same
                if getattr(self, 'playback_model', 'scoped') == 'scoped':
                    indices = self._iter_indices_for_group(key)
                    if indices:
                        self.current_index = indices[0]
                        self.play_current()
                        self._highlight_current_row()
                    else:
                        self.status.showMessage(f"No items found in group '{key}'", 3000)
                else:
                    if item.childCount() > 0:
                        child = item.child(0)
                        cdata = child.data(0, Qt.UserRole)
                        if isinstance(cdata, tuple) and cdata[0] == 'current':
                            idx = cdata[1]
                            self._save_current_position()
                            self.current_index = idx
                            self.play_current()
                            self._highlight_current_row()

                self._update_up_next()

            except Exception as e:
                print(f"Error while setting group scope: {e}")

    def _handle_playlist_mouse_press(self, event):
        """Handle middle mouse clicks on playlist items"""
        try:
            if event.button() == Qt.MiddleButton:
                item = self.playlist_tree.itemAt(event.position().toPoint())
                if item:
                    data = item.data(0, Qt.UserRole)
                    if isinstance(data, tuple) and data[0] == 'group':
                        # Toggle expansion state for group headers
                        item.setExpanded(not item.isExpanded())
                        return True  # Event handled
            
            # Let other mouse events pass through normally
            return False
        except Exception as e:
            print(f"Mouse press handler error: {e}")
            return False            
        
    def _create_mouse_press_handler(self):
        """Create a mouse press handler that supports both middle click and normal functionality"""
        original_mouse_press = self.playlist_tree.mousePressEvent
        
        def enhanced_mouse_press(event):
            # Handle middle mouse clicks
            if self._handle_playlist_mouse_press(event):
                return  # Event was handled, don't pass through
            
            # Pass through to original handler for all other clicks
            original_mouse_press(event)
        
        return enhanced_mouse_press    

    def _show_playlist_context_menu(self, pos):
        selected_items = self.playlist_tree.selectedItems()
        if not selected_items:
            return

        menu = QMenu()  # <-- Single menu object for all cases
        self._apply_menu_theme(menu)

        # --- CASE 1: Multiple items are selected ---
        if len(selected_items) > 1:
            total_indices = set()
            group_count = 0
            individual_count = 0
            group_keys = []

            for selected_item in selected_items:
                data = selected_item.data(0, Qt.UserRole)
                if isinstance(data, tuple):
                    kind = data[0]
                    if kind == 'group':
                        group_count += 1
                        raw_key = data[1] if len(data) > 1 else None
                        actual_key = self._group_effective_key(raw_key, selected_item)
                        
                        if actual_key:
                            indices = self._iter_indices_for_group(actual_key)
                            total_indices.update(indices)
                            group_keys.append(actual_key)
                            
                    elif kind == 'current':
                        individual_count += 1
                        idx = data[1]
                        if 0 <= idx < len(self.playlist):
                            total_indices.add(idx)

            if total_indices:
                summary = []
                if group_count > 0:
                    summary.append(f"{group_count} group{'s' if group_count != 1 else ''}")
                if individual_count > 0:
                    summary.append(f"{individual_count} individual item{'s' if individual_count != 1 else ''}")
                summary_text = " + ".join(summary)

                menu.addAction(f"🗑️ Remove {summary_text} ({len(total_indices)} total items)").triggered.connect(
                    lambda: self._remove_selected_items()
                )
                menu.addSeparator()
                menu.addAction(f"🔄 Reset Playback Positions ({len(total_indices)} items)").triggered.connect(
                    lambda: self._reset_selected_playback_positions(list(total_indices))
                )
                menu.addAction(f"✅ Mark as Unwatched ({len(total_indices)} items)").triggered.connect(
                    lambda: self._mark_selected_unwatched(list(total_indices))
                )
            else:
                menu.addAction("⚠ No valid items found in selection")

        # --- CASE 2: Exactly one item is selected ---
        elif len(selected_items) == 1:
            item = selected_items[0]
            data = item.data(0, Qt.UserRole)
            if not isinstance(data, tuple):
                return

            kind, *rest = data
            if kind == 'current':
                idx, it = rest[0], rest[1]
                url = it.get('url')

                menu.addAction("▶ Play").triggered.connect(lambda: self._play_index(idx))
                menu.addAction("⭐ Play Next").triggered.connect(lambda i=idx: self._queue_item_next(i))
                copy_action = menu.addAction("🔗 Copy URL")
                copy_action.triggered.connect(lambda checked=False, u=url: (
                    print(f"[DEBUG] Copy URL action triggered with URL: {repr(u)}"),
                    self._copy_url(u)
                )[1])
                menu.addAction("🗑️ Remove").triggered.connect(lambda: self._remove_index(idx))
                menu.addSeparator()
                menu.addAction("⏮️ Reset Playback Position").triggered.connect(lambda: self._clear_resume_for_url(url))
                menu.addAction("✅ Mark as Unwatched").triggered.connect(lambda u=url: self._mark_item_unwatched(u))

            elif kind == 'group':
                raw_key = rest[0] if rest else None
                actual_key = self._group_effective_key(raw_key, item)

                if actual_key:
                    indices = self._iter_indices_for_group(actual_key)
                    if indices:
                        menu.addAction("▶ Play Group").triggered.connect(
                            lambda checked=False, k=actual_key: self._set_scope_group(k, autoplay=True)
                        )
                        menu.addSeparator()
                        menu.addAction("🔄 Reset Playback Positions").triggered.connect(
                            lambda checked=False, k=actual_key: self._reset_group_playback_positions(k)
                        )
                        menu.addAction("✅ Mark Group as Unwatched").triggered.connect(
                            lambda checked=False, k=actual_key: self._mark_group_unwatched_enhanced(k)
                        )
                        menu.addSeparator()
                        menu.addAction(f"🗑️ Remove All ({len(indices)} items)").triggered.connect(
                            lambda checked=False, key=actual_key: self._remove_all_in_group(key)
                        )
                        menu.addAction("🧹 Remove Watched from Group").triggered.connect(
                            lambda checked=False, k=actual_key: self._clear_watched_in_group(k)
                        )
                    else:
                        menu.addAction(f"❌ No items found for group")
                else:
                    menu.addAction("❌ Unable to identify group")
        
        # Show the menu (single call for all cases)
        menu.exec(self.playlist_tree.viewport().mapToGlobal(pos))

# Add this debug version to your _remove_all_in_group method:

    def _remove_all_in_group(self, group_key):
        """Remove all items in a specific group with undo support"""
        print(f"[DEBUG] _remove_all_in_group called with key: '{group_key}'")
        
        try:
            # Get all indices for this group
            indices = list(self._iter_indices_for_group(group_key))
            
            if not indices:
                print(f"[DEBUG] No items found for group key: {group_key}")
                return
                
            print(f"[DEBUG] Found {len(indices)} items to remove for key: {group_key}")
            
            # Confirm deletion if many items
            if len(indices) > 5:
                reply = QMessageBox.question(
                    self, 
                    "Remove Group", 
                    f"Remove {len(indices)} items from this group?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                
            # --- FIX: Remember which folders are open ---
            expansion_state = self._get_tree_expansion_state()
            # --- FIX: Forget the last pasted link so it can be re-added ---
            self._last_clipboard_offer = ""    
            
            # Store undo data BEFORE deletion
            was_playing = self._is_playing()
            old_current_index = self.current_index
            
            # Collect items for undo (in original order)
            items_for_undo = []
            for i in sorted(indices):
                if 0 <= i < len(self.playlist):
                    items_for_undo.append({
                        'index': i,
                        'item': self.playlist[i].copy()  # Deep copy
                    })
            
            # Prepare undo data
            undo_data = {
                'items': items_for_undo,
                'was_playing': was_playing,
                'old_current_index': old_current_index,
                'group_key': group_key
            }
            
            # Remove items in reverse order to avoid index shifting
            for i in sorted(indices, reverse=True):
                print(f"[DEBUG] Removing item at index: {i}")
                if 0 <= i < len(self.playlist):
                    del self.playlist[i]
                    
                    # Update current_index if affected
                    if self.current_index == i:
                        self.current_index = -1
                    elif i < self.current_index:
                        self.current_index -= 1
            
            # Add to undo stack AFTER successful deletion
            self._add_undo_operation('delete_group', undo_data)
            
            # Save and refresh
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            
            # --- FIX: Re-open the folders that were open before ---
            self._refresh_playlist_widget(expansion_state=expansion_state)

            # Show status message
            group_name = group_key[:30] + "..." if len(group_key) > 30 else group_key
            self.status.showMessage(f"Removed {len(indices)} items from '{group_name}' (Ctrl+Z to undo)", 4000)
            
        except Exception as e:
            print(f"[DEBUG] Error in _remove_all_in_group: {e}")
            self.status.showMessage(f"Remove group failed: {e}", 4000)

    def _debug_group_resolution(self, item, raw_key):
        """Debug helper to understand group key resolution issues."""
        try:
            print(f"\n[DEBUG] Group Resolution Debug:")
            print(f"  Item text: {repr(item.text(0))}")
            print(f"  Raw key: {repr(raw_key)}")
            print(f"  UserRole data: {repr(item.data(0, Qt.UserRole))}")
            print(f"  UserRole+1 data: {repr(item.data(0, Qt.UserRole + 1))}")
            
            # Show all unique playlist keys/names
            keys = set()
            names = set()
            for playlist_item in self.playlist:
                pk = playlist_item.get('playlist_key')
                pn = playlist_item.get('playlist')
                if pk: keys.add(pk)
                if pn: names.add(pn)
            
            print(f"  Available playlist_keys: {sorted(keys)}")
            print(f"  Available playlist names: {sorted(names)}")
            
            # Test all potential keys
            test_keys = [raw_key]
            if item.data(0, Qt.UserRole + 1):
                test_keys.append(item.data(0, Qt.UserRole + 1))
            
            item_text = item.text(0)
            if item_text and item_text.startswith('📃 '):
                group_name = item_text[2:].strip()
                if '(' in group_name and group_name.endswith(')'):
                    group_name = group_name[:group_name.rfind('(')].strip()
                test_keys.append(group_name)
            
            for test_key in test_keys:
                if test_key:
                    indices = self._iter_indices_for_group(test_key)
                    print(f"  Testing key {repr(test_key)}: {len(indices)} items")
            
            self.status.showMessage("Group debug info printed to console", 3000)
            
        except Exception as e:
            print(f"[DEBUG] Group resolution debug failed: {e}")

    def _force_play_anyway(self, idx: int):  # <-- This is the next existing method
        """Play item regardless of completion status"""
        try:
            if 0 <= idx < len(self.playlist):
                self._force_play_ignore_completed = True
                self._play_index(idx)
        except Exception:
            pass

    def _play_index(self, idx):
        if 0 <= idx < len(self.playlist):
            self.current_index = idx; self.play_current(); self._update_up_next()

    def _move_item(self, idx, delta):
        j = idx + delta
        if 0 <= idx < len(self.playlist) and 0 <= j < len(self.playlist):
            self.playlist[idx], self.playlist[j] = self.playlist[j], self.playlist[idx]
            self._save_current_playlist(); self._refresh_playlist_widget()
            self.current_index = j

    def _queue_item_next(self, idx):
        try:
            if not (0 <= idx < len(self.playlist)):
                return
            if self.current_index == -1:
                # Nothing playing: make it first
                it = self.playlist.pop(idx)
                self.playlist.insert(0, it)
                self.current_index = 0
                self._save_current_playlist(); self._refresh_playlist_widget(); self.play_current(); return
            next_pos = self.current_index + 1
            if idx == next_pos:
                return  # already next
            it = self.playlist.pop(idx)
            # Adjust current_index if the removed index was before current
            if idx < self.current_index:
                self.current_index -= 1
            next_pos = min(next_pos, len(self.playlist))
            self.playlist.insert(next_pos, it)
            self._save_current_playlist(); self._refresh_playlist_widget()
            self.status.showMessage("Queued to play next", 3000)
        except Exception:
            pass

    def _remove_index(self, idx):
        import traceback
        print("🗑️ _remove_index called!")
        # print("📍 Called from:", traceback.format_stack()[-2].strip())  # Shows who called this
        if 0 <= idx < len(self.playlist):

            # --- FIX: Remember which folders are open ---
            expansion_state = self._get_tree_expansion_state()
            # --- FIX: Forget the last pasted link so it can be re-added ---
            self._last_clipboard_offer = ""

            # Store undo data BEFORE deletion
            was_playing = self._is_playing()
            old_current_index = self.current_index
            
            # Store the item being deleted
            item_to_delete = self.playlist[idx].copy()  # Deep copy
            
            # Prepare undo data
            undo_data = {
                'items': [{
                    'index': idx,
                    'item': item_to_delete
                }],
                'was_playing': was_playing,
                'old_current_index': old_current_index
            }
            
            # Perform the deletion
            del self.playlist[idx]
            
            # Update current_index if affected
            if self.current_index == idx:
                self.current_index = -1
            elif idx < self.current_index:
                self.current_index -= 1
            
            # Add to undo stack AFTER successful deletion
            self._add_undo_operation('delete_items', undo_data)
            
            # Save and refresh
            self._save_current_playlist()
            self._refresh_playlist_widget()

            # --- FIX: Re-open the folders that were open before ---
            self._refresh_playlist_widget(expansion_state=expansion_state)
            
            # Adjust current_index bounds
            if self.current_index >= len(self.playlist):
                self.current_index = len(self.playlist) - 1
                
            # Recover playback state
            self._recover_current_after_change(was_playing)
            
            # Show status message
            self.status.showMessage("Removed 1 item (Ctrl+Z to undo)", 3000)

    def _clear_resume_for_url(self, url):
        try:
            cleared = False
            # Try exact and canonical keys
            keys = [url, self._canonical_url_key(url)]
            for k in keys:
                if k and k in self.playback_positions:
                    del self.playback_positions[k]
                    cleared = True
            # Fallback: fuzzy match by video id (YouTube/Bilibili)
            if not cleared:
                alt = self._find_resume_key_for_url(url)
                if alt and alt in self.playback_positions:
                    del self.playback_positions[alt]
                    cleared = True
            self._save_positions()
            self.status.showMessage("Cleared resume point" if cleared else "No resume point found", 3000)
        except Exception as e:
            self.status.showMessage(f"Clear resume failed: {e}", 4000)

    def _add_undo_operation(self, operation_type, data):
        """Add an operation to the undo stack"""
        try:
            undo_op = {
                'type': operation_type,
                'data': data,
                'timestamp': time.time()
            }
            
            self._undo_stack.append(undo_op)
            
            # Limit undo stack size
            if len(self._undo_stack) > self._max_undo_operations:
                self._undo_stack.pop(0)  # Remove oldest operation
                
            print(f"[UNDO] Added operation: {operation_type}")
            
        except Exception as e:
            print(f"[UNDO] Error adding operation: {e}")

    def _perform_undo(self):
        """Enhanced undo method that handles playlist manager operations"""
        try:
            if not self._undo_stack:
                self.status.showMessage("Nothing to undo", 2000)
                return
                
            operation = self._undo_stack.pop()
            op_type = operation['type']
            op_data = operation['data']
            
            print(f"[UNDO] Performing undo: {op_type}")
            
            if op_type == 'load_playlist':
                # Handle playlist load undo
                try:
                    self.playlist = op_data['old_playlist']
                    self.current_index = op_data['old_current_index']
                    was_playing = op_data['was_playing']
                    
                    self._save_current_playlist()
                    self._refresh_playlist_widget()
                    self._recover_current_after_change(was_playing)
                    
                except Exception as e:
                    print(f"[UNDO] Error restoring playlist load: {e}")
                    
            elif op_type == 'delete_items':
                self._undo_delete_items(op_data)
            elif op_type == 'delete_group':
                self._undo_delete_group(op_data)
            elif op_type == 'clear_playlist':
                self._undo_clear_playlist(op_data)
            elif op_type == 'move_items':
                self._undo_move_items(op_data)
            else:
                self.status.showMessage(f"Cannot undo operation: {op_type}", 3000)
                # Put it back if we can't handle it
                self._undo_stack.append(operation)
                return
                
            self.status.showMessage(f"Undid: {op_type.replace('_', ' ').title()}", 3000)
            
        except Exception as e:
            print(f"[UNDO] Error performing undo: {e}")
            self.status.showMessage(f"Undo failed: {e}", 3000)


    def _undo_delete_items(self, data):
        """Restore deleted individual items"""
        try:
            items_data = data['items']
            was_playing = data['was_playing']
            old_current_index = data['old_current_index']
            
            # Restore items to their original positions
            for item_info in reversed(items_data):  # Reverse to maintain order
                index = item_info['index']
                item = item_info['item']
                
                # Insert at original position
                if index <= len(self.playlist):
                    self.playlist.insert(index, item)
                else:
                    self.playlist.append(item)
            
            # Restore current index if it was affected
            if old_current_index >= 0:
                self.current_index = old_current_index
                
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            
        except Exception as e:
            print(f"[UNDO] Error restoring items: {e}")

    def _undo_delete_group(self, data):
        """Restore deleted group"""
        try:
            group_data = data['items']
            was_playing = data['was_playing']
            old_current_index = data['old_current_index']
            
            # Restore all items from the group
            for item_info in reversed(group_data):
                index = item_info['index']
                item = item_info['item']
                
                if index <= len(self.playlist):
                    self.playlist.insert(index, item)
                else:
                    self.playlist.append(item)
            
            if old_current_index >= 0:
                self.current_index = old_current_index
                
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            
        except Exception as e:
            print(f"[UNDO] Error restoring group: {e}")

    def _undo_clear_playlist(self, data):
        """Restore cleared playlist"""
        try:
            self.playlist = data['playlist'].copy()
            self.current_index = data['current_index']
            was_playing = data['was_playing']
            
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            
        except Exception as e:
            print(f"[UNDO] Error restoring playlist: {e}")        

    def _undo_move_items(self, data):
        """Restore playlist after a move/reorder operation."""
        try:
            self.playlist = data.get('playlist', [])
            self.current_index = data.get('current_index', -1)
            was_playing = data.get('was_playing', False)

            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            self.status.showMessage("Reverted playlist order", 3000)
        except Exception as e:
            logger.error(f"Undo move items failed: {e}")        

    def _clear_playlist(self):
        count = len(self.playlist)
        if count == 0:
            self.status.showMessage("Playlist is already empty", 2000)
            return
        
        # Enhanced confirmation with video count
        message = f"Delete {count} video{'s' if count != 1 else ''}?\n\nThis action can be undone with Ctrl+Z."
        if QMessageBox.question(self, "Clear Playlist", message, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            
            # --- FIX: Forget the last pasted link so it can be re-added ---
            self._last_clipboard_offer = ""
            
            # Store undo data
            undo_data = {
                'playlist': self.playlist.copy(),
                'current_index': self.current_index,
                'was_playing': self._is_playing()
            }
            
            # Clear playlist
            self.playlist.clear()
            self.current_index = -1
            
            # Add to undo stack
            self._add_undo_operation('clear_playlist', undo_data)
            
            self._save_current_playlist()
            self._refresh_playlist_widget()
            
            self.status.showMessage(f"Cleared {count} videos (Ctrl+Z to undo)", 4000)

    def _play_all_library(self):
            """Plays the entire library from the beginning."""
            # This section de-duplicates your playlist, which seems intentional.
            seen = set()
            combined = []
            for it in self.playlist:
                u = it.get('url')
                if not u or u in seen:
                    continue
                seen.add(u)
                combined.append({'title': it.get('title', u), 'url': u, 'type': it.get('type'), 'playlist': it.get('playlist')})
            
            if not combined:
                QMessageBox.information(self, "No Media", "No media found in current playlist.")
                return

            # --- THIS IS THE FIX ---
            # Explicitly clear the playback scope. This tells the 'Next' button
            # to use the entire library, not the last group you played.
            self.play_scope = None
            self.status.showMessage("Playing all media in library...", 3000)
            self._update_scope_label()
            # --- END FIX ---

            self.playlist = combined
            self.current_index = 0
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self.play_current()
            
    def _prepare_and_load_track(self, index, start_pos_ms=0, should_play=False):
        """A unified method to load a track into mpv, set options, and optionally play it."""
        if not (0 <= index < len(self.playlist)):
            return

        item = self.playlist[index]
        url = item.get('url', '')

        # --- Set site-specific options (from play_current) ---
        try:
            if item.get('type') == 'bilibili':
                self.mpv['referrer'] = item.get('url') or 'https://www.bilibili.com'
                self.mpv['http-header-fields'] = 'Referer: https://www.bilibili.com,Origin: https://www.bilibili.com,User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
                self.mpv['ytdl-raw-options'] = f"cookies={str(COOKIES_BILI)},add-header=Referer: https://www.bilibili.com,add-header=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                self.mpv['ytdl-format'] = 'bv*[vcodec^=avc1][height<=720]+ba/best[height<=720]/best'
            else:
                self.mpv['referrer'] = ''
                self.mpv['http-header-fields'] = ''
                self.mpv['ytdl-raw-options'] = ''
                self.mpv['ytdl-format'] = 'best[height<=720]/bv*[height<=720]+ba/best'
        except Exception as e:
            logger.error(f"Error setting mpv options: {e}")

        # --- Load the file with start position ---
        start_pos_sec = max(0.0, float(start_pos_ms) / 1000.0)
        logger.info(f"Loading track '{item.get('title')}': url={url}, start_sec={start_pos_sec}, play={should_play}")
        
        try:
            if start_pos_sec > 0:
                # FIX: Use proper format for start parameter
                self.mpv.loadfile(url, 'replace', start=str(start_pos_sec))
            else:
                self.mpv.loadfile(url, 'replace')
        except Exception as e:
            logger.error(f"mpv loadfile command failed: {e}")
            # Fallback to basic play method
            try:
                self.mpv.play(url)
                if start_pos_sec > 0:
                    # Apply seek after loading
                    QTimer.singleShot(500, lambda: setattr(self.mpv, 'time_pos', start_pos_sec))
            except Exception as e2:
                logger.error(f"Fallback play also failed: {e2}")

        # --- Set playback state ---
        self.mpv.pause = not should_play
        
        # --- Handle resume enforcement ---
        if start_pos_ms > 0:
            self._resume_target_ms = start_pos_ms
            self._resume_enforce_until = time.time() + 20.0
            self._restore_saved_position_attempt(url, start_pos_ms, 1)
            self.requestTimerSignal.emit(350, lambda: self._maybe_reapply_resume('start'))

        # --- Update UI ---
        self._set_track_title(item.get('title', 'Unknown'))
        self._update_up_next()
        self.progress.setValue(start_pos_ms)
        self.time_label.setText(format_time(start_pos_ms))
        
        # --- Defer highlight to ensure UI is ready ---
        QTimer.singleShot(100, self._highlight_current_row)

    # Playback
    def play_current(self):
            if not (0 <= self.current_index < len(self.playlist)):
                return
            
            # --- Handle skipping completed videos ---
            if getattr(self, '_force_play_ignore_completed', False):
                self._force_play_ignore_completed = False
            elif getattr(self, 'skip_completed', False):
                logger.info(f"'skip_completed' is True. Checking current track (index {self.current_index}) for completion.")
                guard = 0
                while 0 <= self.current_index < len(self.playlist):
                    url_try = self.playlist[self.current_index].get('url')
                    if not self._is_completed_url(url_try):
                        break
                    logger.info(f"Skipping completed track: {url_try}")
                    self.current_index += 1
                    guard += 1
                    if guard > len(self.playlist) * 2: # Prevent infinite loops
                        self.status.showMessage("All items are completed.", 3000)
                        return
                if self.current_index >= len(self.playlist):
                    self.status.showMessage("All items in scope are completed.", 5000)
                    return
            
            self._end_session()
            
            # --- Determine resume position ---
            item = self.playlist[self.current_index]
            url = item.get('url')
            key = self._canonical_url_key(url) if url else None
            resume_ms = int(self.playback_positions.get(key, self.playback_positions.get(url, 0))) if url else 0

            # --- Call the new unified method to do the heavy lifting ---
            self._prepare_and_load_track(self.current_index, start_pos_ms=resume_ms, should_play=True)

            # --- Update UI specific to starting playback ---
            self.play_pause_btn.setIcon(self._pause_icon_normal)
            self._start_session()
            self._update_tray()

    def next_track(self):
        if not self.playlist:
            return
        # Save current track position before switching
        self._save_current_position()
        # Use scoped playback behavior
        indices = self._scope_indices()
        if indices:
            try:
                pos = indices.index(self.current_index) if self.current_index in indices else -1
                if self.shuffle_mode:
                    import random
                    self.current_index = random.choice(indices)
                else:
                    self.current_index = indices[(pos + 1) % len(indices)]
                self.play_current(); return
            except Exception:
                pass
        if self.shuffle_mode:
            import random
            self.current_index = random.randint(0, len(self.playlist)-1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play_current()

    def previous_track(self):
            if not self.playlist:
                return
            # Save current track position before switching
            self._save_current_position()
            # Use scoped playback behavior
            indices = self._scope_indices()
            if indices:
                try:
                    pos = indices.index(self.current_index) if self.current_index in indices else -1
                    if self.shuffle_mode:
                        import random
                        self.current_index = random.choice(indices)
                    else:
                        # Correctly calculate the previous index within the scope
                        self.current_index = indices[(pos - 1 + len(indices)) % len(indices)] # <-- THE FIX
                    self.play_current(); return
                except Exception:
                    pass
            # This non-scoped part was already correct
            if self.shuffle_mode:
                import random
                self.current_index = random.randint(0, len(self.playlist)-1)
            else:
                self.current_index = (self.current_index - 1 + len(self.playlist)) % len(self.playlist)
            self.play_current()
        
    def toggle_play_pause(self):
        if self._is_playing():
            # print("[DEBUG] Attempting to pause...")
            self.mpv.pause = True
            self._intended_playback_state = False
            # print(f"[DEBUG] After pause command: mpv.pause = {self.mpv.pause}")
            self._save_current_position()
            try:
                self.play_pause_btn.setIcon(self._play_icon_normal)
                self._play_pause_shows_play = True
            except Exception:
                try:
                    self.play_pause_btn.setIcon(self.play_icon)
                    self._play_pause_shows_play = True
                except Exception:
                    pass
            self._end_session()
            # print("[DEBUG] Pause complete, calling _update_silence_indicator...")
            self._update_silence_indicator()
        else:
            # print("[DEBUG] Attempting to play...")
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
                self.play_current()
                return
            self.mpv.pause = False
            self._intended_playback_state = True
            # print(f"[DEBUG] After play command: mpv.pause = {self.mpv.pause}")
            
            # RESET SILENCE TIMER when starting playback
            self._reset_silence_counter()

            # Force icon update after mpv initializes
            self._force_update_silence_indicator_after_delay()
            
            try:
                self.play_pause_btn.setIcon(self._pause_icon_normal)
                self._play_pause_shows_play = False
            except Exception:
                try:
                    self.play_pause_btn.setIcon(self.pause_icon)
                    self._play_pause_shows_play = False
                except Exception:
                    pass
            self._start_session()
            # print("[DEBUG] Play complete, calling _update_silence_indicator...")
            self._update_silence_indicator()
        self._update_tray()

    def _toggle_shuffle(self):
        self.shuffle_mode = self.shuffle_btn.isChecked()
        self.status.showMessage(f"Shuffle {'on' if self.shuffle_mode else 'off'}", 3000)
        self._save_settings()
        self._update_widget_themes() # This line updates the icon
        self._update_up_next()       # This line updates the "Up Next" panel

    def _toggle_repeat(self):
        self.repeat_mode = self.repeat_btn.isChecked()
        self.status.showMessage(f"Repeat {'on' if self.repeat_mode else 'off'}", 3000)
        self._save_settings()
        self._update_widget_themes() # This line updates the icon

    def set_volume(self, value):
        try:
            self.mpv.volume = int(value)
            self.volume_slider.setToolTip(f"Volume: {value}%")
            self._save_settings()
        except Exception as e:
            print(f"Volume error: {e}")

    def set_position(self, pos_ms):
        try:
            self.mpv.time_pos = max(0.0, float(pos_ms) / 1000.0)
        except Exception:
            pass

    def _on_slider_moved(self, pos_ms: int):
            # While scrubbing, update only the time label to reflect the target position
            # Also disable resume enforcement to prevent conflicts
            try:
                self.time_label.setText(format_time(int(pos_ms)))
                # Disable resume enforcement while user is actively scrubbing
                self._resume_enforce_until = 0.0
            except Exception:
                pass

    def _on_slider_released(self):
        # Apply seek when user releases the slider
        try:
            pos_ms = int(self.progress.value())
            # Ensure we disable resume enforcement before seeking
            self._resume_enforce_until = 0.0
            self._resume_target_ms = 0
            
            # Apply the seek position
            self.set_position(pos_ms)
            
            # Update our tracking of last position to prevent save conflicts
            self._last_play_pos_ms = pos_ms
            
            print(f"[seek] user seek to {format_time(pos_ms)}")
        except Exception as e:
            print(f"[seek] error: {e}")
        finally:
            self._user_scrubbing = False

    def _maybe_reapply_resume(self, source: str = ''):
        try:
            # Don't reapply resume if user is actively scrubbing
            if getattr(self, '_user_scrubbing', False):
                return
                
            tgt = int(getattr(self, '_resume_target_ms', 0) or 0)
            until = float(getattr(self, '_resume_enforce_until', 0.0) or 0.0)
            if tgt <= 0 or time.time() > until:
                return
            cur = int(self._last_play_pos_ms or 0)
            # If we're significantly before the target, re-apply seek
            if cur < tgt - 1500:
                # print(f"[resume] reapply from {format_time(cur)} to {format_time(tgt)} source={source}")
                self.mpv.time_pos = max(0.0, float(tgt) / 1000.0)
        except Exception:
            pass

    # Tick updates (position + tray + badge stats)
    def _update_position_tick(self):
        try:
            # Mark item completed when >=95% watched (does not affect current playback)
            if self._is_playing() and 0 <= self.current_index < len(self.playlist):
                dur = float(self.mpv.duration or 0)
                pos = float(self.mpv.time_pos or 0)
                if dur > 0 and pos / dur >= (float(getattr(self, 'completed_percent', 95)) / 100.0):
                    url = self.playlist[self.current_index].get('url')
                    key = self._canonical_url_key(url) if url else None
                    if key and key not in self.completed_urls and url not in self.completed_urls:
                        self.completed_urls.add(key)
                        self._save_completed()
            now = time.time()
            # Enforce resume target early after start
            self._maybe_reapply_resume('tick')
            # Periodically persist resume timestamp while playing
            if self._is_playing() and 0 <= self.current_index < len(self.playlist):
                if now - getattr(self, '_last_resume_save', 0) >= 10:
                    self._save_current_position(); self._last_resume_save = now
            if self._is_playing() and self.session_start_time and now - self.last_position_update >= 30:
                self._update_listening_stats(); self.last_position_update = now
        except Exception:
            pass
        # Update tray and silence indicator visibility based on current playback state
        self._update_tray()
        self.update_badge()

        # Adaptive save intervals based on content and activity
        if self._is_playing() and 0 <= self.current_index < len(self.playlist):
            now = time.time()
            last_save = getattr(self, '_last_resume_save', 0)
            
            # Determine save interval based on context
            save_interval = 5  # Default 5 seconds
            
            # More frequent saves for shorter content
            try:
                duration = float(self.mpv.duration or 0)
                if duration > 0 and duration < 600:  # < 10 minutes
                    save_interval = 3
            except Exception:
                pass
            
            # Less frequent for very long content to reduce I/O
            try:
                if duration > 3600:  # > 1 hour
                    save_interval = 15
            except Exception:
                pass
            
            if now - last_save >= save_interval:
                self._save_current_position()
                self._last_resume_save = now

    def _restore_saved_position(self):
        if not (0 <= self.current_index < len(self.playlist)):
            return
        url = self.playlist[self.current_index].get('url')
        if not url or url not in self.playback_positions:
            return
        pos_ms = int(self.playback_positions[url])
        self._restore_saved_position_attempt(url, pos_ms, 1)

    def _restore_saved_position_attempt(self, url: str, pos_ms: int, attempt: int):
        try:
            # Try to restore; if track not yet loaded, retry a few times
            if attempt > 10:
                print(f"[resume] giving up restore for {url}")
                return
            # If duration not known yet, still try to seek
            self.mpv.time_pos = max(0.0, float(pos_ms) / 1000.0)
            self.status.showMessage(f"Resuming from {format_time(pos_ms)} (attempt {attempt})", 2000)
            # Verify after a short delay
            self.requestTimerSignal.emit(400, lambda: self._verify_restore(url, pos_ms, attempt))
        except Exception as e:
            print(f"_restore_saved_position attempt error: {e}")

    def _verify_restore(self, url: str, pos_ms: int, attempt: int):
        try:
            cur = float(self.mpv.time_pos or 0.0) * 1000.0
            if abs(cur - pos_ms) < 1500:  # within 1.5s
                # print(f"[resume] confirmed at {format_time(int(cur))} for {url}")
                return
        except Exception:
            pass
        # Retry
        self.requestTimerSignal.emit(600, lambda: self._restore_saved_position_attempt(url, pos_ms, attempt + 1))

    # Settings dialog
    def open_settings_tabs(self):
            dlg = QDialog(self); dlg.setWindowTitle("Settings"); dlg.resize(720, 520)
            layout = QVBoxLayout(dlg)
            tabs = QTabWidget(); layout.addWidget(tabs)

            # Playback tab
            w_play = QWidget(); f_play = QFormLayout(w_play)
            spn_completed = QSpinBox(); spn_completed.setRange(50, 100); spn_completed.setSuffix("%")
            spn_completed.setValue(int(getattr(self, 'completed_percent', 95)))
            spn_completed.setToolTip("Percentage of a video watched to be marked as 'completed'.")
            
            chk_skip_completed = QCheckBox("Skip completed videos"); chk_skip_completed.setChecked(bool(getattr(self, 'skip_completed', False)))
            chk_skip_completed.setToolTip("Automatically skip to the next unwatched video if the current one is completed.")

            s_afk = QSpinBox(); s_afk.setRange(1, 240); s_afk.setSuffix(" minutes"); s_afk.setValue(int(getattr(self, 'afk_timeout_minutes', 15)))
            s_afk.setToolTip("Pause playback if there's no mouse or keyboard activity for this duration.")

            f_play.addRow("Completed threshold:", spn_completed)
            f_play.addRow(chk_skip_completed)
            f_play.addRow("Auto-pause after inactivity:", s_afk)
            tabs.addTab(w_play, "Playback")

            # Audio Monitor tab
            w_mon = QWidget(); f_mon = QFormLayout(w_mon)

            # Check if the audio monitor is functional before building the UI
            if not getattr(self.audio_monitor, '_sd', None) or self.audio_monitor.last_error:
                error_msg = self.audio_monitor.last_error or "The 'sounddevice' library is not available or failed to load."
                error_label = QLabel(f"⚠️ Audio Monitor Disabled\n\n{error_msg}")
                error_label.setWordWrap(True)
                error_label.setStyleSheet("color: #d86a4a; font-weight: bold;")
                f_mon.addRow(error_label)
            else:
                # Audio monitor is working, so build the normal UI
                chk_monitor_system = QCheckBox("Monitor system output (speakers/headphones)")
                chk_monitor_system.setChecked(bool(getattr(self, 'monitor_system_output', True)))
                chk_monitor_system.setToolTip("Monitor system audio output (speakers/headphones) instead of microphone.")
                
                cmb_device = QComboBox(); cmb_device.setToolTip("Select the audio device to monitor for silence.")
                try:
                    sd = getattr(self.audio_monitor, '_sd', None)
                    devs = sd.query_devices() if sd else []
                    loopbacks = []; normals = []
                    for i, d in enumerate(devs):
                        if int(d.get('max_input_channels', 0)) > 0:
                            host = d.get('hostapi_name', '') or ''
                            name = d.get('name', f'Device {i}')
                            lname = name.lower()
                            if ('wasapi' in host.lower()) and ('loopback' in lname or 'stereo mix' in lname or 'what u hear' in lname):
                                loopbacks.append((i, name, host))
                            else:
                                normals.append((i, name, host))
                    for i, name, host in (loopbacks + normals):
                        cmb_device.addItem(f"[{i}] {name} ({host})", i)
                    cur = int(getattr(self, 'monitor_device_id', -1))
                    idx = cmb_device.findData(cur)
                    if idx >= 0: cmb_device.setCurrentIndex(idx)
                except Exception:
                    cmb_device.addItem("No devices available"); cmb_device.setEnabled(False)
                pb_rms = QProgressBar()
                pb_rms.setRange(0, 100)
                pb_rms.setFormat('RMS: %p%')
                self.audio_monitor.rmsUpdated.connect(
                    lambda v: (
                        pb_rms.setValue(int(max(0.0, min(1.0, float(v))) * 100)),
                        # logger.info(f"[UI] Updating RMS bar with value: {int(max(0.0, min(1.0, float(v))) * 100)}")
    )
)
                
                s_threshold = QDoubleSpinBox(); s_threshold.setRange(0.001, 1.0); s_threshold.setSingleStep(0.005); s_threshold.setDecimals(4)
                s_threshold.setValue(float(getattr(self, 'silence_threshold', 0.03)))
                s_threshold.setToolTip("Sound level below which is considered silence. Lower is more sensitive.")
                
                s_resume = QDoubleSpinBox(); s_resume.setRange(0.001, 1.0); s_resume.setSingleStep(0.005); s_resume.setDecimals(4)
                s_resume.setValue(float(getattr(self, 'resume_threshold', max(0.03, getattr(self, 'silence_threshold', 0.03) * 1.5))))
                s_resume.setToolTip("Sound level required to exit the silent state. Should be slightly higher than the silence threshold.")
                
                s_silence = QDoubleSpinBox(); s_silence.setRange(0.5, 60.0); s_silence.setSingleStep(0.5); s_silence.setSuffix(" minutes")
                s_silence.setValue(float(getattr(self, 'silence_duration_s', 300.0)) / 60.0)
                s_silence.setToolTip("Duration of continuous silence required before auto-play is triggered.")
                
                chk_auto = QCheckBox("Enable auto-play on silence")
                chk_auto.setChecked(bool(getattr(self, 'auto_play_enabled', True)))
                chk_auto.setToolTip("Globally enable or disable the silence detection and auto-play feature.")

                f_mon.addRow(chk_monitor_system)
                f_mon.addRow("Input device:", cmb_device)
                f_mon.addRow("Live level:", pb_rms)
                f_mon.addRow("Silence threshold:", s_threshold)
                f_mon.addRow("Resume threshold:", s_resume)
                f_mon.addRow("Auto-play after silence:", s_silence)
                f_mon.addRow(chk_auto)
            
            tabs.addTab(w_mon, "Audio Monitor")

            # UI & Panels tab
            w_ui = QWidget(); f_ui = QFormLayout(w_ui)
            chk_restore_session = QCheckBox("Restore last session on startup")
            chk_restore_session.setChecked(bool(getattr(self, 'restore_session', True)))
            chk_restore_session.setToolTip("Automatically save and load your playlist and position between sessions.")
            f_ui.addRow(chk_restore_session)

            chk_show_up_next = QCheckBox("Show 'Up Next' panel")
            chk_show_up_next.setChecked(bool(getattr(self, 'show_up_next', True)))
            chk_show_up_next.setToolTip("Show or hide the 'Up Next' panel below the video player.")
            f_ui.addRow(chk_show_up_next)

            chk_group_singles = QCheckBox("Group miscellaneous videos into a folder")
            chk_group_singles.setChecked(bool(getattr(self, 'group_singles', False)))
            chk_group_singles.setToolTip("Organize individual videos into a 'Miscellaneous' group in the playlist.")
            f_ui.addRow(chk_group_singles)

            chk_center_on_restore = QCheckBox("Center window on restore")
            chk_center_on_restore.setChecked(bool(getattr(self, 'center_on_restore', True)))
            chk_center_on_restore.setToolTip("Center the application window on screen when restoring from the tray or taskbar.")
            f_ui.addRow(chk_center_on_restore)

            chk_min_to_tray = QCheckBox("Minimize to system tray")
            chk_min_to_tray.setChecked(self.minimize_to_tray)
            chk_min_to_tray.setToolTip("When minimizing the window, hide it to the system tray instead of the taskbar.")
            f_ui.addRow(chk_min_to_tray)
            
            chk_show_badge = QCheckBox("Show 'Time Today' badge in top bar")
            chk_show_badge.setChecked(bool(getattr(self, 'show_today_badge', True)))
            chk_show_badge.setToolTip("Show or hide the total listening time for the current day in the main window.")
            f_ui.addRow(chk_show_badge)
            
            tabs.addTab(w_ui, "UI")

            # Diagnostics tab
            w_diag = QWidget(); f_diag = QFormLayout(w_diag)
            lbl_log = QLabel("Logging & Diagnostics"); lbl_log.setStyleSheet("font-weight: bold; margin-top: 10px;"); f_diag.addRow(lbl_log)
            log_level_combo = QComboBox(); log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR']); log_level_combo.setCurrentText(self.log_level)
            log_level_combo.setToolTip("Set the verbosity of log files. 'DEBUG' is the most detailed.")
            f_diag.addRow("Log Level:", log_level_combo)
            logs_btn = QPushButton("Open Logs Folder"); logs_btn.clicked.connect(self.open_logs_folder); logs_btn.setToolTip("Open the folder containing the application's log files.")
            f_diag.addRow("", logs_btn)
            export_btn = QPushButton("Export Diagnostics"); export_btn.clicked.connect(self.export_diagnostics); export_btn.setToolTip("Export logs and configuration into a zip file for troubleshooting.")
            f_diag.addRow("", export_btn)
            tabs.addTab(w_diag, "Diagnostics")
            
            # Buttons
            btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); layout.addWidget(btns)

            def _apply():
                # Apply all settings from all tabs
                # Playback
                try: self.completed_percent = int(spn_completed.value())
                except Exception: pass
                try: self.skip_completed = bool(chk_skip_completed.isChecked())
                except Exception: pass
                try:
                    self.afk_timeout_minutes = int(s_afk.value())
                    if getattr(self, 'afk_monitor', None):
                        self.afk_monitor.timeout_seconds = self.afk_timeout_minutes * 60
                except Exception: pass
                
                # Audio Monitor (only if not in error state)
                if getattr(self.audio_monitor, '_sd', None) and not self.audio_monitor.last_error:
                    try: self.monitor_system_output = bool(chk_monitor_system.isChecked())
                    except Exception: pass
                    try:
                        did = cmb_device.currentData()
                        if did is not None: self.monitor_device_id = int(did)
                    except Exception: pass
                    try: self.silence_threshold = float(s_threshold.value())
                    except Exception: pass
                    try: self.resume_threshold = float(s_resume.value())
                    except Exception: pass
                    try: self.silence_duration_s = float(s_silence.value()) * 60.0
                    except Exception: pass
                    try: self.auto_play_enabled = bool(chk_auto.isChecked())
                    except Exception: pass
                    try:
                        if getattr(self, 'audio_monitor', None):
                            self.audio_monitor.update_settings(
                                silence_duration_s=self.silence_duration_s, silence_threshold=self.silence_threshold,
                                resume_threshold=self.resume_threshold, monitor_system_output=self.monitor_system_output,
                                device_id=self.monitor_device_id)
                    except Exception: pass
                
                # UI & Panels
                try:
                    self.restore_session = bool(chk_restore_session.isChecked())
                    self.show_up_next = bool(chk_show_up_next.isChecked())
                    if hasattr(self, 'up_next_container'): self.up_next_container.setVisible(self.show_up_next)
                except Exception: pass
                try:
                    self.group_singles = bool(chk_group_singles.isChecked())
                    self._refresh_playlist_widget()
                except Exception: pass
                try: self.center_on_restore = bool(chk_center_on_restore.isChecked())
                except Exception: pass
                try: self.minimize_to_tray = bool(chk_min_to_tray.isChecked())
                except Exception: pass
                try:
                    self.show_today_badge = bool(chk_show_badge.isChecked())
                    if hasattr(self, 'today_badge'): self.today_badge.setVisible(self.show_today_badge)
                except Exception: pass
                
                # Persist all settings
                self._save_settings()
                dlg.accept()

            btns.accepted.connect(_apply)
            btns.rejected.connect(dlg.reject)
            dlg.exec()

    def open_settings(self):
        dlg = QDialog(self); dlg.setWindowTitle("Settings"); dlg.resize(400, 300)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        
        # Audio monitoring settings
        c_monitor_system = QCheckBox()
        c_monitor_system.setChecked(getattr(self.audio_monitor, 'monitor_system_output', True))
        c_monitor_system.setToolTip("Monitor system audio output (speakers/headphones) instead of microphone")
        form.addRow("Monitor system output:", c_monitor_system)

        # Live RMS meter (0-100%)
        pb_rms = QProgressBar(); pb_rms.setRange(0, 100); pb_rms.setFormat('RMS: %p%')
        try:
            self.audio_monitor.rmsUpdated.connect(lambda v: pb_rms.setValue(int(max(0.0, min(1.0, float(v))) * 100)))
        except Exception:
            pass
        form.addRow("Live level:", pb_rms)

        chk_min_to_tray = QCheckBox()
        chk_min_to_tray.setChecked(self.minimize_to_tray)
        form.addRow("Minimize to tray:", chk_min_to_tray)
        
        # Input device (prioritize WASAPI loopback-capable inputs)
        c_device = QComboBox()
        try:
            sd = getattr(self.audio_monitor, '_sd', None)
            devs = sd.query_devices() if sd else []
            loopbacks = []; normals = []
            for i, d in enumerate(devs):
                try:
                    if int(d.get('max_input_channels', 0)) <= 0:
                        continue
                    host = d.get('hostapi_name', '') or ''
                    name = d.get('name', f'Device {i}')
                    item = (i, name, host)
                    lname = name.lower()
                    if ('wasapi' in host.lower()) and ('loopback' in lname or 'stereo mix' in lname or 'what u hear' in lname):
                        loopbacks.append(item)
                    else:
                        normals.append(item)
                except Exception:
                    continue
            for i, name, host in (loopbacks + normals):
                c_device.addItem(f"[{i}] {name} ({host})", i)
            cur = int(getattr(self, 'monitor_device_id', -1))
            idx = c_device.findData(cur)
            if idx >= 0:
                c_device.setCurrentIndex(idx)
        except Exception:
            c_device.addItem("No devices available"); c_device.setEnabled(False)
        form.addRow("Input device:", c_device)
        
        s_threshold = QDoubleSpinBox()
        s_threshold.setRange(0.001, 1.0)
        s_threshold.setSingleStep(0.001)
        s_threshold.setDecimals(3)
        s_threshold.setValue(getattr(self.audio_monitor, 'threshold', 0.03))
        s_threshold.setToolTip("Lower values = more sensitive to quiet sounds")
        form.addRow("Silence threshold:", s_threshold)

        # Hysteresis resume threshold (leaving silence)
        s_resume = QDoubleSpinBox(); s_resume.setRange(0.001, 1.0); s_resume.setSingleStep(0.005); s_resume.setDecimals(4)
        s_resume.setToolTip("Threshold used to leave silence; typically ≥ silence threshold")
        try:
            s_resume.setValue(float(getattr(self, 'resume_threshold', max(0.03, getattr(self, 'silence_threshold', 0.03) * 1.5))))
        except Exception:
            s_resume.setValue(max(0.03, getattr(self, 'silence_threshold', 0.03) * 1.5))
        form.addRow("Resume threshold:", s_resume)

        log_level_combo = QComboBox()  # Create a dropdown
        log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR'])  # Add log level options
        log_level_combo.setCurrentText(self.log_level)  # Set the current log level
        form.addRow("Log Level:", log_level_combo)  # Add it to the settings form

        # Completed threshold percent
        s_completed = QSpinBox()
        s_completed.setRange(50, 100); s_completed.setSuffix("%")
        s_completed.setValue(int(getattr(self, 'completed_percent', 95)))
        form.addRow("Completed threshold:", s_completed)

        # Skip completed toggle
        c_skip_completed = QCheckBox()
        c_skip_completed.setChecked(bool(getattr(self, 'skip_completed', False)))
        c_skip_completed.setToolTip("If enabled, items marked as completed will be auto-skipped when starting playback")
        form.addRow("Skip completed:", c_skip_completed)
        # Up Next toggle
        c_show_up_next = QCheckBox(); c_show_up_next.setChecked(bool(getattr(self, 'show_up_next', True)))
        form.addRow("Show Up Next:", c_show_up_next)
        
        s_silence = QDoubleSpinBox()
        s_silence.setRange(0.5, 60.0)
        s_silence.setSingleStep(0.5)
        s_silence.setSuffix(" minutes")
        s_silence.setValue(self.silence_duration_s/60.0)
        form.addRow("Auto-play after silence:", s_silence)
        
        s_afk = QSpinBox()
        s_afk.setRange(1, 120)
        s_afk.setValue(self.afk_timeout_minutes)
        s_afk.setSuffix(" minutes")
        form.addRow("Auto-pause after inactivity:", s_afk)
        
        c_auto = QCheckBox()
        c_auto.setChecked(self.auto_play_enabled)
        form.addRow("Enable auto-play on silence:", c_auto)
        
        c_thumb = QCheckBox()
        c_thumb.setChecked(self.show_thumbnails)
        form.addRow("Show thumbnails:", c_thumb)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(btns)
        
        def _apply():
            # Update settings
            old_monitor_system = getattr(self.audio_monitor, 'monitor_system_output', True)
            old_threshold = getattr(self.audio_monitor, 'threshold', 0.03)
            
            self.silence_duration_s = float(s_silence.value() * 60.0)
            self.afk_timeout_minutes = int(s_afk.value())
            self.auto_play_enabled = bool(c_auto.isChecked())
            self.show_thumbnails = bool(c_thumb.isChecked())
            
            self.minimize_to_tray = bool(chk_min_to_tray.isChecked())
            
            new_monitor_system = bool(c_monitor_system.isChecked())
            new_threshold = float(s_threshold.value())
            new_dev_id = c_device.currentData() if 'c_device' in locals() else None
            # Persist to instance
            self.monitor_system_output = new_monitor_system
            self.silence_threshold = new_threshold
            self.monitor_device_id = new_dev_id
            self.completed_percent = int(s_completed.value())
            # Skip completed
            try:
                self.skip_completed = bool(c_skip_completed.isChecked())
                # Monitor settings and thresholds
                try:
                    self.monitor_system_output = bool(c_monitor_system.isChecked())
                except Exception:
                    pass
                try:
                    self.silence_threshold = float(s_threshold.value())
                except Exception:
                    pass
                try:
                    self.resume_threshold = float(s_resume.value())
                except Exception:
                    self.resume_threshold = max(self.silence_threshold, self.silence_threshold * 1.5)
                # Hot-apply to running monitor
                try:
                    if getattr(self, 'audio_monitor', None):
                        self.audio_monitor.update_settings(
                            silence_duration_s=self.silence_duration_s,
                            silence_threshold=self.silence_threshold,
                            resume_threshold=self.resume_threshold,
                            monitor_system_output=self.monitor_system_output,
                            device_id=self.monitor_device_id
                        )
                except Exception:
                    pass
                self.show_up_next = bool(c_show_up_next.isChecked())
                # Apply Up Next visibility immediately
                try:
                    if hasattr(self, 'up_next_container'):
                        self.up_next_container.setVisible(self.show_up_next)
                except Exception:
                    pass
            except Exception:
                pass
            
            # Update audio monitor settings
            if getattr(self, 'audio_monitor', None):
                self.audio_monitor.update_settings(
                    silence_duration_s=self.silence_duration_s,
                    silence_threshold=new_threshold,
                    monitor_system_output=new_monitor_system
                )
                
                # Restart audio monitor if monitoring mode or threshold changed significantly
                if (old_monitor_system != new_monitor_system or 
                    abs(old_threshold - new_threshold) > 0.005 or
                    int(getattr(self, 'monitor_device_id', new_dev_id)) != new_dev_id):
                    self._restart_audio_monitor()
            
            # Update AFK monitor
            if getattr(self, 'afk_monitor', None):
                self.afk_monitor.timeout_seconds = self.afk_timeout_minutes * 60

            self._refresh_playlist_widget()
            
            # Diagnostics
            try:
                old_level = self.log_level
                self.log_level = log_level_combo.currentText()
                if old_level != self.log_level:
                    # Reinitialize logging with new level
                    logging.getLogger().setLevel(getattr(logging, self.log_level.upper(), logging.INFO))
                    logger.info(f"Log level changed from {old_level} to {self.log_level}")
            except Exception as e:
                logger.error(f"Failed to apply diagnostics settings: {e}")
            
            self._save_settings()
            dlg.accept()
            self.status.showMessage("Settings saved", 4000)
        
        btns.accepted.connect(_apply)
        btns.rejected.connect(dlg.reject)
        dlg.exec()

    def _on_playlist_items_ready(self, items: list):
            if not items:
                self._hide_loading("No entries found in playlist", 4000)
                return

            # --- PREPARATION ---
            # 1. Deduplicate against the entire existing playlist
            existing_urls = {it.get('url') for it in self.playlist if it.get('url')}
            new_items = [it for it in items if it.get('url') and it.get('url') not in existing_urls]
            
            if not new_items:
                self._hide_loading("Playlist items already exist", 4000)
                return

            # 2. Keep track of the starting index for new items
            base_index = len(self.playlist)
            
            # 3. Update the internal playlist data structure first
            self.playlist.extend(new_items)
            
            # --- BATCHED UI UPDATE ---
            # 4. Define the function that will process one batch of new items
            def add_batch_to_ui(batch, start_offset):
                for i, item_data in enumerate(batch):
                    current_index = base_index + start_offset + i
                    self._add_single_item_to_tree(current_index, item_data)

            # 5. Use the helper to process all new items without freezing the UI
            self._process_with_yield(
                items=new_items,
                processor_func=add_batch_to_ui,
                batch_size=50,  # Process 50 items at a time
                progress_callback=lambda p, t: self._show_loading(f"Adding {p} / {t} items...")
            )

            # --- FINALIZATION ---
            # 6. Schedule a single save operation after all items are added
            self._schedule_save_current_playlist()
            self._hide_loading(f"Added {len(new_items)} new entries", 5000)
            
            # 7. Resolve titles in the background for items that need it
            items_needing_titles = [it for it in new_items if not it.get('title') or it['title'] == it.get('url')]
            if items_needing_titles:
                for item in items_needing_titles:
                    self._resolve_title_parallel(item.get('url'), item.get('type', 'local'))
            
    def _restart_audio_monitor(self):
        """Restart the audio monitor with new settings"""
        if hasattr(self, 'audio_monitor') and self.audio_monitor:
            self.audio_monitor.stop()
            self.audio_monitor.wait(2000)

            try:
                dev_id = getattr(self, 'monitor_device_id', None)
                if not isinstance(dev_id, int) or dev_id < 0:
                    dev_id = None
            except Exception:
                dev_id = None

            self.audio_monitor = SystemAudioMonitor(
                silence_duration_s=self.silence_duration_s,
                silence_threshold=float(getattr(self, 'silence_threshold', 0.03)),
                resume_threshold=float(getattr(self, 'resume_threshold', max(0.03, getattr(self, 'silence_threshold', 0.03) * 1.5))),
                monitor_system_output=bool(getattr(self, 'monitor_system_output', True)),
                device_id=dev_id
            )
            self.audio_monitor.silenceDetected.connect(self.on_silence_detected)
            self.audio_monitor.audioStateChanged.connect(self._update_silence_indicator)
            self.audio_monitor.start()

    def open_help(self):
            dlg = QDialog(self); dlg.setWindowTitle("Keyboard Shortcuts"); dlg.resize(420, 400)
            layout = QVBoxLayout(dlg)
            form = QFormLayout()
            def add(k, desc):
                form.addRow(QLabel(f"<b>{k}</b>"), QLabel(desc))
            
            add("Space", "Play / Pause")
            add("N", "Next Track")
            add("P", "Previous Track")
            add("M", "Toggle Mute")
            add("→", "Seek Forward 5s")
            add("←", "Seek Backward 5s")
            add("B", "Play Selected Group")
            add("↑ / + / =", "Volume Up")
            add("↓ / -", "Volume Down")
            add("S", "Toggle Shuffle")
            add("R", "Toggle Repeat")
            add("F", "Toggle Fullscreen")
            add("Ctrl + L", "Add Link from URL")
            add("Delete", "Remove Selected Item(s)")
            print("🗑️ _remove_index called!")
            
            layout.addLayout(form)
            btns = QDialogButtonBox(QDialogButtonBox.Close); btns.rejected.connect(dlg.reject); layout.addWidget(btns)
            dlg.exec()

    # Stats dialog
    def open_stats(self):
            dlg = QDialog(self); dlg.setWindowTitle("Listening Statistics"); dlg.resize(780, 460)
            layout = QVBoxLayout(dlg)
            overall = QLabel(f"Total time: {human_duration(self.listening_stats.get('overall', 0))}")
            layout.addWidget(overall)

            # Heatmap
            daily = dict(self.listening_stats.get('daily', {}))
            heat = StatsHeatmapWidget(daily, theme=getattr(self, 'theme', 'dark'))
            layout.addWidget(heat)

            # Metrics under heatmap
            def _compute_metrics(dmap):
                import datetime as _dt
                if not dmap:
                    return 0, 0.0
                items = []
                for k, v in dmap.items():
                    try:
                        y, m, d = [int(x) for x in k.split('-')]
                        items.append((_dt.date(y, m, d), float(v or 0)))
                    except Exception:
                        continue
                if not items:
                    return 0, 0.0
                items.sort(key=lambda x: x[0])
                # Average over non-zero days
                nz = [v for _, v in items if v > 0]
                avg = (sum(nz) / len(nz)) if nz else 0.0
                # Longest consecutive-day streak with >0 seconds
                longest = cur = 0
                prev_date = None
                for dte, val in items:
                    if val > 0:
                        if prev_date is not None and dte == prev_date + _dt.timedelta(days=1):
                            cur += 1
                        else:
                            cur = 1
                    else:
                        cur = 0
                    if cur > longest:
                        longest = cur
                    prev_date = dte
                return int(longest), float(avg)

            _longest, _avg_sec = _compute_metrics(daily)
            metrics = QLabel(f"Longest streak: {_longest} days    •    Average daily: {human_duration(_avg_sec)}")
            layout.addWidget(metrics)

            # Table and filter controls
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Date", "Time Listened"])
            table.horizontalHeader().setStretchLastSection(True)
            table.verticalHeader().setVisible(False)
            # Make the table read-only (disable in-place editing) but keep selection/navigation
            try:
                from PySide6.QtWidgets import QAbstractItemView
                table.setEditTriggers(QAbstractItemView.NoEditTriggers)
                table.setSelectionBehavior(QAbstractItemView.SelectRows)
                table.setSelectionMode(QAbstractItemView.SingleSelection)
            except Exception:
                pass
            layout.addWidget(table)

            flt = QHBoxLayout()
            selected_label = QLabel("Click a day in the heatmap to filter the table"); flt.addWidget(selected_label); flt.addStretch()
            show_all_btn = QPushButton("Show All"); show_all_btn.setVisible(False); flt.addWidget(show_all_btn)
            layout.addLayout(flt)

            def rebuild_table(filter_date=None):
                rows = sorted(daily.items(), key=lambda x: x[0], reverse=True)
                if filter_date:
                    rows = [(d, s) for d, s in rows if d == filter_date]
                    sel_sec = daily.get(filter_date, 0)
                    selected_label.setText(f"Selected: {filter_date} — {human_duration(sel_sec)}")
                    show_all_btn.setVisible(True)
                else:
                    selected_label.setText("Click a day in the heatmap to filter the table")
                    show_all_btn.setVisible(False)
                table.setRowCount(len(rows))
                for r, (d, sec) in enumerate(rows):
                    it0 = QTableWidgetItem(d)
                    try:
                        it0.setFlags(it0.flags() & ~Qt.ItemIsEditable)
                    except Exception:
                        pass
                    table.setItem(r, 0, it0)

                    it1 = QTableWidgetItem(human_duration(sec))
                    try:
                        it1.setFlags(it1.flags() & ~Qt.ItemIsEditable)
                    except Exception:
                        pass
                    table.setItem(r, 1, it1)
                table.resizeColumnsToContents()

            heat.daySelected.connect(lambda d: rebuild_table(d))
            show_all_btn.clicked.connect(lambda: rebuild_table(None))
            rebuild_table(None)

            btns = QDialogButtonBox(QDialogButtonBox.Close); btns.rejected.connect(dlg.reject); layout.addWidget(btns)
            dlg.exec()

    def _reset_stats(self, dlg):
        if QMessageBox.question(self, "Reset Stats", "Are you sure?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.listening_stats = {'daily': {}, 'overall': 0}
            try:
                json.dump(self.listening_stats, open(CFG_STATS, 'w', encoding='utf-8'))
            except Exception:
                pass
            dlg.accept(); self.update_badge()

    def _toggle_auto_play(self):
        self.auto_play_enabled = self.auto_play_checkbox.isChecked()
        self._save_settings()

    # Stats/badge
    def _start_session(self):
        # Begin a listening session for stats/badge
        self.session_start_time = time.time()
        self.last_position_update = self.session_start_time

    def _end_session(self):
        if self.session_start_time:
            try:
                self._update_listening_stats()
            except Exception:
                pass
            self.session_start_time = None

    def _update_listening_stats(self, force: bool = False):
        """
        Add elapsed listening time to stats.
        - When force is False: only update while actively playing (periodic commit).
        - When force is True: commit whatever has accumulated since session_start_time
          even if playback is currently paused/stopped (e.g., on pause).
        """
        if not self.session_start_time:
            return

        if (not force) and (not self._is_playing()):
            return

        duration = time.time() - self.session_start_time
        if duration <= 0:
            return

        today = datetime.now().strftime('%Y-%m-%d')
        self.listening_stats.setdefault('daily', {})
        self.listening_stats['daily'][today] = self.listening_stats['daily'].get(today, 0) + duration
        self.listening_stats['overall'] = self.listening_stats.get('overall', 0) + duration

        # Reset or roll session_start_time depending on context
        if force:
            self.session_start_time = None
        else:
            self.session_start_time = time.time()

        try:
            json.dump(self.listening_stats, open(CFG_STATS, 'w', encoding='utf-8'))
        except Exception:
            pass

    def _end_session(self):
        # Commit any in-progress session even if we just paused (force=True)
        if self.session_start_time:
            self._update_listening_stats(force=True)

    def update_badge(self):
        today = datetime.now().strftime('%Y-%m-%d')
        base = self.listening_stats.get('daily', {}).get(today, 0.0)
        if self._is_playing() and self.session_start_time:
            base += time.time() - self.session_start_time
        self.today_badge.setText(human_duration(base))

    # Resume positions
    def _save_current_position(self):
        if not (0 <= self.current_index < len(self.playlist)):
            return
        try:
            # Don't save position while user is scrubbing
            if getattr(self, '_user_scrubbing', False):
                return
                
            # Use last observed play position from mpv observer to avoid stale reads
            pos = int(self._last_play_pos_ms or 0)
            if pos <= 5000:
                return
            dur_sec = self.mpv.duration
            dur = int(float(dur_sec) * 1000) if dur_sec else 0
            # Do not save within last 10s when duration is known
            if dur > 0 and pos >= dur - 10000:
                return
            # During enforcement window, ignore saves that are below target by >2s
            # BUT allow saves that are significantly different (user may have seeked)
            if getattr(self, '_resume_target_ms', 0) > 0 and time.time() < getattr(self, '_resume_enforce_until', 0.0):
                tgt = int(self._resume_target_ms)
                # Allow saves if position is very different from target (likely user seek)
                if abs(pos - tgt) > 30000:  # 30+ seconds difference
                    print(f"[resume] allowing save (user seek) at {format_time(pos)} target {format_time(tgt)}")
                elif pos < tgt - 2000:
                    print(f"[resume] guard skip (below target) at {format_time(pos)} target {format_time(tgt)}")
                    return
                    
            item = self.playlist[self.current_index]
            url = item.get('url')
            # Only save if advanced by >=5s since last save for this URL
            prev = self._last_saved_pos_ms.get(url, -1)
            if prev >= 0 and abs(pos - prev) < 5000:
                # print(f"[resume] skip (no movement) at {format_time(pos)} for {url}")
                return
            self.playback_positions[url] = pos
            self._last_saved_pos_ms[url] = pos
            self._save_positions()
            print(f"[resume] saved {format_time(pos)} for {url}")
        except Exception as e:
            print(f"_save_current_position error: {e}")
            
    def _clear_resume_enforcement(self):
        """Clear resume enforcement to allow free seeking"""
        self._resume_enforce_until = 0.0
        self._resume_target_ms = 0
        print("[resume] enforcement cleared")        

    # Helpers
    def _is_playing(self):
        try:
            return not bool(self.mpv.pause) and (self.current_index >= 0)
        except Exception:
            return False
        
    def playlist_chevron_color(self):
        """Return the correct chevron color based on current theme."""
        # Use off-white for dark, brown for vinyl/light
        return "#f3f3f3" if getattr(self, "theme", "dark") == "dark" else "#4a2c2a"    

    def filter_playlist(self, text: str):
            """Filter playlist tree and auto-expand if the number of results is small."""
            try:
                # --- CONFIGURATION ---
                # Here you can easily change the threshold from 5 to any number you prefer.
                EXPANSION_THRESHOLD = 5 

                query = text.lower().strip()
                # print(f"[SEARCH] Filtering with query: '{query}'")

                if not query:
                    self._show_all_items()
                    return

                groups_with_matches = []
                total_matches_found = 0

                # Iterate through all top-level items
                for i in range(self.playlist_tree.topLevelItemCount()):
                    item = self.playlist_tree.topLevelItem(i)
                    if not item:
                        continue

                    data = item.data(0, Qt.UserRole)

                    # Case 1: Item is a group (playlist header)
                    if isinstance(data, tuple) and data[0] == 'group':
                        any_child_visible = False
                        group_text = item.text(0).lower()
                        group_matches = query in group_text

                        for j in range(item.childCount()):
                            child = item.child(j)
                            child_text = child.text(0).lower()

                            if query in child_text or group_matches:
                                child.setHidden(False)
                                any_child_visible = True
                                # --- MODIFICATION: Increment total match count ---
                                total_matches_found += 1 
                            else:
                                child.setHidden(True)

                        if any_child_visible:
                            groups_with_matches.append(item)

                        # A group is visible if its title matches or it has a visible child
                        item.setHidden(not (any_child_visible or group_matches))
                    
                    # Case 2: Item is a top-level individual track (not in a group)
                    else:
                        item_text = item.text(0).lower()
                        is_match = query in item_text
                        item.setHidden(not is_match)
                        if is_match:
                            # --- MODIFICATION: Increment total match count ---
                            total_matches_found += 1 

                # --- NEW, MORE FLEXIBLE AUTO-EXPAND LOGIC ---
                # print(f"[SEARCH] Found {total_matches_found} total matching items.")

                # If the total number of results is small, expand all parent groups that have matches.
                if 0 < total_matches_found <= EXPANSION_THRESHOLD:
                    for group in groups_with_matches:
                        group.setExpanded(True)
                    
                    # Optional: Scroll to the very first matching item in the tree for a better UX
                    if len(groups_with_matches) > 0:
                        first_group = groups_with_matches[0]
                        for i in range(first_group.childCount()):
                            if not first_group.child(i).isHidden():
                                self.playlist_tree.scrollToItem(first_group.child(i))
                                break
                # If there are too many results, collapse all groups for a clean overview.
                else:
                    self.playlist_tree.collapseAll()

            except Exception as e:
                print(f"Filter playlist error: {e}")

    def _show_all_items(self):
        """Show all items in the playlist tree"""
        try:
            for i in range(self.playlist_tree.topLevelItemCount()):
                item = self.playlist_tree.topLevelItem(i)
                if item:
                    item.setHidden(False)
                    # Show all children too
                    for j in range(item.childCount()):
                        child = item.child(j)
                        if child:
                            child.setHidden(False)
        except Exception as e:
            print(f"Show all items error: {e}")

    def _schedule_search_filter(self, text):
        """Schedule search filtering with a small delay for IME support"""
        try:
            # Stop any existing timer
            self._search_timer.stop()
            
            # Check if this is likely Japanese input (contains non-ASCII characters)
            has_japanese = any(ord(char) > 127 for char in text)
            
            if has_japanese:
                # For Japanese text, use a longer delay and also check composition state
                delay = 800  # Longer delay for Japanese
            else:
                # For ASCII text, shorter delay
                delay = 150
                
            self._search_timer.start(delay)
            
        except Exception as e:
            print(f"Schedule search filter error: {e}")

    def _on_search_text_changed(self, text):
        """Simplified search with better Japanese support"""
        try:
            # print(f"[DEBUG] Search text changed: '{text}'")  # DEBUG LINE
            
            # Stop any existing timer
            self._search_timer.stop()
            
            # Always use a delay, but adjust based on content
            has_cjk = any(ord(char) > 127 for char in text)
            
            if has_cjk:
                # For Japanese/Chinese/Korean, wait longer
                delay = 750
            else:
                # For ASCII, still use a small delay for consistency
                delay = 200
                
            # print(f"[DEBUG] Starting timer with delay: {delay}ms")  # DEBUG LINE
            self._search_timer.start(delay)
            
        except Exception as e:
            print(f"Search text changed error: {e}")          

    # Silence + AFK handlers
    def on_silence_detected(self):
        if self.auto_play_enabled and self.playlist and (not self._is_playing()):
            self.status.showMessage("System silence detected - Resuming playback", 4000)
            if self.current_index == -1:  # No current video selected
                self.current_index = 0  # Default to the first video
            self.play_current()  # Resume the current video
            self._update_silence_indicator()

    def on_user_afk(self):
        if self._is_playing():
            self.toggle_play_pause(); self.status.showMessage("Paused due to inactivity", 4000)

    # Keyboard shortcuts
    def _setup_keyboard_shortcuts(self):
            # Main Playback
            QShortcut(QKeySequence(Qt.Key_Space), self, self.toggle_play_pause)
            QShortcut(QKeySequence(Qt.Key_N), self, self.next_track)
            QShortcut(QKeySequence(Qt.Key_P), self, self.previous_track)
            QShortcut(QKeySequence(Qt.Key_M), self, self._toggle_mute)

            # Seeking
            QShortcut(QKeySequence(Qt.Key_Right), self, lambda: self._seek_relative(5))
            QShortcut(QKeySequence(Qt.Key_Left), self, lambda: self._seek_relative(-5))

            # Volume
            QShortcut(QKeySequence(Qt.Key_Up), self, self._volume_up)
            QShortcut(QKeySequence(Qt.Key_Down), self, self._volume_down)
            QShortcut(QKeySequence(Qt.Key_Plus), self, self._volume_up)
            QShortcut(QKeySequence(Qt.Key_Equal), self, self._volume_up)
            QShortcut(QKeySequence(Qt.Key_Minus), self, self._volume_down)

            # Toggles
            QShortcut(QKeySequence(Qt.Key_S), self, self._toggle_shuffle_shortcut)
            QShortcut(QKeySequence(Qt.Key_R), self, self._toggle_repeat_shortcut)

            QShortcut(QKeySequence(Qt.Key_C), self, self._toggle_all_groups)
            QShortcut(QKeySequence(Qt.Key_X), self, self._expand_all_groups)

            # Group playback
            QShortcut(QKeySequence(Qt.Key_B), self, self._play_selected_group)
            
            # Window & Misc
            QShortcut(QKeySequence(Qt.Key_F), self, self._toggle_fullscreen)
            QShortcut(QKeySequence(Qt.CTRL | Qt.Key_L), self, self.add_link_dialog)
            QShortcut(QKeySequence(Qt.Key_Delete), self, self._remove_selected_items)
            QShortcut(QKeySequence(Qt.Key_F1), self, self.open_help)

            QShortcut(QKeySequence(Qt.CTRL | Qt.Key_Z), self, self._perform_undo)
            QShortcut(QKeySequence(Qt.CTRL | Qt.Key_V), self, self._handle_paste)

            # Playlist navigation
            QShortcut(QKeySequence(Qt.Key_Home), self, self._navigate_to_top)
            QShortcut(QKeySequence(Qt.Key_End), self, self._navigate_to_bottom)
            
    def _toggle_mute(self):
        """Toggles the player's mute status."""
        try:
            current_mute = bool(self.mpv.mute)
            self.mpv.mute = not current_mute
            # Show status message
            self.status.showMessage(
                f"Volume {'muted' if not current_mute else 'unmuted'}", 
                2000
            )
        except Exception:
            pass

    def _seek_relative(self, seconds):
        """Seeks the player forward or backward by a number of seconds."""
        try:
            current_pos = self.mpv.time_pos or 0
            self.mpv.time_pos = current_pos + seconds
        except Exception:
            pass

    def _toggle_fullscreen(self):
        """Toggles the main window between fullscreen and normal states."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()        

    def _toggle_shuffle_shortcut(self):
        self.shuffle_btn.setChecked(not self.shuffle_btn.isChecked())
        self._toggle_shuffle()

    def _toggle_repeat_shortcut(self):
        self.repeat_btn.setChecked(not self.repeat_btn.isChecked())
        self._toggle_repeat()

    def _remove_selected_items(self):
        """Remove selected items - handles both individual items and group headers with undo support"""
        try:
            items = self.playlist_tree.selectedItems()
            if not items:
                return
            
            # --- FIX: Remember which folders are open ---
            expansion_state = self._get_tree_expansion_state()
            # --- FIX: Forget the last pasted link so it can be re-added ---
            self._last_clipboard_offer = ""

            all_indices = set()
            group_names_for_display = []

            # Process each selected item
            for item in items:
                data = item.data(0, Qt.UserRole)
                if not isinstance(data, tuple):
                    continue
                    
                kind = data[0]
                
                if kind == 'current':
                    # Individual item
                    idx = data[1]
                    if 0 <= idx < len(self.playlist):
                        all_indices.add(idx)
                        
                elif kind == 'group':
                    # Group item - resolve the key properly
                    group_key = None
                    
                    # Method 1: Try the raw key from UserRole
                    if len(data) > 1:
                        group_key = data[1]
                    
                    # Method 2: Try stored key from UserRole + 1
                    if not group_key:
                        try:
                            group_key = item.data(0, Qt.UserRole + 1)
                        except Exception:
                            pass
                    
                    # Method 3: Extract from display text
                    if not group_key:
                        item_text = item.text(0)
                        if item_text and item_text.startswith('📃 '):
                            group_name = item_text[2:].strip()
                            if '(' in group_name and group_name.endswith(')'):
                                group_name = group_name[:group_name.rfind('(')].strip()
                            
                            # Try to find matching playlist items
                            for playlist_item in self.playlist:
                                playlist_key = playlist_item.get('playlist_key')
                                playlist_name = playlist_item.get('playlist')
                                
                                if playlist_key == group_name or playlist_name == group_name:
                                    group_key = playlist_key or playlist_name
                                    break
                            
                            # If no match found, use the extracted name
                            if not group_key:
                                group_key = group_name
                    
                    # Get indices for this group
                    if group_key:
                        group_indices = self._iter_indices_for_group(group_key)
                        print(f"[DEBUG] Group '{group_key}' resolves to {len(group_indices)} items")
                        all_indices.update(group_indices)
                        
                        # Store display name for confirmation dialog
                        display_name = item.text(0)
                        if display_name.startswith('📃 '):
                            display_name = display_name[2:].strip()
                        group_names_for_display.append(display_name)
                    else:
                        print(f"[DEBUG] Could not resolve group key for item: {item.text(0)}")

            # Convert to sorted list for processing
            indices_to_remove = sorted(all_indices)
            
            if not indices_to_remove:
                self.status.showMessage("No items to remove", 3000)
                return

            print(f"[DEBUG] Final removal list: {len(indices_to_remove)} items")
            
            # Confirmation dialog for large deletions
            total_items = len(indices_to_remove)
            if total_items > 5 or group_names_for_display:
                if group_names_for_display:
                    msg = f"Remove {total_items} items including groups:\n" + "\n".join(f"• {name}" for name in group_names_for_display)
                else:
                    msg = f"Remove {total_items} selected items?"
                    
                reply = QMessageBox.question(
                    self, 
                    "Remove Items", 
                    msg,
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return

            # Store undo data BEFORE deletion
            was_playing = self._is_playing()
            old_current_index = self.current_index
            
            # Collect items for undo (in original order)
            items_for_undo = []
            for i in indices_to_remove:
                if 0 <= i < len(self.playlist):
                    items_for_undo.append({
                        'index': i,
                        'item': self.playlist[i].copy()  # Deep copy
                    })

            # Prepare undo data
            undo_type = 'delete_group' if group_names_for_display else 'delete_items'
            undo_data = {
                'items': items_for_undo,
                'was_playing': was_playing,
                'old_current_index': old_current_index
            }
            if group_names_for_display:
                undo_data['group_names'] = group_names_for_display

            # Perform removal in reverse order to avoid index shifting
            for i in reversed(indices_to_remove):
                if 0 <= i < len(self.playlist):
                    del self.playlist[i]
                    
                    # Update current_index if affected
                    if self.current_index == i:
                        self.current_index = -1
                    elif i < self.current_index:
                        self.current_index -= 1

            # Add to undo stack
            self._add_undo_operation(undo_type, undo_data)

            # Save and refresh
            self._save_current_playlist()
            self._refresh_playlist_widget()
            self._recover_current_after_change(was_playing)
            
            # Status message
            if group_names_for_display:
                self.status.showMessage(f"Removed {total_items} items from {len(group_names_for_display)} groups (Ctrl+Z to undo)", 4000)
            else:
                self.status.showMessage(f"Removed {total_items} items (Ctrl+Z to undo)", 3000)

        except Exception as e:
            print(f"Remove selected items error: {e}")
            import traceback
            traceback.print_exc()
            self.status.showMessage(f"Remove failed: {e}", 4000)

    def _volume_up(self):
        v = min(100, self.volume_slider.value() + 5)
        self.volume_slider.setValue(v)
        self.set_volume(v)
        self.status.showMessage(f"Volume: {v}%", 1500)

    def _volume_down(self):
        v = max(0, self.volume_slider.value() - 5)
        self.volume_slider.setValue(v)
        self.set_volume(v)
        self.status.showMessage(f"Volume: {v}%", 1500)

    # Window + close
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            # --- THIS IS THE CRITICAL FIX ---
            # We ONLY update our state tracker when the window is in a visible, stable state.
            # We explicitly IGNORE the minimized state for this check.
            if not self.isMinimized():
                if self.isMaximized():
                    self._was_maximized = True
                else:
                    # This covers both Normal and FullScreen states that aren't Maximized
                    self._was_maximized = False
            
            # Now, separately handle the action of minimizing to the tray.
            # This logic now correctly uses the last known stable state.
            if self.isMinimized() and self.minimize_to_tray:
                QTimer.singleShot(100, self.hide)
                return # We've handled the event

        elif event.type() == QEvent.ApplicationFontChange:
            self._apply_dynamic_fonts()
        
        # Always call the superclass method for other events.
        super().changeEvent(event)
    def closeEvent(self, event):
            """Gracefully stop monitors, save state, and close."""
            # Save state first
            try:
                logger.info("Saving session and settings on exit...")
                self._save_session()
                self._save_settings()
            except Exception as e:
                logger.error(f"Failed to save state on close: {e}")

            # Stop background threads
            try:
                if getattr(self, 'audio_monitor', None):
                    self.audio_monitor.stop()
                    self.audio_monitor.wait(1000)
                if getattr(self, 'afk_monitor', None):
                    self.afk_monitor.stop()
                    self.afk_monitor.wait(1000)
                if getattr(self, 'ytdl_manager', None):
                    self.ytdl_manager.stop()
                    self.ytdl_manager.wait(1000)
            except Exception as e:
                logger.error(f"Error stopping background threads: {e}")
            
            # Call the base class method to ensure proper window closure
            super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    w = MediaPlayer()
    # Initialize typography AFTER the window builds and applies its theme so our QSS lands last
    from ui.typography import TypographyManager
    typo = TypographyManager(app, project_root=APP_DIR)
    typo.install()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
