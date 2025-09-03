# Metadata Fetching Performance Improvements

## Overview

This update addresses the significant performance issues with metadata fetching in the Silence Suzuka Player, particularly for duration fetching operations that were blocking the UI and causing noticeable lag.

## Key Improvements

### 1. Enhanced MetadataWorker Class
- **Persistent yt-dlp Instances**: Reuses expensive yt-dlp instances across requests instead of creating new ones each time
- **Multi-field Support**: Can fetch titles, durations, descriptions, uploaders, and view counts in a single request
- **Better Error Handling**: Provides detailed error messages and status updates
- **Configurable Timeouts**: Improved timeout and retry settings for better reliability

### 2. Intelligent Caching System (MetadataManager)
- **Persistent Cache**: Stores metadata on disk to avoid re-fetching across sessions
- **Freshness Checking**: Configurable cache expiration (default 7 days) to balance performance vs accuracy
- **Selective Retrieval**: Can fetch only specific fields from cache when needed
- **Automatic Cleanup**: Removes old cache entries to prevent bloat
- **Fast Operations**: Sub-millisecond cache lookups for real-time performance

### 3. Background Duration Fetching
- **Automatic Processing**: Optionally fetches durations in background when new items are added
- **Non-blocking**: Runs in separate thread to maintain UI responsiveness
- **Cache-aware**: Checks cache first before making network requests
- **Configurable**: Can be enabled/disabled in settings

### 4. Enhanced Progress Feedback
- **Detailed Progress**: Shows current/total items with percentage completion
- **Status Messages**: Real-time updates on what URL is being processed
- **Cache Integration**: Progress accounts for items loaded from cache
- **Cancellation Support**: Users can cancel long-running operations

### 5. Settings Integration
- **Auto-fetch Toggle**: Enable/disable automatic background duration fetching
- **Cache Duration**: Configure how long to keep metadata in cache
- **User Control**: Clear visibility and control over metadata operations

## Performance Benefits

### Before Optimization:
- Sequential processing: 1 item at a time
- No caching: Re-fetched same URLs repeatedly
- Expensive operations: New yt-dlp instance per request
- UI blocking: Manual fetching could freeze interface
- Poor feedback: Minimal progress indication

### After Optimization:
- **Faster Initial Load**: Cache provides instant results for known URLs
- **Reduced Network Traffic**: Avoids redundant API calls
- **Better Responsiveness**: Background processing keeps UI interactive
- **Improved User Experience**: Clear progress indication and cancellation
- **Efficient Resource Usage**: Reused yt-dlp instances and intelligent caching

## Usage

### Automatic Background Fetching
When enabled (default), durations are automatically fetched in the background when new items are added to playlists. Users see a subtle notification and can continue using the application.

### Manual Duration Fetching
The manual "⏱️" button now shows enhanced progress with cache information and allows cancellation. The process is significantly faster due to caching and persistent yt-dlp instances.

### Settings Configuration
Users can control metadata fetching behavior in Settings → UI & Panels:
- Enable/disable automatic background fetching
- Configure cache duration (1-30 days)

## Technical Implementation

### File Structure
- **MetadataWorker**: Enhanced worker thread for parallel metadata fetching
- **MetadataManager**: Persistent caching and cache management
- **DurationFetcher**: Backward-compatible wrapper with enhanced features
- **Settings Integration**: New settings in UI & Panels tab

### Cache Location
Metadata cache is stored in:
- Windows: `%APPDATA%/SilenceSuzukaPlayer/metadata_cache.json`
- macOS: `~/Library/Application Support/SilenceSuzukaPlayer/metadata_cache.json`
- Linux: `~/.config/SilenceSuzukaPlayer/metadata_cache.json`

### Compatibility
- Maintains full backward compatibility with existing playlist files
- Graceful degradation if cache files are corrupted or missing
- Works with existing YouTube and Bilibili URL patterns

## Testing

The implementation includes comprehensive testing of the caching system:
- Cache persistence across application restarts
- Performance testing with 100+ items
- Freshness checking and cleanup operations
- Error handling and edge cases

All tests pass successfully, confirming the reliability and performance of the new system.