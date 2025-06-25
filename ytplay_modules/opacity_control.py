"""
Opacity control for text source fade effects.
Manages smooth fade in/out transitions for title display.
"""

import obspython as obs
from config import TITLE_FADE_DURATION, TITLE_FADE_STEPS, TITLE_FADE_INTERVAL, OPACITY_FILTER_NAME, TEXT_SOURCE_NAME
from logger import log

# Module-level variables
_opacity_timer = None
_current_opacity = 100.0
_target_opacity = 100.0
_opacity_step = 0.0
_fade_direction = None  # 'in' or 'out'
_pending_text = None
_opacity_filter_created = False


def ensure_opacity_filter():
    """Ensure the opacity filter exists on the text source."""
    global _opacity_filter_created
    
    if _opacity_filter_created:
        return True
    
    # Get the text source
    text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
    if not text_source:
        return False
    
    # Check if filter already exists
    existing_filter = obs.obs_source_get_filter_by_name(text_source, OPACITY_FILTER_NAME)
    if existing_filter:
        obs.obs_source_release(existing_filter)
        obs.obs_source_release(text_source)
        _opacity_filter_created = True
        return True
    
    # Create color correction filter for opacity control
    filter_settings = obs.obs_data_create()
    obs.obs_data_set_int(filter_settings, "opacity", 100)
    
    opacity_filter = obs.obs_source_create_private(
        "color_filter", 
        OPACITY_FILTER_NAME, 
        filter_settings
    )
    
    if opacity_filter:
        obs.obs_source_filter_add(text_source, opacity_filter)
        obs.obs_source_release(opacity_filter)
        _opacity_filter_created = True
        log(f"Created opacity filter for text source")
    
    obs.obs_data_release(filter_settings)
    obs.obs_source_release(text_source)
    
    return _opacity_filter_created


def update_text_opacity(opacity):
    """Update the opacity of the text source using color filter."""
    try:
        # Get the text source
        text_source = obs.obs_get_source_by_name(TEXT_SOURCE_NAME)
        if not text_source:
            return
        
        # Get the opacity filter
        opacity_filter = obs.obs_source_get_filter_by_name(text_source, OPACITY_FILTER_NAME)
        if not opacity_filter:
            obs.obs_source_release(text_source)
            # Try to create the filter
            if ensure_opacity_filter():
                # Try again
                opacity_filter = obs.obs_source_get_filter_by_name(text_source, OPACITY_FILTER_NAME)
                if not opacity_filter:
                    return
            else:
                return
        
        # Update the opacity value
        filter_settings = obs.obs_source_get_settings(opacity_filter)
        obs.obs_data_set_int(filter_settings, "opacity", int(opacity))
        obs.obs_source_update(opacity_filter, filter_settings)
        
        # Clean up
        obs.obs_data_release(filter_settings)
        obs.obs_source_release(opacity_filter)
        obs.obs_source_release(text_source)
        
    except Exception as e:
        log(f"ERROR updating text opacity: {e}")


def opacity_transition_callback():
    """Callback for opacity transition timer."""
    global _opacity_timer, _current_opacity, _target_opacity, _opacity_step, _fade_direction, _pending_text
    
    # Update current opacity
    _current_opacity += _opacity_step
    
    # Clamp opacity to valid range
    if _fade_direction == 'in':
        _current_opacity = min(_current_opacity, _target_opacity)
    else:
        _current_opacity = max(_current_opacity, _target_opacity)
    
    # Update the actual opacity
    update_text_opacity(_current_opacity)
    
    # Check if we've reached the target
    if abs(_current_opacity - _target_opacity) < 0.1:
        # Remove timer
        if _opacity_timer:
            obs.timer_remove(_opacity_timer)
            _opacity_timer = None
        
        _current_opacity = _target_opacity
        update_text_opacity(_current_opacity)
        
        # If fading out and reached 0, update the text
        if _fade_direction == 'out' and _current_opacity == 0 and _pending_text is not None:
            # Import here to avoid circular dependency
            from media_control import update_text_source_content
            update_text_source_content(_pending_text['song'], _pending_text['artist'], _pending_text.get('gemini_failed', False))
            _pending_text = None
            # Now fade in
            fade_in_text()
        
        log(f"Title fade {_fade_direction} complete (opacity: {_current_opacity}%)")


def start_opacity_transition(target, direction):
    """Start an opacity transition."""
    global _opacity_timer, _target_opacity, _opacity_step, _fade_direction, _current_opacity
    
    # Cancel any existing transition
    if _opacity_timer:
        obs.timer_remove(_opacity_timer)
        _opacity_timer = None
    
    _target_opacity = target
    _fade_direction = direction
    
    # Calculate step size
    opacity_range = abs(_target_opacity - _current_opacity)
    if opacity_range > 0:
        _opacity_step = opacity_range / TITLE_FADE_STEPS
        if direction == 'out':
            _opacity_step = -_opacity_step
        
        # Start the timer
        _opacity_timer = opacity_transition_callback
        obs.timer_add(_opacity_timer, TITLE_FADE_INTERVAL)
        log(f"Starting title fade {direction} (current: {_current_opacity}% -> target: {_target_opacity}%)")


def fade_in_text():
    """Fade in the text source."""
    start_opacity_transition(100.0, 'in')


def fade_out_text():
    """Fade out the text source."""
    global _current_opacity
    # Don't start a new fade if we're already at 0 or fading out
    if _current_opacity <= 0 or (_fade_direction == 'out' and _opacity_timer is not None):
        return
    start_opacity_transition(0.0, 'out')


def cancel_opacity_timer():
    """Cancel any pending opacity timer."""
    global _opacity_timer
    if _opacity_timer:
        obs.timer_remove(_opacity_timer)
        _opacity_timer = None


def get_current_opacity():
    """Get current opacity value."""
    return _current_opacity


def set_current_opacity(opacity):
    """Set current opacity value."""
    global _current_opacity
    _current_opacity = opacity
    update_text_opacity(_current_opacity)


def set_pending_text(text_info):
    """Set pending text for after fade out."""
    global _pending_text
    _pending_text = text_info


def is_fading():
    """Check if currently fading."""
    return _opacity_timer is not None
