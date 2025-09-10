#!/usr/bin/env python3
"""
Smart Queue Settings for Silence Suzuka Player

Provides configuration for smart queue behavior following the typography manager pattern.
"""

from dataclasses import dataclass


@dataclass
class SmartQueueSettings:
    """Smart Queue configuration settings"""
    
    # Main toggle
    enabled: bool = False
    
    # Feature toggles (only active when smart queue is enabled)
    time_aware: bool = True
    content_similarity: bool = True
    learning_enabled: bool = True
    
    # Configuration
    max_suggestions: int = 3
    
    # Time-aware settings
    short_video_threshold: int = 300  # seconds (5 minutes)
    long_session_threshold: int = 1800  # seconds (30 minutes) 
    
    # Learning settings
    min_learning_samples: int = 10  # minimum interactions before learning kicks in
    pattern_weight: float = 0.3  # how much weight to give to learned patterns
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'enabled': self.enabled,
            'time_aware': self.time_aware,
            'content_similarity': self.content_similarity,
            'learning_enabled': self.learning_enabled,
            'max_suggestions': self.max_suggestions,
            'short_video_threshold': self.short_video_threshold,
            'long_session_threshold': self.long_session_threshold,
            'min_learning_samples': self.min_learning_samples,
            'pattern_weight': self.pattern_weight
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(
            enabled=data.get('enabled', False),
            time_aware=data.get('time_aware', True),
            content_similarity=data.get('content_similarity', True),
            learning_enabled=data.get('learning_enabled', True),
            max_suggestions=data.get('max_suggestions', 3),
            short_video_threshold=data.get('short_video_threshold', 300),
            long_session_threshold=data.get('long_session_threshold', 1800),
            min_learning_samples=data.get('min_learning_samples', 10),
            pattern_weight=data.get('pattern_weight', 0.3)
        )