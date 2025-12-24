"""Title display management.
Handles scheduling and timing of title show/hide operations.
"""

import obspython as obs

from .logger import log

# Title timing constants (in seconds)
TITLE_CLEAR_BEFORE_END = 3.5  # Clear title 3.5 seconds before song ends
TITLE_SHOW_AFTER_START = 1.5  # Show title 1.5 seconds after song starts
SEEK_THRESHOLD = 5000  # 5 seconds - consider it a seek if position jumps by more than this

# Module-level variables
_title_clear_timer = None
_title_show_timer = None
_pending_title_info = None
_title_clear_scheduled = False  # Track if title clear is already scheduled
_duration_check_timer = None  # Timer for delayed duration check


def clear_title_before_end_callback():
    """Callback to clear title before song ends."""
    global _title_clear_timer, _title_clear_scheduled
    # Remove the timer to prevent it from firing again
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None
    _title_clear_scheduled = False
    log("Fading out title before song end")

    # Import here to avoid circular dependency
    from .opacity_control import fade_out_text
    fade_out_text()


def show_title_after_start_callback():
    """Callback to show title after song starts."""
    global _title_show_timer, _pending_title_info
    # Remove the timer to prevent it from firing again
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None

    if _pending_title_info:
        song = _pending_title_info.get('song', 'Unknown Song')
        artist = _pending_title_info.get('artist', 'Unknown Artist')
        gemini_failed = _pending_title_info.get('gemini_failed', False)
        log(f"Showing title after delay: {song} - {artist}")

        # Import here to avoid circular dependency
        from .media_control import update_text_source_content
        from .opacity_control import fade_in_text

        update_text_source_content(song, artist, gemini_failed)
        fade_in_text()
        _pending_title_info = None


def cancel_title_timers():
    """Cancel any pending title timers."""
    global _title_clear_timer, _title_show_timer, _pending_title_info, _title_clear_scheduled
    global _duration_check_timer

    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None

    if _title_show_timer:
        obs.timer_remove(_title_show_timer)
        _title_show_timer = None

    if _duration_check_timer:
        obs.timer_remove(_duration_check_timer)
        _duration_check_timer = None

    _pending_title_info = None
    _title_clear_scheduled = False


def schedule_title_clear(duration_ms):
    """Schedule clearing of title before song ends."""
    global _title_clear_timer, _title_clear_scheduled

    # Cancel any existing timer
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)

    # Calculate when to clear (duration - 3.5 seconds)
    clear_time_ms = duration_ms - (TITLE_CLEAR_BEFORE_END * 1000)

    if clear_time_ms > 0:
        # Schedule the clear
        _title_clear_timer = clear_title_before_end_callback
        obs.timer_add(_title_clear_timer, int(clear_time_ms))
        _title_clear_scheduled = True
        log(f"Scheduled title fade out in {clear_time_ms/1000:.1f} seconds")


def schedule_title_show(video_info):
    """Schedule showing of title after song starts."""
    global _title_show_timer, _pending_title_info

    # Cancel any existing timer
    if _title_show_timer:
        obs.timer_remove(_title_show_timer)

    # Store the title info for later
    _pending_title_info = video_info

    # Import here to avoid circular dependency
    from .media_control import update_text_source_content
    from .opacity_control import set_current_opacity, update_text_opacity

    # Set opacity to 0 immediately (no fade needed as it's a new video)
    set_current_opacity(0.0)
    update_text_opacity(0.0)

    # Clear text immediately
    update_text_source_content("", "", False)

    # Schedule the show
    _title_show_timer = show_title_after_start_callback
    obs.timer_add(_title_show_timer, int(TITLE_SHOW_AFTER_START * 1000))
    log(f"Scheduled title show in {TITLE_SHOW_AFTER_START} seconds")


def schedule_title_clear_from_current(remaining_ms):
    """Schedule title clear based on remaining time."""
    global _title_clear_timer, _title_clear_scheduled

    # Cancel any existing timer
    if _title_clear_timer:
        obs.timer_remove(_title_clear_timer)
        _title_clear_timer = None

    # Calculate when to clear
    clear_in_ms = remaining_ms - (TITLE_CLEAR_BEFORE_END * 1000)

    if clear_in_ms > 0:
        _title_clear_timer = clear_title_before_end_callback
        obs.timer_add(_title_clear_timer, int(clear_in_ms))
        _title_clear_scheduled = True
        log(f"Scheduled title fade out in {clear_in_ms/1000:.1f} seconds (remaining: {remaining_ms/1000:.1f}s)")
    else:
        # Import here to avoid circular dependency
        from .opacity_control import fade_out_text, get_current_opacity

        if get_current_opacity() > 0:
            # Should fade out immediately
            log("Time to fade out has passed, fading immediately")
            _title_clear_scheduled = False  # Don't schedule, just do it
            fade_out_text()


def delayed_duration_check_callback():
    """Callback that runs once to check duration and schedule title clear."""
    global _duration_check_timer

    # Remove the timer reference so it doesn't get called again
    if _duration_check_timer:
        obs.timer_remove(_duration_check_timer)
        _duration_check_timer = None

    # Import here to avoid circular dependency
    from .config import MEDIA_SOURCE_NAME
    from .media_control import get_media_duration

    duration = get_media_duration(MEDIA_SOURCE_NAME)
    if duration > 0:
        schedule_title_clear(duration)
        log(f"Got duration after delay: {duration/1000:.1f}s")
    else:
        # Try again after another delay
        log("No duration yet, trying again...")
        _duration_check_timer = delayed_duration_check_callback
        obs.timer_add(_duration_check_timer, 500)


def schedule_title_clear_with_delay():
    """Schedule title clear after a short delay to ensure accurate duration."""
    global _duration_check_timer

    # Cancel any existing timer
    if _duration_check_timer:
        obs.timer_remove(_duration_check_timer)
        _duration_check_timer = None

    # Schedule the duration check after 200ms
    _duration_check_timer = delayed_duration_check_callback
    obs.timer_add(_duration_check_timer, 200)


def is_title_clear_scheduled():
    """Check if title clear is scheduled."""
    return _title_clear_scheduled


def get_title_clear_timer():
    """Get the title clear timer reference."""
    return _title_clear_timer


def get_pending_title_info():
    """Get pending title info."""
    return _pending_title_info


def update_text_source(song, artist, gemini_failed=False):
    """
    Update text and trigger fade effect.
    This is called when we want to change the text with a transition.
    """
    # Import here to avoid circular dependency
    from .media_control import update_text_source_content
    from .opacity_control import fade_in_text, fade_out_text, get_current_opacity, set_pending_text

    # If opacity is not 0, fade out first then update
    if get_current_opacity() > 0:
        set_pending_text({'song': song, 'artist': artist, 'gemini_failed': gemini_failed})
        fade_out_text()
    else:
        # Already at 0, just update and fade in
        update_text_source_content(song, artist, gemini_failed)
        if song or artist:  # Only fade in if there's content
            fade_in_text()
