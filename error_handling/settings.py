"""
Settings for the intelligent error handling system.
"""

import json
from pathlib import Path
from typing import Dict, Any

class ErrorHandlingSettings:
    """Settings for intelligent error handling"""
    
    def __init__(self):
        # Core error handling settings
        self.enabled = True
        
        # Circuit breaker settings
        self.max_consecutive_failures = 3
        self.circuit_breaker_timeout = 60  # seconds to pause auto-advance after circuit breaker activation
        
        # Backoff settings
        self.initial_backoff_delay = 1.0  # seconds
        self.backoff_multiplier = 2.0
        self.max_backoff_delay = 30.0  # seconds
        
        # Retry limits per error type
        self.max_retries_network = 3
        self.max_retries_system = 2
        self.max_retries_auth = 0  # Don't auto-retry auth errors
        self.max_retries_media_not_found = 0  # Don't auto-retry permanent errors
        
        # User experience settings  
        self.show_error_notifications = True
        self.auto_skip_permanent_errors = True
        self.pause_on_network_offline = True
        
        # Advanced settings
        self.error_history_limit = 100  # Keep track of last N errors
        self.cleanup_error_history_days = 7
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization"""
        return {
            'enabled': self.enabled,
            'max_consecutive_failures': self.max_consecutive_failures,
            'circuit_breaker_timeout': self.circuit_breaker_timeout,
            'initial_backoff_delay': self.initial_backoff_delay,
            'backoff_multiplier': self.backoff_multiplier,
            'max_backoff_delay': self.max_backoff_delay,
            'max_retries_network': self.max_retries_network,
            'max_retries_system': self.max_retries_system,
            'max_retries_auth': self.max_retries_auth,
            'max_retries_media_not_found': self.max_retries_media_not_found,
            'show_error_notifications': self.show_error_notifications,
            'auto_skip_permanent_errors': self.auto_skip_permanent_errors,
            'pause_on_network_offline': self.pause_on_network_offline,
            'error_history_limit': self.error_history_limit,
            'cleanup_error_history_days': self.cleanup_error_history_days
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """Load settings from dictionary"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def save_to_file(self, file_path: Path):
        """Save settings to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error Handling: Failed to save settings: {e}")
    
    def load_from_file(self, file_path: Path):
        """Load settings from JSON file"""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    self.from_dict(data)
        except Exception as e:
            print(f"Error Handling: Failed to load settings: {e}")