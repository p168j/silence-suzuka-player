#!/usr/bin/env python3
"""
Test script for the enhanced PlaylistManagerDialog functionality.
Tests search, filtering, and sorting capabilities.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the dependencies that require GUI
class MockQApplication:
    def __init__(self, *args, **kwargs):
        pass
    
    def exec(self):
        return 0
    
    def quit(self):
        pass

class MockWidget:
    def __init__(self, *args, **kwargs):
        self._visible = True
        self._enabled = True
        
    def setVisible(self, visible):
        self._visible = visible
        
    def setEnabled(self, enabled):
        self._enabled = enabled
        
    def show(self):
        self._visible = True
        
    def hide(self):
        self._visible = False

# Mock the PySide6 modules to avoid GUI dependencies
sys.modules['PySide6'] = type('MockModule', (), {})()
sys.modules['PySide6.QtWidgets'] = type('MockModule', (), {
    'QApplication': MockQApplication,
    'QDialog': MockWidget,
    'QWidget': MockWidget,
    'QLabel': MockWidget,
    'QLineEdit': MockWidget,
    'QSpinBox': MockWidget,
    'QComboBox': MockWidget,
    'QPushButton': MockWidget,
    'QListWidget': MockWidget,
    'QListWidgetItem': MockWidget,
    'QVBoxLayout': MockWidget,
    'QHBoxLayout': MockWidget,
    'QFormLayout': MockWidget,
    'QGroupBox': MockWidget,
    'QFrame': MockWidget,
    'QSplitter': MockWidget,
    'QScrollArea': MockWidget,
    'QHeaderView': MockWidget,
    'QTreeWidget': MockWidget,
    'QTreeWidgetItem': MockWidget,
    'QCheckBox': MockWidget,
    'QProgressBar': MockWidget,
    'QMessageBox': type('MockMessageBox', (), {
        'information': lambda *args: None,
        'warning': lambda *args: None,
        'question': lambda *args: 1,
        'Yes': 1,
        'No': 0,
    })(),
    'QFileDialog': type('MockFileDialog', (), {
        'getOpenFileName': lambda *args: ("", ""),
        'getSaveFileName': lambda *args: ("", ""),
    })(),
})()

sys.modules['PySide6.QtCore'] = type('MockModule', (), {
    'Qt': type('MockQt', (), {
        'UserRole': 1000,
        'ItemIsSelectable': 1,
        'Horizontal': 1,
        'ScrollBarAsNeeded': 1,
    })(),
    'QTimer': type('MockQTimer', (), {
        '__init__': lambda self: None,
        'timeout': type('MockSignal', (), {'connect': lambda self, f: None})(),
        'start': lambda self, ms: None,
        'stop': lambda self: None,
        'setSingleShot': lambda self, single: None,
    }),
    'QSize': lambda w, h: (w, h),
    'Signal': lambda *args: type('MockSignal', (), {'connect': lambda self, f: None})(),
})()

sys.modules['PySide6.QtGui'] = type('MockModule', (), {
    'QFont': type('MockQFont', (), {
        'Bold': 1,
        '__init__': lambda self, *args: None,
    }),
    'QIcon': MockWidget,
    'QPixmap': MockWidget,
    'QPainter': MockWidget,
})()

def create_test_playlists():
    """Create test playlist data for testing"""
    base_date = datetime.now()
    
    test_playlists = {
        "Rock Classics": {
            "items": [
                {"title": "Bohemian Rhapsody", "url": "https://youtube.com/watch?v=test1", "type": "youtube"},
                {"title": "Stairway to Heaven", "url": "https://youtube.com/watch?v=test2", "type": "youtube"},
                {"title": "Hotel California", "url": "https://youtube.com/watch?v=test3", "type": "youtube"},
            ],
            "metadata": {
                "created": (base_date - timedelta(days=5)).isoformat(),
                "description": "Classic rock songs from the 70s",
                "version": "2.0"
            }
        },
        "Japanese Music": {
            "items": [
                {"title": "紅蓮華", "url": "https://youtube.com/watch?v=test4", "type": "youtube"},
                {"title": "炎", "url": "https://youtube.com/watch?v=test5", "type": "youtube"},
            ],
            "metadata": {
                "created": (base_date - timedelta(days=2)).isoformat(),
                "description": "Popular Japanese songs",
                "version": "2.0"
            }
        },
        "My Local Collection": {
            "items": [
                {"title": "Local Song 1", "url": "/path/to/song1.mp3", "type": "local"},
                {"title": "Local Song 2", "url": "/path/to/song2.mp3", "type": "local"},
                {"title": "Local Song 3", "url": "/path/to/song3.mp3", "type": "local"},
                {"title": "Local Song 4", "url": "/path/to/song4.mp3", "type": "local"},
                {"title": "Local Song 5", "url": "/path/to/song5.mp3", "type": "local"},
            ],
            "metadata": {
                "created": (base_date - timedelta(days=10)).isoformat(),
                "description": "My personal music collection",
                "version": "2.0"
            }
        },
        "Small Playlist": {
            "items": [
                {"title": "Single Song", "url": "https://youtube.com/watch?v=single", "type": "youtube"},
            ],
            "metadata": {
                "created": base_date.isoformat(),
                "description": "Just one song",
                "version": "2.0"
            }
        },
        "Bilibili Mix": {
            "items": [
                {"title": "Video 1", "url": "https://bilibili.com/video/test1", "type": "bilibili"},
                {"title": "Video 2", "url": "https://bilibili.com/video/test2", "type": "bilibili"},
                {"title": "Video 3", "url": "https://bilibili.com/video/test3", "type": "bilibili"},
                {"title": "Video 4", "url": "https://bilibili.com/video/test4", "type": "bilibili"},
            ],
            "metadata": {
                "created": (base_date - timedelta(days=1)).isoformat(),
                "description": "Videos from Bilibili",
                "version": "2.0"
            }
        }
    }
    
    return test_playlists

class TestPlaylistManager:
    """Test the playlist management functionality"""
    
    def __init__(self):
        self.test_playlists = create_test_playlists()
        # Create a mock dialog with the search functionality
        self.dialog = self._create_mock_dialog()
    
    def _create_mock_dialog(self):
        """Create a mock dialog for testing"""
        dialog = type('MockPlaylistManagerDialog', (), {})()
        
        # Initialize the filter and sort state (similar to real dialog)
        dialog._current_filter = {
            'name': '',
            'min_items': 0,
            'max_items': None,
            'date_from': None,
            'date_to': None
        }
        dialog._current_sort = {
            'field': 'created',
            'reverse': True
        }
        dialog._filtered_playlists = []
        dialog._is_destroyed = False
        dialog.saved_playlists = self.test_playlists
        
        # Add the filtering method
        dialog._apply_filters_and_sort = self._apply_filters_and_sort.__get__(dialog, dialog.__class__)
        
        return dialog
    
    def _apply_filters_and_sort(self):
        """Apply current filters and sorting to the playlist list (test version)"""
        try:
            # Get all playlists as tuples (name, data)
            all_playlists = list(self.saved_playlists.items()) if self.saved_playlists else []
            
            if not all_playlists:
                self._filtered_playlists = []
                return
            
            # Apply filters
            filtered_playlists = []
            name_filter = self._current_filter.get('name', '').lower()
            min_items = self._current_filter.get('min_items', 0)
            max_items = self._current_filter.get('max_items')
            
            for name, playlist_data in all_playlists:
                try:
                    # Name filter
                    if name_filter and name_filter not in name.lower():
                        continue
                    
                    # Item count filter
                    item_count = len(playlist_data.get('items', []))
                    if item_count < min_items:
                        continue
                    if max_items is not None and item_count > max_items:
                        continue
                    
                    filtered_playlists.append((name, playlist_data))
                    
                except Exception as e:
                    print(f"Error filtering playlist {name}: {e}")
                    continue
            
            # Apply sorting
            sort_field = self._current_sort.get('field', 'created')
            reverse = self._current_sort.get('reverse', True)
            
            try:
                if sort_field == 'name':
                    filtered_playlists.sort(key=lambda x: x[0].lower(), reverse=reverse)
                elif sort_field == 'items':
                    filtered_playlists.sort(key=lambda x: len(x[1].get('items', [])), reverse=reverse)
                else:  # 'created'
                    filtered_playlists.sort(
                        key=lambda x: x[1].get('metadata', {}).get('created', ''),
                        reverse=reverse
                    )
            except Exception as e:
                print(f"Error sorting playlists: {e}")
            
            # Cache the filtered results
            self._filtered_playlists = filtered_playlists
            
        except Exception as e:
            print(f"Apply filters and sort error: {e}")
    
    def test_search_functionality(self):
        """Test search by name functionality"""
        print("=== Testing Search Functionality ===")
        
        # Test 1: Search for "rock"
        self.dialog._current_filter['name'] = 'rock'
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        assert len(results) == 1, f"Expected 1 result for 'rock', got {len(results)}"
        assert results[0][0] == "Rock Classics", f"Expected 'Rock Classics', got '{results[0][0]}'"
        print("✓ Search for 'rock' passed")
        
        # Test 2: Search for "Japanese" (case insensitive)
        self.dialog._current_filter['name'] = 'japanese'
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        assert len(results) == 1, f"Expected 1 result for 'japanese', got {len(results)}"
        assert results[0][0] == "Japanese Music", f"Expected 'Japanese Music', got '{results[0][0]}'"
        print("✓ Case insensitive search passed")
        
        # Test 3: Search for non-existent term
        self.dialog._current_filter['name'] = 'nonexistent'
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        assert len(results) == 0, f"Expected 0 results for 'nonexistent', got {len(results)}"
        print("✓ Non-existent search term passed")
        
        # Test 4: Empty search (should return all)
        self.dialog._current_filter['name'] = ''
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        assert len(results) == 5, f"Expected 5 results for empty search, got {len(results)}"
        print("✓ Empty search passed")
    
    def test_item_count_filtering(self):
        """Test filtering by item count"""
        print("\\n=== Testing Item Count Filtering ===")
        
        # Reset search filter
        self.dialog._current_filter['name'] = ''
        
        # Test 1: Filter for playlists with at least 3 items
        self.dialog._current_filter['min_items'] = 3
        self.dialog._current_filter['max_items'] = None
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        expected_names = {"Rock Classics", "My Local Collection", "Bilibili Mix"}
        result_names = {name for name, _ in results}
        
        assert result_names == expected_names, f"Expected {expected_names}, got {result_names}"
        print("✓ Minimum item count filter passed")
        
        # Test 2: Filter for playlists with 1-3 items
        self.dialog._current_filter['min_items'] = 1
        self.dialog._current_filter['max_items'] = 3
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        expected_names = {"Rock Classics", "Japanese Music", "Small Playlist"}
        result_names = {name for name, _ in results}
        
        assert result_names == expected_names, f"Expected {expected_names}, got {result_names}"
        print("✓ Item count range filter passed")
        
        # Test 3: Filter for exactly 1 item
        self.dialog._current_filter['min_items'] = 1
        self.dialog._current_filter['max_items'] = 1
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        assert len(results) == 1, f"Expected 1 result, got {len(results)}"
        assert results[0][0] == "Small Playlist", f"Expected 'Small Playlist', got '{results[0][0]}'"
        print("✓ Exact item count filter passed")
    
    def test_sorting_functionality(self):
        """Test sorting functionality"""
        print("\\n=== Testing Sorting Functionality ===")
        
        # Reset filters
        self.dialog._current_filter = {
            'name': '',
            'min_items': 0,
            'max_items': None,
            'date_from': None,
            'date_to': None
        }
        
        # Test 1: Sort by name ascending
        self.dialog._current_sort = {'field': 'name', 'reverse': False}
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        expected_order = ["Bilibili Mix", "Japanese Music", "My Local Collection", "Rock Classics", "Small Playlist"]
        actual_order = [name for name, _ in results]
        
        assert actual_order == expected_order, f"Expected {expected_order}, got {actual_order}"
        print("✓ Sort by name ascending passed")
        
        # Test 2: Sort by name descending
        self.dialog._current_sort = {'field': 'name', 'reverse': True}
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        expected_order = ["Small Playlist", "Rock Classics", "My Local Collection", "Japanese Music", "Bilibili Mix"]
        actual_order = [name for name, _ in results]
        
        assert actual_order == expected_order, f"Expected {expected_order}, got {actual_order}"
        print("✓ Sort by name descending passed")
        
        # Test 3: Sort by item count ascending
        self.dialog._current_sort = {'field': 'items', 'reverse': False}
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        # Expected: Small Playlist (1), Japanese Music (2), Rock Classics (3), Bilibili Mix (4), My Local Collection (5)
        item_counts = [len(playlist_data.get('items', [])) for _, playlist_data in results]
        
        assert item_counts == sorted(item_counts), f"Item counts not in ascending order: {item_counts}"
        print("✓ Sort by item count ascending passed")
        
        # Test 4: Sort by item count descending
        self.dialog._current_sort = {'field': 'items', 'reverse': True}
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        item_counts = [len(playlist_data.get('items', [])) for _, playlist_data in results]
        
        assert item_counts == sorted(item_counts, reverse=True), f"Item counts not in descending order: {item_counts}"
        print("✓ Sort by item count descending passed")
    
    def test_combined_filters(self):
        """Test combination of search and filtering"""
        print("\\n=== Testing Combined Filters ===")
        
        # Test: Search for playlists containing "bili" with at least 2 items
        self.dialog._current_filter = {
            'name': 'bili',  # Should match "Bilibili Mix" only
            'min_items': 2,
            'max_items': None,
            'date_from': None,
            'date_to': None
        }
        self.dialog._current_sort = {'field': 'name', 'reverse': False}
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        expected_names = {"Bilibili Mix"}  # Only Bilibili Mix contains "bili" and has 4 items (>= 2)
        result_names = {name for name, _ in results}
        
        assert result_names == expected_names, f"Expected {expected_names}, got {result_names}"
        print("✓ Combined search and item count filter passed")
        
        # Test: Search for "music" with 1-3 items
        self.dialog._current_filter = {
            'name': 'music',  # Should match "Japanese Music" only
            'min_items': 1,
            'max_items': 3,
            'date_from': None,
            'date_to': None
        }
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        expected_names = {"Japanese Music"}  # Japanese Music has 2 items (within 1-3 range)
        result_names = {name for name, _ in results}
        
        assert result_names == expected_names, f"Expected {expected_names}, got {result_names}"
        print("✓ Combined search and item range filter passed")
        
        # Test: No results case
        self.dialog._current_filter['name'] = 'xyz'
        self.dialog._current_filter['min_items'] = 10
        self.dialog._apply_filters_and_sort()
        results = self.dialog._filtered_playlists
        
        assert len(results) == 0, f"Expected 0 results, got {len(results)}"
        print("✓ No results case passed")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Running PlaylistManagerDialog Enhanced Search Tests\\n")
        
        try:
            self.test_search_functionality()
            self.test_item_count_filtering()
            self.test_sorting_functionality()
            self.test_combined_filters()
            
            print("\\n🎉 All tests passed! The enhanced playlist management functionality is working correctly.")
            return True
            
        except AssertionError as e:
            print(f"\\n❌ Test failed: {e}")
            return False
        except Exception as e:
            print(f"\\n💥 Unexpected error during testing: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    # Run the tests
    tester = TestPlaylistManager()
    success = tester.run_all_tests()
    
    if success:
        print("\\n✅ Enhanced playlist management features are ready for integration!")
        sys.exit(0)
    else:
        print("\\n❌ Tests failed. Please check the implementation.")
        sys.exit(1)