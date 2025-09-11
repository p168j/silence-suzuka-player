# Intelligent Error Handling System

The Silence Suzuka Player now includes an intelligent error handling system that prevents error cascades and provides graceful degradation when media fails to play.

## Features

### Error Classification
The system automatically classifies errors into different types:

- **Network Errors** (🌐): Connection timeouts, DNS failures, SSL errors - retried with exponential backoff
- **Media Not Found** (❌): File not found, 404 errors, unavailable videos - skipped after brief pause  
- **Authentication Errors** (🔐): Login required, forbidden access, private content - requires user intervention
- **System Errors** (⚙️): Format not supported, codec issues, MPV failures - retried with different settings
- **Unknown Errors** (❓): Unclassified errors - conservative retry approach

### Circuit Breaker Pattern
After **3 consecutive failures** (configurable), the system automatically:
- Pauses auto-advance for **60 seconds** (configurable)
- Shows warning in the UI with countdown
- Allows manual controls to continue playback
- Automatically resumes when timeout expires or user manually resets

### Exponential Backoff
Retry attempts use progressive delays:
- 1st retry: **1 second**
- 2nd retry: **2 seconds** 
- 3rd retry: **4 seconds**
- Maximum: **30 seconds**

### Error Status Indicator
A dynamic button appears in the control bar showing current error state:

- 🚨 **Red**: Circuit breaker active (auto-advance paused)
- ⚠️ **Orange**: Recent consecutive failures  
- ℹ️ **Yellow**: Some errors occurred but not critical
- **Hidden**: No recent errors

Click the button to reset error handling state and resume auto-advance.

## Configuration

### Settings Location
Error handling settings are saved in `config.json` under the `error_handling` section.

### Configurable Options

#### Core Settings
- `enabled`: Enable/disable intelligent error handling (default: true)
- `max_consecutive_failures`: Circuit breaker threshold (default: 3)
- `circuit_breaker_timeout`: Pause duration in seconds (default: 60)

#### Backoff Settings  
- `initial_backoff_delay`: Starting retry delay (default: 1.0s)
- `backoff_multiplier`: Delay increase factor (default: 2.0)
- `max_backoff_delay`: Maximum retry delay (default: 30.0s)

#### Retry Limits by Error Type
- `max_retries_network`: Network errors (default: 3)
- `max_retries_system`: System/MPV errors (default: 2) 
- `max_retries_auth`: Authentication errors (default: 0)
- `max_retries_media_not_found`: Permanent errors (default: 0)

#### User Experience
- `show_error_notifications`: Display error messages (default: true)
- `auto_skip_permanent_errors`: Skip permanent failures after pause (default: true)
- `pause_on_network_offline`: Pause when network unavailable (default: true)

## Usage Examples

### Manual Reset
When the circuit breaker is active:
1. Click the red 🚨 button in the control bar, OR
2. Wait for the timeout to expire (shown in status message)

### Retry Failed Item
When an item fails to play:
1. The system automatically retries based on error type
2. Use Previous/Next buttons to manually control playback
3. Click error status button to reset retry counters

### Network Issues
When offline or having connection problems:
1. System detects network status automatically
2. Pauses auto-advance for online content
3. Shows appropriate error messages
4. Resumes when connectivity returns

## Error Recovery Scenarios

### Scenario 1: Single Item Failure
```
Error: "Video format not supported"
→ Classification: System Error
→ Action: Retry once, then skip with 2s pause
→ Status: Brief notification, continue playback
```

### Scenario 2: Network Timeout
```
Error: "Connection timeout"
→ Classification: Network Error  
→ Action: Retry with 1s → 2s → 4s delays
→ Status: Show retry progress, eventually skip
```

### Scenario 3: Consecutive Failures
```
3 errors in a row
→ Circuit Breaker: Activated
→ Action: Pause auto-advance for 60s
→ Status: Red 🚨 button, warning message
→ Recovery: Manual reset or wait for timeout
```

### Scenario 4: Network Offline
```
Network check fails for online URLs
→ Classification: Network Error (offline)
→ Action: Pause auto-advance, show offline message  
→ Status: Resume when connectivity detected
```

## Implementation Details

### Error Handler Class
```python
class PlaybackErrorHandler:
    def classify_error(self, error_message: str, url: str) -> ErrorType
    def should_retry(self, playlist_index: int, error_type: ErrorType) -> Tuple[bool, float]
    def record_error(self, error_message: str, playlist_index: int, url: str) -> ErrorEvent
    def record_success(self, playlist_index: int)
    def is_circuit_breaker_active(self) -> bool
```

### Integration Points
- **MPV Error Handler**: `_show_mpv_error()` method enhanced with intelligent logic
- **Next Track Logic**: `next_track()` respects circuit breaker state
- **Settings System**: Error handling settings saved/loaded with other preferences  
- **UI Updates**: Error status button and notifications integrated into existing interface

## Troubleshooting

### Error Handling Not Working
1. Check that `enabled` is `true` in settings
2. Verify error classification is working (check console output)
3. Reset error handling state using the UI button

### Too Aggressive Retrying
1. Reduce `max_retries_*` values for specific error types
2. Increase `initial_backoff_delay` for longer waits between retries
3. Decrease `max_consecutive_failures` to activate circuit breaker sooner

### Circuit Breaker Activating Too Often
1. Increase `max_consecutive_failures` threshold
2. Adjust retry limits to handle more errors before circuit breaker
3. Check for underlying network or media library issues

### Performance Impact
The error handling system is designed to have minimal overhead:
- Error classification uses simple string matching
- Network checks are throttled (max once per 30 seconds)
- Error history is limited and cleaned up automatically
- All operations are non-blocking and asynchronous where possible