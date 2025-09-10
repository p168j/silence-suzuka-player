"""
Smart Queue Module for Silence Suzuka Player

Provides intelligent queue suggestions while maintaining zero UI bloat.
"""

from .settings import SmartQueueSettings
from .manager import SmartQueueManager

__all__ = ['SmartQueueSettings', 'SmartQueueManager']