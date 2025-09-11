"""
Error Handling Module for Silence Suzuka Player

Provides intelligent error handling for media playback to prevent error cascades
and provide graceful degradation when media fails to play.
"""

from .settings import ErrorHandlingSettings
from .handler import PlaybackErrorHandler, ErrorType

__all__ = ['ErrorHandlingSettings', 'PlaybackErrorHandler', 'ErrorType']