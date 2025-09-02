cat > button_animations.py << 'EOL'
"""
Button animation effects for Silence Suzuka Player
Provides tactile feedback through subtle animations.
"""

from PySide6.QtCore import (
    QPropertyAnimation, QEasingCurve, QRect, 
    Property, QPoint, QTimer, Qt
)
from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor, QPainter, QBrush, QPen


class BounceAnimationMixin:
    """Mixin class that adds a bounce animation effect to buttons on click."""
    
    def setup_bounce_animation(self, distance=2, duration=150):
        """
        Set up the bounce animation for a button.
        
        Args:
            distance: How far the button should "push down" in pixels
            duration: Animation duration in milliseconds
        """
        self._orig_pos = self.pos()
        self._bounce_distance = distance
        self._bounce_duration = duration
        self._bounce_animation = QPropertyAnimation(self, b"pos")
        self._bounce_animation.setEasingCurve(QEasingCurve.OutBounce)
        self._bounce_animation.setDuration(self._bounce_duration)
        
        # Store the original clicked handler if it exists
        if hasattr(self, "clicked"):
            self._original_clicked_handlers = self.clicked.callbacks
            # Disconnect all handlers temporarily
            try:
                self.clicked.disconnect()
            except RuntimeError:
                pass
            
            # Reconnect the original handlers
            for callback in self._original_clicked_handlers:
                self.clicked.connect(callback)
                
        # Add our bounce effect as the first handler
        self.clicked.connect(self._trigger_bounce)
    
    def _trigger_bounce(self):
        """Trigger the bounce animation when button is clicked."""
        # Only animate if not already animating
        if self._bounce_animation.state() == QPropertyAnimation.Running:
            return
            
        # Calculate down and up positions
        down_pos = self._orig_pos + QPoint(0, self._bounce_distance)
        
        # Update starting position in case the button has moved in the layout
        self._orig_pos = self.pos()
        
        # Set up the animation values
        self._bounce_animation.setStartValue(self.pos())
        self._bounce_animation.setKeyValueAt(0.3, down_pos)  # Push down first
        self._bounce_animation.setEndValue(self._orig_pos)   # Return to original
        
        # Start the animation
        self._bounce_animation.start()


class BouncePushButton(QPushButton, BounceAnimationMixin):
    """QPushButton with built-in bounce animation effect."""
    
    def __init__(self, *args, **kwargs):
        bounce_distance = kwargs.pop("bounce_distance", 2) 
        bounce_duration = kwargs.pop("bounce_duration", 150)
        
        super().__init__(*args, **kwargs)
        self._orig_pos = self.pos()
        self.setup_bounce_animation(bounce_distance, bounce_duration)


def apply_bounce_to_button(button, distance=2, duration=150):
    """
    Apply bounce animation to an existing button.
    
    Args:
        button: The QPushButton to enhance
        distance: How far the button should "push down" in pixels
        duration: Animation duration in milliseconds
    """
    # Add the mixin methods to the button instance
    button.__class__ = type(
        'EnhancedButton', 
        (button.__class__, BounceAnimationMixin), 
        {}
    )
    # Initialize the animation
    button.setup_bounce_animation(distance, duration)
    return button


def enhance_player_controls(player):
    """
    Apply bounce animations to the player's control buttons.
    
    Args:
        player: The MediaPlayer instance
    """
    # Enhance main player control buttons
    buttons = []
    
    # Try to find the common control buttons
    for btn_name in ['play_pause_btn', 'shuffle_btn', 'repeat_btn', 'prev_btn', 'next_btn']:
        if hasattr(player, btn_name) and getattr(player, btn_name) is not None:
            buttons.append(getattr(player, btn_name))
    
    # Apply animations with appropriate settings for each button
    for button in buttons:
        if hasattr(player, 'play_pause_btn') and button == player.play_pause_btn:
            # Main play button gets slightly stronger effect
            apply_bounce_to_button(button, distance=3, duration=180)
        else:
            # Standard effect for other buttons
            apply_bounce_to_button(button, distance=2, duration=150)
    
    return buttons
EOL