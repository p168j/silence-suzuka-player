#!/usr/bin/env python3
"""
Typography Preferences Dialog for Silence Suzuka Player

Simple modal dialog for configuring typography settings:
- Font family dropdowns (Latin + CJK)
- Base size spinboxes
- Scale control
- Apply/OK/Cancel/Reset buttons
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QDialogButtonBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt

from .typography import TypographySettings, TypographyManager


class TypographyPreferencesDialog(QDialog):
    """Typography preferences configuration dialog"""
    
    def __init__(self, typography_manager: TypographyManager, parent=None):
        super().__init__(parent)
        self.typography_manager = typography_manager
        self.original_settings = typography_manager.settings
        
        self.setWindowTitle("Typography Preferences")
        self.setModal(True)
        self.resize(480, 400)
        
        self._build_ui()
        self._load_current_settings()
        
    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        
        # Font Family Section
        font_group = QGroupBox("Font Families")
        font_layout = QFormLayout(font_group)
        
        # Latin font dropdown
        self.latin_font_combo = QComboBox()
        self.latin_font_combo.setEditable(True)
        self._populate_font_combo(self.latin_font_combo)
        font_layout.addRow("Latin Font:", self.latin_font_combo)
        
        # CJK font dropdown  
        self.cjk_font_combo = QComboBox()
        self.cjk_font_combo.setEditable(True)
        self._populate_font_combo(self.cjk_font_combo, prioritize_cjk=True)
        font_layout.addRow("CJK Font:", self.cjk_font_combo)
        
        layout.addWidget(font_group)
        
        # Base Sizes Section
        sizes_group = QGroupBox("Base Font Sizes")
        sizes_layout = QFormLayout(sizes_group)
        
        self.body_size_spin = QSpinBox()
        self.body_size_spin.setRange(8, 48)
        self.body_size_spin.setSuffix("px")
        sizes_layout.addRow("Body Text:", self.body_size_spin)
        
        self.list_size_spin = QSpinBox()
        self.list_size_spin.setRange(8, 48)
        self.list_size_spin.setSuffix("px")
        sizes_layout.addRow("List Items:", self.list_size_spin)
        
        self.title_size_spin = QSpinBox()
        self.title_size_spin.setRange(12, 72)
        self.title_size_spin.setSuffix("px")
        sizes_layout.addRow("Titles:", self.title_size_spin)
        
        self.time_size_spin = QSpinBox()
        self.time_size_spin.setRange(10, 48)
        self.time_size_spin.setSuffix("px")
        sizes_layout.addRow("Time Labels:", self.time_size_spin)
        
        self.chip_size_spin = QSpinBox()
        self.chip_size_spin.setRange(8, 24)
        self.chip_size_spin.setSuffix("px")
        sizes_layout.addRow("Chips:", self.chip_size_spin)
        
        self.badge_size_spin = QSpinBox()
        self.badge_size_spin.setRange(8, 24)
        self.badge_size_spin.setSuffix("px")
        sizes_layout.addRow("Badges:", self.badge_size_spin)
        
        layout.addWidget(sizes_group)
        
        # Scale Section
        scale_group = QGroupBox("Scale Factor")
        scale_layout = QFormLayout(scale_group)
        
        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.5, 3.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setDecimals(2)
        self.scale_spin.valueChanged.connect(self._on_scale_changed)
        scale_layout.addRow("Scale:", self.scale_spin)
        
        # Scale info label
        self.scale_info_label = QLabel()
        self.scale_info_label.setWordWrap(True)
        self.scale_info_label.setStyleSheet("color: #666; font-size: 11px;")
        scale_layout.addRow("", self.scale_info_label)
        
        layout.addWidget(scale_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Reset button (left side)
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        # Standard buttons (right side)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        self.button_box.accepted.connect(self._accept)
        self.button_box.rejected.connect(self._reject)
        
        button_layout.addWidget(self.button_box)
        
        layout.addLayout(button_layout)
        
    def _populate_font_combo(self, combo: QComboBox, prioritize_cjk: bool = False):
        """Populate font combo with available fonts"""
        try:
            fonts = self.typography_manager.get_available_fonts()
            
            if prioritize_cjk:
                # For CJK, prioritize fonts that support CJK characters
                cjk_fonts = [
                    "Noto Sans JP", "Noto Sans CJK JP", "Yu Gothic UI", 
                    "Meiryo UI", "MS Gothic", "SimSun", "Noto Sans"
                ]
                
                prioritized = []
                remaining = []
                
                for font in fonts:
                    if any(cjk in font for cjk in ["Noto", "Yu", "Meiryo", "Gothic", "Sans"]):
                        prioritized.append(font)
                    else:
                        remaining.append(font)
                        
                combo.addItems(prioritized + remaining)
            else:
                combo.addItems(fonts)
                
        except Exception as e:
            print(f"Failed to populate font combo: {e}")
            # Fallback fonts
            combo.addItems(["Inter", "Arial", "Helvetica", "sans-serif"])
            
    def _load_current_settings(self):
        """Load current settings into the UI"""
        settings = self.typography_manager.settings
        
        # Set font combos
        self._set_combo_text(self.latin_font_combo, settings.latin_family)
        self._set_combo_text(self.cjk_font_combo, settings.cjk_family)
        
        # Set base sizes
        self.body_size_spin.setValue(settings.body_size)
        self.list_size_spin.setValue(settings.list_size)
        self.title_size_spin.setValue(settings.title_size)
        self.time_size_spin.setValue(settings.time_size)
        self.chip_size_spin.setValue(settings.chip_size)
        self.badge_size_spin.setValue(settings.badge_size)
        
        # Set scale
        self.scale_spin.setValue(settings.scale)
        self._update_scale_info()
        
    def _set_combo_text(self, combo: QComboBox, text: str):
        """Set combo box text, adding it if not found"""
        index = combo.findText(text)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            # Add the text and select it
            combo.addItem(text)
            combo.setCurrentText(text)
            
    def _on_scale_changed(self):
        """Handle scale value changes"""
        self._update_scale_info()
        
    def _update_scale_info(self):
        """Update scale information label"""
        scale = self.scale_spin.value()
        body_scaled = int(16 * scale)  # Using baseline body size of 16
        title_scaled = int(24 * scale)  # Using baseline title size of 24
        
        info_text = f"Preview: Body {body_scaled}px, Title {title_scaled}px"
        self.scale_info_label.setText(info_text)
        
    def _get_current_settings(self) -> TypographySettings:
        """Get settings from current UI state"""
        return TypographySettings(
            latin_family=self.latin_font_combo.currentText(),
            cjk_family=self.cjk_font_combo.currentText(),
            fallback_generic="sans-serif",  # Keep constant
            body_size=self.body_size_spin.value(),
            list_size=self.list_size_spin.value(),
            title_size=self.title_size_spin.value(),
            time_size=self.time_size_spin.value(),
            chip_size=self.chip_size_spin.value(),
            badge_size=self.badge_size_spin.value(),
            scale=self.scale_spin.value()
        )
        
    def _apply_settings(self):
        """Apply current settings immediately"""
        new_settings = self._get_current_settings()
        self.typography_manager.update_settings(new_settings)
        
    def _reset_to_defaults(self):
        """Reset all settings to professional defaults with scale 1.3"""
        defaults = TypographySettings()  # Uses defaults from dataclass
        
        # Load defaults into UI
        self._set_combo_text(self.latin_font_combo, defaults.latin_family)
        self._set_combo_text(self.cjk_font_combo, defaults.cjk_family)
        
        self.body_size_spin.setValue(defaults.body_size)
        self.list_size_spin.setValue(defaults.list_size)
        self.title_size_spin.setValue(defaults.title_size)
        self.time_size_spin.setValue(defaults.time_size)
        self.chip_size_spin.setValue(defaults.chip_size)
        self.badge_size_spin.setValue(defaults.badge_size)
        
        self.scale_spin.setValue(defaults.scale)
        self._update_scale_info()
        
    def _accept(self):
        """Apply settings and close dialog"""
        self._apply_settings()
        self.accept()
        
    def _reject(self):
        """Cancel changes and close dialog"""
        # Restore original settings
        self.typography_manager.update_settings(self.original_settings)
        self.reject()