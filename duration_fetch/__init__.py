#!/usr/bin/env python3
"""
Duration Fetch Module for Silence Suzuka Player

Provides background duration fetching, caching, and settings management
to eliminate the UX bottleneck of manual duration fetching for online videos.
"""

from .settings import DurationFetchSettings
from .cache import DurationCache
from .background_fetcher import BackgroundDurationFetcher

__all__ = ['DurationFetchSettings', 'DurationCache', 'BackgroundDurationFetcher']