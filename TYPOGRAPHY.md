# Typography System Documentation

## Overview

The Typography System provides native (non-monkey-patched) typography management for Silence Suzuka Player with professional baseline sizes, user scaling, and comprehensive hotkey support.

## Features

### Core Functionality
- **Font Loading**: Automatically loads fonts from `assets/fonts` directory (TTF/OTF)
- **QSS Typography**: Applies app-wide typography via CSS-like stylesheets
- **Settings Persistence**: Saves configuration to platform-appropriate directories
- **Live Scaling**: Real-time typography scaling via hotkeys
- **Theme Compatibility**: Works alongside existing vinyl/dark themes

### Professional Baseline Sizes
- Body/List Text: 16px
- Titles: 24px  
- Time Labels: 20px
- Chips: 13px
- Badges: 12px

All sizes are scaled by user preference (default: 1.3x for improved readability).

### Hotkeys
- `Ctrl+=` / `Ctrl++`: Scale up by 0.1
- `Ctrl+-`: Scale down by 0.1
- `Ctrl+0`: Reset to default scale (1.3)
- `Ctrl+,`: Open Typography Preferences dialog

## Implementation

### Files Added
- `ui/typography.py`: Core TypographyManager and TypographySettings
- `ui/preferences_typography.py`: Typography preferences dialog
- `ui/__init__.py`: Module initialization

### Integration
The system is integrated into `silence-suzuka-player.py` main() function:

```python
def main():
    app = QApplication(sys.argv)
    w = MediaPlayer()
    # Initialize typography AFTER the window builds and applies its theme so our QSS lands last
    from ui.typography import TypographyManager
    typo = TypographyManager(app, project_root=APP_DIR)
    typo.install()
    w.show()
    sys.exit(app.exec())
```

### QSS Architecture
The typography system generates two CSS blocks:

1. **FAMILY Block**: Sets font families for QLabel and QAbstractItemView
2. **SIZE Block**: Sets specific font sizes for targeted components

Example generated QSS:
```css
/* Typography Manager - FAMILY Block */
QLabel, QAbstractItemView {
    font-family: "Inter", "Noto Sans JP", sans-serif;
}

/* Typography Manager - SIZE Block */
QLabel {
    font-size: 20px;
}

#titleLabel {
    font-size: 31px;
}

#trackLabel {
    font-size: 31px;
}

#timeLabel, #durLabel, #elapsedLabel, #remainingLabel, #currentTimeLabel, #totalTimeLabel {
    font-size: 26px;
}

#scopeChip {
    font-size: 16px;
}

#statsBadge {
    font-size: 15px;
}
```

### Targeted Components
- `#titleLabel`: Main app title
- `#trackLabel`: Currently playing track
- `#timeLabel`, `#durLabel`, `#elapsedLabel`, `#remainingLabel`: Time displays
- `#currentTimeLabel`, `#totalTimeLabel`: Additional time labels
- `#scopeChip`: Scope indicator chip
- `#statsBadge`: Statistics badge
- `QLabel`: General labels
- `QAbstractItemView`: Lists and trees (playlist, etc.)

## Configuration

### Settings Location
Settings are stored in platform-appropriate locations:
- **Windows**: `%APPDATA%\SilenceSuzukaPlayer\typography.json`
- **macOS**: `~/Library/Application Support/SilenceSuzukaPlayer/typography.json`
- **Linux**: `~/.config/SilenceSuzukaPlayer/typography.json`

### Configuration Format
```json
{
  "latin_family": "Inter",
  "cjk_family": "Noto Sans JP",
  "fallback_generic": "sans-serif",
  "body_size": 16,
  "list_size": 16,
  "title_size": 24,
  "time_size": 20,
  "chip_size": 13,
  "badge_size": 12,
  "scale": 1.3
}
```

## Typography Preferences Dialog

The preferences dialog provides:
- **Font Family Selection**: Separate dropdowns for Latin and CJK fonts
- **Base Size Configuration**: Individual spinboxes for each component type
- **Scale Control**: Live scaling with preview
- **Reset to Defaults**: Restore professional baseline with scale 1.3
- **Apply/OK/Cancel**: Standard dialog behavior with live updates

## Compatibility

### Theme Coexistence
The typography system works alongside existing themes by:
- Appending QSS rules to the application stylesheet (CSS cascade ensures precedence)
- Targeting specific selectors without affecting theme colors, margins, etc.
- Using font-family stacks that complement loaded theme fonts

### Font Loading
- Reuses the existing `assets/fonts` directory structure
- Provides fallbacks to system fonts if bundled fonts aren't available
- Prioritizes common fonts (Inter, Roboto, Noto families) in font picker

### Forward/Backward Compatibility
- Configuration format supports adding new fields without breaking existing installs
- Missing configuration fields automatically use sensible defaults
- Extra fields in configuration files are safely ignored

## Testing

Comprehensive test suite validates:
- ✅ Core dataclass serialization/deserialization
- ✅ QSS generation with proper scaling
- ✅ Platform-specific configuration directories
- ✅ Integration with existing app stylesheets
- ✅ Component targeting and CSS cascade behavior
- ✅ Complete user workflow simulation
- ✅ Requirements compliance

## Usage Examples

### Basic Usage
The system works automatically once integrated. Users can:
1. Use hotkeys to adjust scale in real-time
2. Open preferences (Ctrl+,) to customize fonts and sizes
3. Settings persist across app restarts

### Programmatic Access
```python
from ui.typography import TypographyManager, TypographySettings

# Create manager
manager = TypographyManager(app, project_root=Path("/app/root"))

# Install system
manager.install()

# Update settings programmatically
new_settings = TypographySettings(scale=1.5, latin_family="Arial")
manager.update_settings(new_settings)
```

## Performance

- Minimal overhead: QSS generation only occurs when settings change
- Font loading happens once at startup
- Event filtering is efficient (only processes keyboard events)
- Configuration I/O is only triggered by user actions or app startup/shutdown