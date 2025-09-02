cat > video_styling.py << 'EOL'
"""
Enhanced video area styling for Silence Suzuka Player
Implements the "Integrated Corner Embed" design.
"""

from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect, QVBoxLayout, QLabel
from PySide6.QtGui import QColor, QPalette, QBrush, QLinearGradient, QFont
from PySide6.QtCore import Qt, QRect, QSize


class VideoStyler:
    """Class to handle video area styling options."""
    
    # Style constants
    STYLE_CLASSIC = "classic"  # Original black rectangle
    STYLE_INTEGRATED = "integrated"  # Option B: Integrated corner
    
    def __init__(self, player):
        """
        Initialize the video styler.
        
        Args:
            player: The MediaPlayer instance
        """
        self.player = player
        self._current_style = self.STYLE_CLASSIC
        self._shadow_effect = None
        
    def apply_style(self, style_name=None):
        """
        Apply a specific video area style.
        
        Args:
            style_name: Name of the style to apply (None to use current style)
        """
        if style_name is not None:
            self._current_style = style_name
            
        # Remove any existing effects first
        self._cleanup_effects()
        
        # Apply the selected style
        if self._current_style == self.STYLE_INTEGRATED:
            self._apply_integrated_style()
        else:
            self._apply_classic_style()
            
    def _cleanup_effects(self):
        """Remove any existing effects from the video frame."""
        if hasattr(self.player, 'video_frame'):
            self.player.video_frame.setGraphicsEffect(None)
            self._shadow_effect = None
            
    def _apply_classic_style(self):
        """Apply the classic (original) styling."""
        if hasattr(self.player, 'video_frame'):
            # Simple black background with no special effects
            self.player.video_frame.setStyleSheet("background-color: #000000;")
            
    def _apply_integrated_style(self):
        """Apply the integrated corner embed styling (Option B)."""
        if hasattr(self.player, 'video_frame'):
            # Get theme from player
            theme = getattr(self.player, 'theme', 'dark')
            
            if theme == 'vinyl':
                # Vinyl theme styling
                border_color = "#c2a882"
                bg_color = "#000000"
                shadow_color = QColor(0, 0, 0, 110)
                
                style = f"""
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                """
            else:
                # Dark theme styling
                border_color = "#2e2e2e"
                bg_color = "#000000"
                shadow_color = QColor(0, 0, 0, 160)
                
                style = f"""
                    background-color: {bg_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                """
            
            self.player.video_frame.setStyleSheet(style)
            
            # Add shadow effect
            self._shadow_effect = QGraphicsDropShadowEffect(self.player.video_frame)
            self._shadow_effect.setBlurRadius(15)
            self._shadow_effect.setOffset(0, 0)
            self._shadow_effect.setColor(shadow_color)
            self.player.video_frame.setGraphicsEffect(self._shadow_effect)


def enhance_video_area(player, style=VideoStyler.STYLE_INTEGRATED):
    """
    Apply enhanced styling to the player's video area.
    
    Args:
        player: The MediaPlayer instance
        style: The styling to apply (VideoStyler.STYLE_CLASSIC or VideoStyler.STYLE_INTEGRATED)
    
    Returns:
        VideoStyler instance
    """
    styler = VideoStyler(player)
    styler.apply_style(style)
    return styler
EOL