#!/usr/bin/env python3
"""
Background Duration Fetcher for Silence Suzuka Player

Queue-based background duration fetching system with worker threads,
prioritization, and graceful error handling.
"""

import time
import queue
import threading
import os
from typing import List, Dict, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

from PySide6.QtCore import QThread, Signal, QTimer

from .settings import DurationFetchSettings
from .cache import DurationCache


class FetchPriority(Enum):
    """Priority levels for duration fetching"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class FetchRequest:
    """A single duration fetch request"""
    playlist_index: int
    item: Dict[str, Any]
    priority: FetchPriority = FetchPriority.NORMAL
    added_time: float = field(default_factory=time.time)
    retry_count: int = 0
    
    def __lt__(self, other):
        """For priority queue sorting (higher priority first)"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        # If same priority, newer requests first
        return self.added_time > other.added_time


class WorkerThread(QThread):
    """Worker thread for fetching individual durations"""
    
    fetchCompleted = Signal(int, int, str)  # playlist_index, duration, source
    fetchFailed = Signal(int, str)  # playlist_index, error_message
    
    def __init__(self, worker_id: int, request_queue: queue.PriorityQueue, 
                 cache: DurationCache, settings: DurationFetchSettings):
        super().__init__()
        self.worker_id = worker_id
        self.request_queue = request_queue
        self.cache = cache
        self.settings = settings
        self._should_stop = False
        self._current_request = None
    
    def stop(self):
        """Stop the worker thread"""
        self._should_stop = True
        # Add a poison pill to wake up the thread
        try:
            self.request_queue.put((FetchPriority.LOW, None), block=False)
        except queue.Full:
            pass
    
    def get_current_item(self) -> Optional[Dict[str, Any]]:
        """Get the currently processing item"""
        return self._current_request.item if self._current_request else None
    
    def run(self):
        """Main worker thread loop"""
        while not self._should_stop:
            try:
                # Get next request with timeout
                try:
                    priority, request = self.request_queue.get(timeout=1.0)
                    if request is None or self._should_stop:
                        break
                except queue.Empty:
                    continue
                
                self._current_request = request
                
                # Skip if already cached
                url = request.item.get('url', '')
                cached_duration = self.cache.get(url)
                if cached_duration is not None:
                    self.fetchCompleted.emit(request.playlist_index, cached_duration, 'cache')
                    continue
                
                # Perform the actual fetch
                success, duration, source, error = self._fetch_duration(request)
                
                if success:
                    # Cache the result
                    self.cache.set(url, duration, source)
                    self.fetchCompleted.emit(request.playlist_index, duration, source)
                else:
                    self.fetchFailed.emit(request.playlist_index, error or 'Unknown error')
                
                # Rate limiting delay
                if self.settings.delay_between_fetches_ms > 0:
                    time.sleep(self.settings.delay_between_fetches_ms / 1000.0)
                
            except Exception as e:
                if self._current_request:
                    self.fetchFailed.emit(self._current_request.playlist_index, str(e))
            finally:
                self._current_request = None
    
    def _fetch_duration(self, request: FetchRequest) -> Tuple[bool, int, str, Optional[str]]:
        """
        Fetch duration for a single item.
        
        Returns:
            (success, duration, source, error_message)
        """
        item = request.item
        item_type = item.get('type', 'unknown')
        url = item.get('url', '')
        
        try:
            if item_type == 'local':
                return self._fetch_local_duration(url)
            elif item_type in ('youtube', 'bilibili'):
                return self._fetch_online_duration(url, item_type)
            else:
                return False, 0, 'unknown', f'Unsupported item type: {item_type}'
                
        except Exception as e:
            return False, 0, 'error', str(e)
    
    def _fetch_local_duration(self, url: str) -> Tuple[bool, int, str, Optional[str]]:
        """Fetch duration for local file using mpv"""
        try:
            # Import here to avoid issues if mpv is not available
            from mpv import MPV
            import os
            
            # Convert file:// URL to path
            path = self._url_to_path(url)
            if not path or not os.path.exists(path):
                return False, 0, 'mpv', f'File not found: {path}'
            
            # Create headless mpv instance
            mpv_instance = None
            try:
                mpv_instance = MPV(
                    vid='no',
                    audio_display='no', 
                    vo='null',
                    ao='null',
                    force_window='no',
                    pause='yes',
                    idle='yes',
                    osc=False,
                    ytdl=False,
                    msg_level='all=no'
                )
                
                # Load file and wait for duration
                mpv_instance.loadfile(path, 'replace')
                start_time = time.time()
                
                while time.time() - start_time < self.settings.fetch_timeout:
                    if self._should_stop:
                        return False, 0, 'mpv', 'Cancelled'
                    
                    try:
                        duration = mpv_instance.duration
                        if duration is not None and duration > 0:
                            return True, int(duration), 'mpv', None
                    except Exception:
                        pass
                    
                    time.sleep(0.1)
                
                return False, 0, 'mpv', 'Timeout waiting for duration'
                
            finally:
                if mpv_instance:
                    try:
                        mpv_instance.terminate()
                    except Exception:
                        pass
                        
        except ImportError:
            return False, 0, 'mpv', 'MPV not available'
        except Exception as e:
            return False, 0, 'mpv', str(e)
    
    def _fetch_online_duration(self, url: str, item_type: str) -> Tuple[bool, int, str, Optional[str]]:
        """Fetch duration for online video using yt-dlp"""
        try:
            import yt_dlp
            import subprocess
            
            # Prepare yt-dlp options
            opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': False,
            }
            
            # Add Bilibili-specific optimizations
            if item_type == 'bilibili':
                # Aggressive format selection - skip 1080p+ negotiations for faster resolution
                opts.update({
                    'format': 'best[height<=720]/best[height<=480]/best',
                    'format_sort': ['res:720', 'fps', 'codec:h264'],
                    
                    # Network optimization - aggressive timeouts for faster response
                    'socket_timeout': 6,        # Down from 15s default
                    'retries': 1,               # Fail fast, don't retry much
                    'fragment_retries': 1,      # Less retry overhead
                    
                    # Connection improvements
                    'http_chunk_size': 1048576,           # 1MB chunks
                    'concurrent_fragment_downloads': 3,    # Parallel processing
                    
                    # Skip unnecessary processing for duration-only fetching
                    'writesubtitles': False,
                    'writeautomaticsub': False, 
                    'writeinfojson': False,
                    'writethumbnail': False,
                    
                    # Faster processing preferences
                    'prefer_ffmpeg': True,
                    'keepvideo': False,
                })
                
                # Add cookies if available (preserve existing functionality)
                cookies_file = Path(__file__).parent.parent / 'cookies.txt'
                if cookies_file.exists():
                    opts['cookiefile'] = str(cookies_file)
            
            # Use yt-dlp with timeout
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Set socket timeout
                ydl.params['socket_timeout'] = self.settings.fetch_timeout
                
                info = ydl.extract_info(url, download=False)
                if info:
                    duration = int(info.get('duration', 0))
                    if duration > 0:
                        return True, duration, 'yt-dlp', None
                    else:
                        return False, 0, 'yt-dlp', 'No duration found'
                else:
                    return False, 0, 'yt-dlp', 'Failed to extract info'
                    
        except ImportError:
            return False, 0, 'yt-dlp', 'yt-dlp not available'
        except Exception as e:
            error_msg = str(e)
            
            # Handle common yt-dlp errors
            if 'timeout' in error_msg.lower():
                return False, 0, 'yt-dlp', 'Network timeout'
            elif 'unavailable' in error_msg.lower():
                return False, 0, 'yt-dlp', 'Video unavailable'
            elif 'private' in error_msg.lower():
                return False, 0, 'yt-dlp', 'Private video'
            else:
                return False, 0, 'yt-dlp', error_msg
    
    def _url_to_path(self, url: str) -> str:
        """Convert file:// URL to local path"""
        if url.startswith('file://'):
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            path = unquote(parsed.path)
            # Windows path fix
            if os.name == 'nt' and path.startswith('/'):
                path = path[1:]
            return path
        else:
            return url


class BackgroundDurationFetcher(QThread):
    """
    Main background duration fetcher with worker thread pool and intelligent queuing.
    """
    
    # Signals
    durationReady = Signal(int, int, str)  # playlist_index, duration, source
    fetchProgress = Signal(int, int)  # completed, total
    fetchError = Signal(int, str)  # playlist_index, error
    statsUpdated = Signal(dict)  # cache statistics
    
    def __init__(self, config_dir: Path, settings: DurationFetchSettings, parent=None):
        super().__init__(parent)
        self.config_dir = config_dir
        self.settings = settings
        
        # Initialize cache
        self.cache = DurationCache(config_dir, settings)
        
        # Request queue (priority queue)
        self.request_queue = queue.PriorityQueue()
        
        # Worker threads
        self.workers: List[WorkerThread] = []
        
        # Statistics
        self.stats = {
            'queued': 0,
            'completed': 0,
            'failed': 0,
            'cache_hits': 0
        }
        
        # Auto-save timer
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._periodic_save)
        self.save_timer.start(30000)  # Save every 30 seconds
        
        self._should_stop = False
        
    def start_workers(self):
        """Start worker threads"""
        if self.workers:
            return  # Already started
        
        worker_count = max(1, min(self.settings.worker_thread_count, 8))
        
        for i in range(worker_count):
            worker = WorkerThread(i, self.request_queue, self.cache, self.settings)
            worker.fetchCompleted.connect(self._on_fetch_completed)
            worker.fetchFailed.connect(self._on_fetch_failed)
            self.workers.append(worker)
            worker.start()
    
    def stop_workers(self):
        """Stop all worker threads"""
        self._should_stop = True
        
        # Stop all workers
        for worker in self.workers:
            worker.stop()
        
        # Wait for workers to finish (with timeout)
        for worker in self.workers:
            worker.wait(3000)  # 3 second timeout
        
        self.workers.clear()
        
        # Save cache
        self.cache.save()
    
    def enqueue_items(self, items: List[Tuple[int, Dict[str, Any]]], 
                     priority: FetchPriority = FetchPriority.NORMAL,
                     visible_indices: Optional[List[int]] = None):
        """
        Queue items for duration fetching with intelligent prioritization.
        
        Args:
            items: List of (playlist_index, item_dict) tuples
            priority: Base priority for all items
            visible_indices: List of currently visible playlist indices for prioritization
        """
        if not self.settings.auto_fetch_enabled:
            return
        
        self.start_workers()
        
        for playlist_index, item in items:
            # Skip if already has duration or not fetchable
            if item.get('duration'):
                continue
                
            item_type = item.get('type')
            if item_type not in ('youtube', 'bilibili', 'local'):
                continue
            
            url = item.get('url', '')
            if not url:
                continue
            
            # Check cache first
            cached_duration = self.cache.get(url)
            if cached_duration is not None:
                self.stats['cache_hits'] += 1
                self.durationReady.emit(playlist_index, cached_duration, 'cache')
                continue
            
            # Determine priority
            item_priority = priority
            if self.settings.prioritize_visible and visible_indices:
                if playlist_index in visible_indices:
                    item_priority = FetchPriority.HIGH
            
            # Create and queue request
            request = FetchRequest(
                playlist_index=playlist_index,
                item=item,
                priority=item_priority
            )
            
            try:
                self.request_queue.put((item_priority, request), block=False)
                self.stats['queued'] += 1
            except queue.Full:
                # Queue is full, skip this item
                print(f"Duration Fetch: Queue full, skipping item {playlist_index}")
                break
        
        # Update stats
        self._emit_stats()
    
    def enqueue_single_item(self, playlist_index: int, item: Dict[str, Any], 
                           priority: FetchPriority = FetchPriority.URGENT):
        """Queue a single item for immediate fetching"""
        self.enqueue_items([(playlist_index, item)], priority)
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache and fetch statistics"""
        cache_stats = self.cache.get_stats()
        
        # Add worker status
        worker_status = []
        for worker in self.workers:
            current_item = worker.get_current_item()
            status = {
                'worker_id': worker.worker_id,
                'active': current_item is not None,
                'current_url': current_item.get('url', '') if current_item else None
            }
            worker_status.append(status)
        
        return {
            'cache': cache_stats,
            'queue_size': self.request_queue.qsize(),
            'workers': worker_status,
            'fetch_stats': self.stats.copy()
        }
    
    def clear_cache(self):
        """Clear the duration cache"""
        self.cache.clear()
        self._emit_stats()
    
    def _on_fetch_completed(self, playlist_index: int, duration: int, source: str):
        """Handle successful duration fetch"""
        self.stats['completed'] += 1
        self.durationReady.emit(playlist_index, duration, source)
        self._emit_stats()
    
    def _on_fetch_failed(self, playlist_index: int, error: str):
        """Handle failed duration fetch"""
        self.stats['failed'] += 1
        self.fetchError.emit(playlist_index, error)
        self._emit_stats()
    
    def _emit_stats(self):
        """Emit updated statistics"""
        total = self.stats['completed'] + self.stats['failed'] + self.stats['cache_hits']
        self.fetchProgress.emit(total, self.stats['queued'] + total)
        self.statsUpdated.emit(self.get_cache_statistics())
    
    def _periodic_save(self):
        """Periodically save cache to disk"""
        if not self._should_stop:
            self.cache.save()
    
    def update_settings(self, settings: DurationFetchSettings):
        """Update settings and restart workers if needed"""
        old_worker_count = self.settings.worker_thread_count
        self.settings = settings
        self.cache.settings = settings
        
        # Restart workers if count changed
        if settings.worker_thread_count != old_worker_count:
            self.stop_workers()
            if settings.auto_fetch_enabled:
                self.start_workers()
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_workers()