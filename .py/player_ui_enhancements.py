cat > player_ui_enhancements.py << 'EOL'
"""
Integration module to apply UI enhancements to Silence Suzuka Player
"""

from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QLabel, QFormLayout, QWidget
)
from button_animations import enhance_player_controls
from video_styling import enhance_video_area, VideoStyler


def apply_ui_enhancements(player):
    """
    Apply all UI enhancements to the player.
    
    Args:
        player: The MediaPlayer instance
    """
    # Add configuration variables to the player
    player.button_animations_enabled = getattr(player, 'button_animations_enabled', True)
    player.video_style = getattr(player, 'video_style', VideoStyler.STYLE_INTEGRATED)
    
    # Apply the enhancements
    if player.button_animations_enabled:
        enhanced_buttons = enhance_player_controls(player)
    
    # Apply video styling
    player.video_styler = enhance_video_area(player, player.video_style)
    
    # Add settings options if the player has a settings dialog
    if hasattr(player, 'open_settings_tabs'):
        _add_settings_options(player)
    
    return player


def _add_settings_options(player):
    """
    Add UI enhancement options to the settings dialog.
    
    Args:
        player: The MediaPlayer instance
    """
    # Check if open_settings_tabs exists and is callable
    if not hasattr(player, 'open_settings_tabs') or not callable(player.open_settings_tabs):
        return
    
    # Store original open_settings method to extend it
    original_open_settings = player.open_settings_tabs
    
    def extended_open_settings():
        """Extended version of the settings dialog that includes UI enhancement options."""
        # Call the original implementation first
        dlg, tabs = original_open_settings()
        
        # Add UI enhancements tab
        w_ui_enhance = QWidget()
        f_ui_enhance = QFormLayout(w_ui_enhance)
        
        # Button animations toggle
        chk_button_anim = QCheckBox()
        chk_button_anim.setChecked(player.button_animations_enabled)
        f_ui_enhance.addRow("Button animations:", chk_button_anim)
        
        # Video styling dropdown
        cmb_video_style = QComboBox()
        cmb_video_style.addItem("Classic", VideoStyler.STYLE_CLASSIC)
        cmb_video_style.addItem("Integrated Corner", VideoStyler.STYLE_INTEGRATED)
        
        # Set current selection based on player's setting
        index = cmb_video_style.findData(player.video_style)
        if index >= 0:
            cmb_video_style.setCurrentIndex(index)
            
        f_ui_enhance.addRow("Video area style:", cmb_video_style)
        
        # Preview label explaining the options
        label_preview = QLabel("Changes will apply after clicking OK")
        label_preview.setWordWrap(True)
        f_ui_enhance.addRow(label_preview)
        
        # Add the tab
        tabs.addTab(w_ui_enhance, "UI Enhancements")
        
        # Find the apply button or function if it exists
        apply_widget = None
        if hasattr(dlg, 'findChild'):
            apply_widget = dlg.findChild(QWidget, "_apply_func")
        
        if apply_widget and hasattr(apply_widget, 'apply'):
            # Store original apply function
            original_apply = apply_widget.apply
            
            def extended_apply():
                # Call original apply function
                original_apply()
                
                # Save our additional settings
                player.button_animations_enabled = chk_button_anim.isChecked()
                player.video_style = cmb_video_style.currentData()
                
                # Apply the changes immediately
                if player.button_animations_enabled:
                    enhance_player_controls(player)
                
                if player.video_styler:
                    player.video_styler.apply_style(player.video_style)
                
                # Save the settings if the method exists
                if hasattr(player, '_save_settings') and callable(player._save_settings):
                    try:
                        player._save_settings()
                    except Exception:
                        pass
                    
            # Replace the apply function
            apply_widget.apply = extended_apply
        
        return dlg, tabs
    
    # Replace the open_settings method
    player.open_settings_tabs = extended_open_settings
EOL