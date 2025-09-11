"""
Intelligent error handler for media playback.
Implements circuit breaker pattern, exponential backoff, and error classification.
"""

import time
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

class ErrorType(Enum):
    """Classification of different error types"""
    NETWORK = "network"
    MEDIA_NOT_FOUND = "media_not_found" 
    AUTHENTICATION = "authentication"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class ErrorEvent:
    """Represents a single error event"""
    timestamp: float
    error_type: ErrorType
    error_message: str
    playlist_index: int
    url: str
    retry_count: int = 0

class PlaybackErrorHandler:
    """
    Intelligent error handler that prevents error cascades and provides graceful degradation.
    
    Features:
    - Error classification (network, media not found, auth, system)
    - Circuit breaker pattern to pause auto-advance after consecutive failures
    - Exponential backoff for retries
    - Different retry strategies per error type
    """
    
    def __init__(self, settings):
        self.settings = settings
        
        # Error tracking
        self.error_history: List[ErrorEvent] = []
        self.consecutive_failures = 0
        self.last_successful_play = time.time()
        
        # Circuit breaker state
        self.circuit_breaker_active = False
        self.circuit_breaker_activated_at = 0
        
        # Current item retry tracking
        self.current_item_retries: Dict[int, int] = {}  # playlist_index -> retry_count
        self.retry_delays: Dict[int, float] = {}  # playlist_index -> next_retry_time
        
        # Network connectivity
        self.is_offline = False
        self.last_network_check = 0
        self.network_check_interval = 30  # Check every 30 seconds
    
    def check_network_connectivity(self) -> bool:
        """
        Check if network connectivity is available.
        Uses a simple approach by checking if we can resolve common DNS names.
        """
        import socket
        
        # Don't check too frequently
        if time.time() - self.last_network_check < self.network_check_interval:
            return not self.is_offline
        
        self.last_network_check = time.time()
        
        try:
            # Try to resolve a few common domains
            socket.gethostbyname("google.com")
            self.is_offline = False
            return True
        except (socket.gaierror, OSError):
            try:
                # Fallback to another domain
                socket.gethostbyname("cloudflare.com")
                self.is_offline = False
                return True
            except (socket.gaierror, OSError):
                self.is_offline = True
                return False
        
    def classify_error(self, error_message: str, url: str = "") -> ErrorType:
        """
        Classify an error based on the error message and context.
        
        Args:
            error_message: The error message from MPV
            url: The URL that failed (for additional context)
            
        Returns:
            ErrorType enum value
        """
        error_lower = error_message.lower()
        
        # Network-related errors (temporary, should retry)
        network_patterns = [
            'network', 'connection', 'timeout', 'dns', 'resolve',
            'unreachable', 'temporary failure', 'socket error',
            'ssl error', 'certificate', 'handshake failed'
        ]
        
        # Media not found errors (permanent, don't retry much)
        not_found_patterns = [
            'not found', '404', 'file does not exist', 'no such file',
            'unavailable', 'removed', 'deleted', 'private video',
            'video unavailable', 'this video is not available'
        ]
        
        # Authentication errors (need user intervention)
        auth_patterns = [
            'authentication', 'unauthorized', '401', '403', 'forbidden',
            'access denied', 'login required', 'permission denied',
            'members only', 'private'
        ]
        
        # System/MPV errors (may be temporary)
        system_patterns = [
            'format not supported', 'codec', 'decoder', 'demuxer',
            'no video', 'no audio', 'invalid data', 'corrupted'
        ]
        
        # Check patterns in order of specificity
        for pattern in network_patterns:
            if pattern in error_lower:
                return ErrorType.NETWORK
                
        for pattern in not_found_patterns:
            if pattern in error_lower:
                return ErrorType.MEDIA_NOT_FOUND
                
        for pattern in auth_patterns:
            if pattern in error_lower:
                return ErrorType.AUTHENTICATION
                
        for pattern in system_patterns:
            if pattern in error_lower:
                return ErrorType.SYSTEM
        
        # If no pattern matches and it's an online URL, check network connectivity
        is_online_url = url.startswith(('http://', 'https://')) if url else False
        if is_online_url and not self.check_network_connectivity():
            return ErrorType.NETWORK
        
        return ErrorType.UNKNOWN
    
    def should_retry(self, playlist_index: int, error_type: ErrorType) -> Tuple[bool, float]:
        """
        Determine if we should retry playing this item and when.
        
        Args:
            playlist_index: Index of the failed item
            error_type: Classification of the error
            
        Returns:
            Tuple of (should_retry, delay_seconds)
        """
        if not self.settings.enabled:
            return False, 0
        
        # Check if we're in circuit breaker mode
        if self.circuit_breaker_active:
            return False, 0
            
        # Get current retry count for this item
        current_retries = self.current_item_retries.get(playlist_index, 0)
        
        # Get max retries for this error type
        max_retries = self._get_max_retries_for_error_type(error_type)
        
        if current_retries >= max_retries:
            return False, 0
            
        # Calculate exponential backoff delay
        delay = min(
            self.settings.initial_backoff_delay * (self.settings.backoff_multiplier ** current_retries),
            self.settings.max_backoff_delay
        )
        
        return True, delay
    
    def record_error(self, error_message: str, playlist_index: int, url: str) -> ErrorEvent:
        """
        Record an error and update internal state.
        
        Args:
            error_message: The error message
            playlist_index: Index of the failed playlist item
            url: URL that failed to play
            
        Returns:
            ErrorEvent object representing this error
        """
        error_type = self.classify_error(error_message, url)
        retry_count = self.current_item_retries.get(playlist_index, 0)
        
        error_event = ErrorEvent(
            timestamp=time.time(),
            error_type=error_type,
            error_message=error_message,
            playlist_index=playlist_index,
            url=url,
            retry_count=retry_count
        )
        
        # Add to history (with limit)
        self.error_history.append(error_event)
        if len(self.error_history) > self.settings.error_history_limit:
            self.error_history = self.error_history[-self.settings.error_history_limit:]
        
        # Update consecutive failure count
        self.consecutive_failures += 1
        
        # Check if we should activate circuit breaker
        if self.consecutive_failures >= self.settings.max_consecutive_failures:
            self._activate_circuit_breaker()
        
        # Update retry count for this item
        self.current_item_retries[playlist_index] = retry_count + 1
        
        return error_event
    
    def record_success(self, playlist_index: int):
        """Record a successful playback to reset error tracking."""
        self.consecutive_failures = 0
        self.last_successful_play = time.time()
        
        # Clear retry count for this item
        if playlist_index in self.current_item_retries:
            del self.current_item_retries[playlist_index]
        if playlist_index in self.retry_delays:
            del self.retry_delays[playlist_index]
            
        # Deactivate circuit breaker on success
        if self.circuit_breaker_active:
            self.circuit_breaker_active = False
            print("Error Handling: Circuit breaker deactivated after successful playback")
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is currently active."""
        if not self.circuit_breaker_active:
            return False
            
        # Check if timeout has expired
        if time.time() - self.circuit_breaker_activated_at > self.settings.circuit_breaker_timeout:
            self.circuit_breaker_active = False
            print("Error Handling: Circuit breaker timeout expired, resuming auto-advance")
            return False
            
        return True
    
    def get_circuit_breaker_remaining_time(self) -> float:
        """Get remaining time for circuit breaker timeout."""
        if not self.circuit_breaker_active:
            return 0
        return max(0, self.settings.circuit_breaker_timeout - (time.time() - self.circuit_breaker_activated_at))
    
    def reset_circuit_breaker(self):
        """Manually reset the circuit breaker (user action)."""
        self.circuit_breaker_active = False
        self.consecutive_failures = 0
        print("Error Handling: Circuit breaker manually reset")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors for UI display."""
        if not self.error_history:
            return {"total_errors": 0, "by_type": {}, "recent_errors": []}
        
        # Count errors by type in last hour
        one_hour_ago = time.time() - 3600
        recent_errors = [e for e in self.error_history if e.timestamp > one_hour_ago]
        
        by_type = {}
        for error in recent_errors:
            error_type_str = error.error_type.value
            by_type[error_type_str] = by_type.get(error_type_str, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "by_type": by_type,
            "consecutive_failures": self.consecutive_failures,
            "circuit_breaker_active": self.circuit_breaker_active,
            "circuit_breaker_remaining": self.get_circuit_breaker_remaining_time(),
            "is_offline": self.is_offline,
            "recent_errors": [
                {
                    "timestamp": error.timestamp,
                    "type": error.error_type.value,
                    "message": error.error_message[:100],  # Truncate long messages
                    "playlist_index": error.playlist_index,
                    "retry_count": error.retry_count
                }
                for error in recent_errors[-10:]  # Last 10 errors
            ]
        }
    
    def cleanup_old_errors(self):
        """Remove old errors from history."""
        cutoff_time = time.time() - (self.settings.cleanup_error_history_days * 24 * 3600)
        self.error_history = [e for e in self.error_history if e.timestamp > cutoff_time]
    
    def _activate_circuit_breaker(self):
        """Activate the circuit breaker to pause auto-advance."""
        self.circuit_breaker_active = True
        self.circuit_breaker_activated_at = time.time()
        print(f"Error Handling: Circuit breaker activated after {self.consecutive_failures} consecutive failures")
        print(f"Error Handling: Auto-advance paused for {self.settings.circuit_breaker_timeout} seconds")
    
    def _get_max_retries_for_error_type(self, error_type: ErrorType) -> int:
        """Get maximum retry count for a specific error type."""
        if error_type == ErrorType.NETWORK:
            return self.settings.max_retries_network
        elif error_type == ErrorType.SYSTEM:
            return self.settings.max_retries_system
        elif error_type == ErrorType.AUTHENTICATION:
            return self.settings.max_retries_auth
        elif error_type == ErrorType.MEDIA_NOT_FOUND:
            return self.settings.max_retries_media_not_found
        else:
            return 1  # Default for unknown errors