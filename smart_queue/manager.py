#!/usr/bin/env python3
"""
Smart Queue Manager for Silence Suzuka Player

Analyzes content and user patterns to provide intelligent queue suggestions.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse

from .settings import SmartQueueSettings


class SmartQueueManager:
    """
    Manages intelligent queue suggestions based on content analysis and user patterns.
    
    Features:
    - Time-aware suggestions (short videos when limited time)
    - Content similarity matching 
    - Learning from user behavior patterns
    - Time-of-day context awareness
    """
    
    def __init__(self, config_dir: Path, settings: Optional[SmartQueueSettings] = None):
        self.config_dir = config_dir
        self.settings = settings or SmartQueueSettings()
        
        # Learning data storage
        self.learning_file = config_dir / 'smart_queue_learning.json'
        self.learning_data = self._load_learning_data()
        
        # Current session tracking
        self.session_start = time.time()
        self.recent_skips = []  # Track recent skip events
        self.recent_completions = []  # Track recent completion events
        
    def _load_learning_data(self) -> Dict[str, Any]:
        """Load learning data from persistent storage"""
        if not self.learning_file.exists():
            return {
                'patterns': {},  # User behavior patterns
                'preferences': {},  # Content preferences
                'time_patterns': {},  # Time-based patterns
                'skip_rates': {},  # Skip rates by content type/source
                'completion_rates': {},  # Completion rates
                'last_updated': time.time()
            }
        
        try:
            with open(self.learning_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return self._load_learning_data()  # Return empty data if loading fails
    
    def _save_learning_data(self):
        """Save learning data to persistent storage"""
        if not self.settings.learning_enabled:
            return
            
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            self.learning_data['last_updated'] = time.time()
            
            temp_file = self.learning_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2)
            temp_file.replace(self.learning_file)
        except Exception as e:
            print(f"Smart Queue: Failed to save learning data: {e}")
    
    def record_interaction(self, item: Dict[str, Any], action: str, context: Dict[str, Any] = None):
        """
        Record user interaction for learning purposes.
        
        Args:
            item: The playlist item
            action: 'play', 'skip', 'complete', etc.
            context: Additional context (time_of_day, session_length, etc.)
        """
        if not self.settings.learning_enabled:
            return
            
        try:
            now = time.time()
            hour = datetime.now().hour
            
            # Record the interaction
            interaction = {
                'timestamp': now,
                'action': action,
                'hour': hour,
                'item_type': item.get('type', 'unknown'),
                'item_source': self._get_source_domain(item.get('url', '')),
                'duration': item.get('duration_seconds', 0),
                'context': context or {}
            }
            
            # Update patterns based on action
            if action == 'skip':
                self.recent_skips.append(interaction)
                self._update_skip_patterns(item, interaction)
            elif action == 'complete':
                self.recent_completions.append(interaction)
                self._update_completion_patterns(item, interaction)
            
            # Cleanup old session data (keep last 50 interactions)
            self.recent_skips = self.recent_skips[-50:]
            self.recent_completions = self.recent_completions[-50:]
            
            # Save periodically
            if len(self.recent_skips) % 5 == 0:
                self._save_learning_data()
                
        except Exception as e:
            print(f"Smart Queue: Error recording interaction: {e}")
    
    def _update_skip_patterns(self, item: Dict[str, Any], interaction: Dict[str, Any]):
        """Update skip rate patterns"""
        item_type = item.get('type', 'unknown')
        source = self._get_source_domain(item.get('url', ''))
        hour = interaction['hour']
        
        # Update skip rates by type and source
        if 'skip_rates' not in self.learning_data:
            self.learning_data['skip_rates'] = {}
            
        for key in [item_type, source, f"hour_{hour}"]:
            if key not in self.learning_data['skip_rates']:
                self.learning_data['skip_rates'][key] = {'skips': 0, 'total': 0}
            self.learning_data['skip_rates'][key]['skips'] += 1
            self.learning_data['skip_rates'][key]['total'] += 1
    
    def _update_completion_patterns(self, item: Dict[str, Any], interaction: Dict[str, Any]):
        """Update completion patterns"""
        item_type = item.get('type', 'unknown')
        source = self._get_source_domain(item.get('url', ''))
        hour = interaction['hour']
        
        # Update completion rates
        if 'completion_rates' not in self.learning_data:
            self.learning_data['completion_rates'] = {}
            
        for key in [item_type, source, f"hour_{hour}"]:
            if key not in self.learning_data['completion_rates']:
                self.learning_data['completion_rates'][key] = {'completions': 0, 'total': 0}
            self.learning_data['completion_rates'][key]['completions'] += 1
            self.learning_data['completion_rates'][key]['total'] += 1
    
    def get_suggestions(self, 
                       current_item: Optional[Dict[str, Any]], 
                       playlist: List[Dict[str, Any]], 
                       current_index: int,
                       upcoming_indices: List[int]) -> List[Tuple[int, str, str]]:
        """
        Get smart queue suggestions.
        
        Args:
            current_item: Currently playing item
            playlist: Full playlist
            current_index: Current playlist index
            upcoming_indices: Already queued upcoming indices
            
        Returns:
            List of (index, reason_icon, reason_text) tuples
        """
        if not self.settings.enabled or not playlist:
            return []
            
        try:
            # Get available items (not already in queue)
            available_indices = [i for i in range(len(playlist)) 
                               if i not in upcoming_indices and i != current_index]
            
            if not available_indices:
                return []
            
            suggestions = []
            
            # Time-aware suggestions
            if self.settings.time_aware:
                suggestions.extend(self._get_time_aware_suggestions(
                    current_item, playlist, available_indices))
            
            # Content similarity suggestions
            if self.settings.content_similarity:
                suggestions.extend(self._get_similarity_suggestions(
                    current_item, playlist, available_indices))
            
            # Pattern-based suggestions
            if self.settings.learning_enabled:
                suggestions.extend(self._get_pattern_suggestions(
                    current_item, playlist, available_indices))
            
            # Remove duplicates and sort by priority/score
            seen = set()
            unique_suggestions = []
            for idx, icon, reason in suggestions:
                if idx not in seen:
                    seen.add(idx)
                    unique_suggestions.append((idx, icon, reason))
            
            # Limit to max_suggestions
            return unique_suggestions[:self.settings.max_suggestions]
            
        except Exception as e:
            print(f"Smart Queue: Error generating suggestions: {e}")
            return []
    
    def _get_time_aware_suggestions(self, 
                                  current_item: Optional[Dict[str, Any]], 
                                  playlist: List[Dict[str, Any]], 
                                  available_indices: List[int]) -> List[Tuple[int, str, str]]:
        """Get time-aware suggestions based on current context"""
        suggestions = []
        hour = datetime.now().hour
        
        try:
            # Determine time context
            if 6 <= hour < 12:
                time_icon = "☀️"
                time_context = "morning"
            elif 12 <= hour < 18:
                time_icon = "🌤️" 
                time_context = "afternoon"
            elif 18 <= hour < 22:
                time_icon = "🌅"
                time_context = "evening"
            else:
                time_icon = "🌙"
                time_context = "night"
            
            # Session length consideration
            session_length = time.time() - self.session_start
            
            for idx in available_indices:
                item = playlist[idx]
                duration = item.get('duration_seconds', 0)
                
                # Short video suggestion for long sessions
                if (session_length > self.settings.long_session_threshold and 
                    duration > 0 and duration < self.settings.short_video_threshold):
                    suggestions.append((idx, "🕒", f"Short video for break"))
                
                # Night time - prefer shorter content
                elif time_context == "night" and duration > 0 and duration < 900:  # 15 min
                    suggestions.append((idx, time_icon, f"Good for {time_context}"))
                
                # Morning - energetic content
                elif time_context == "morning" and len(suggestions) < 2:
                    suggestions.append((idx, time_icon, f"Morning pick"))
                    
        except Exception as e:
            print(f"Smart Queue: Error in time-aware suggestions: {e}")
        
        return suggestions
    
    def _get_similarity_suggestions(self, 
                                  current_item: Optional[Dict[str, Any]], 
                                  playlist: List[Dict[str, Any]], 
                                  available_indices: List[int]) -> List[Tuple[int, str, str]]:
        """Get content similarity suggestions"""
        suggestions = []
        
        if not current_item:
            return suggestions
            
        try:
            current_type = current_item.get('type', 'unknown')
            current_source = self._get_source_domain(current_item.get('url', ''))
            current_duration = current_item.get('duration_seconds', 0)
            
            for idx in available_indices:
                item = playlist[idx]
                similarity_score = 0
                reason_parts = []
                
                # Same content type
                if item.get('type') == current_type:
                    similarity_score += 3
                    reason_parts.append("same type")
                
                # Same source domain  
                if self._get_source_domain(item.get('url', '')) == current_source:
                    similarity_score += 2
                    reason_parts.append("same source")
                
                # Similar duration (within 50%)
                item_duration = item.get('duration_seconds', 0)
                if (current_duration > 0 and item_duration > 0 and
                    abs(current_duration - item_duration) / current_duration < 0.5):
                    similarity_score += 1
                    reason_parts.append("similar length")
                
                # Add if sufficiently similar
                if similarity_score >= 2:
                    reason = f"Similar content ({', '.join(reason_parts)})"
                    suggestions.append((idx, "🎭", reason))
                    
        except Exception as e:
            print(f"Smart Queue: Error in similarity suggestions: {e}")
        
        return suggestions
    
    def _get_pattern_suggestions(self, 
                               current_item: Optional[Dict[str, Any]], 
                               playlist: List[Dict[str, Any]], 
                               available_indices: List[int]) -> List[Tuple[int, str, str]]:
        """Get suggestions based on learned user patterns"""
        suggestions = []
        
        if not self.settings.learning_enabled:
            return suggestions
            
        try:
            # Check if we have enough learning data
            total_interactions = sum(
                data.get('total', 0) 
                for data in self.learning_data.get('completion_rates', {}).values()
            )
            
            if total_interactions < self.settings.min_learning_samples:
                return suggestions
            
            hour = datetime.now().hour
            
            for idx in available_indices:
                item = playlist[idx]
                item_type = item.get('type', 'unknown')
                source = self._get_source_domain(item.get('url', ''))
                
                # Calculate preference score based on historical completion rates
                score = 0
                
                # Type preference
                type_data = self.learning_data.get('completion_rates', {}).get(item_type, {})
                if type_data.get('total', 0) >= 3:  # Minimum samples
                    completion_rate = type_data.get('completions', 0) / type_data.get('total', 1)
                    score += completion_rate * 2
                
                # Source preference
                source_data = self.learning_data.get('completion_rates', {}).get(source, {})
                if source_data.get('total', 0) >= 3:
                    completion_rate = source_data.get('completions', 0) / source_data.get('total', 1)
                    score += completion_rate * 1.5
                
                # Time-of-day preference
                hour_key = f"hour_{hour}"
                hour_data = self.learning_data.get('completion_rates', {}).get(hour_key, {})
                if hour_data.get('total', 0) >= 2:
                    completion_rate = hour_data.get('completions', 0) / hour_data.get('total', 1)
                    score += completion_rate * 1
                
                # Add if score is high enough
                if score >= 1.5:  # Threshold for pattern-based suggestion
                    suggestions.append((idx, "📈", f"Based on your preferences"))
                    
        except Exception as e:
            print(f"Smart Queue: Error in pattern suggestions: {e}")
        
        return suggestions
    
    def _get_source_domain(self, url: str) -> str:
        """Extract domain from URL for source matching"""
        if not url:
            return 'unknown'
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Simplify common domains
            if 'youtube' in domain:
                return 'youtube'
            elif 'bilibili' in domain:
                return 'bilibili'
            elif domain:
                return domain
            else:
                return 'local'
        except Exception:
            return 'unknown'
    
    def update_settings(self, new_settings: SmartQueueSettings):
        """Update smart queue settings"""
        self.settings = new_settings
        if not self.settings.enabled:
            # Clear session data when disabled
            self.recent_skips.clear()
            self.recent_completions.clear()
    
    def reset_learning_data(self):
        """Reset all learning data (for user control)"""
        self.learning_data = {
            'patterns': {},
            'preferences': {},
            'time_patterns': {},
            'skip_rates': {},
            'completion_rates': {},
            'last_updated': time.time()
        }
        self.recent_skips.clear()
        self.recent_completions.clear()
        self._save_learning_data()
        print("Smart Queue: Learning data reset successfully")