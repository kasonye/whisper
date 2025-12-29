"""Text formatting utilities for transcription output."""

from typing import List, Dict, Any, Optional


class FormattingConfig:
    """Configuration for text formatting."""

    # Pause thresholds in seconds
    SHORT_PAUSE_THRESHOLD = 0.5   # No break
    MEDIUM_PAUSE_THRESHOLD = 1.5  # Single line break
    # Anything above MEDIUM is a paragraph break (double line break)

    # Minimum pause to consider (avoid negative/tiny values)
    MIN_PAUSE = 0.1

    def __init__(
        self,
        short_pause: float = 0.5,
        medium_pause: float = 1.5,
        min_pause: float = 0.1
    ):
        self.short_pause_threshold = short_pause
        self.medium_pause_threshold = medium_pause
        self.min_pause = min_pause


def format_segments_with_pauses(
    segments: List[Dict[str, Any]],
    config: Optional[FormattingConfig] = None
) -> str:
    """
    Format transcription segments with intelligent line breaks based on pauses.

    Args:
        segments: List of segment dictionaries with 'text', 'start', 'end' keys
        config: Optional formatting configuration

    Returns:
        Formatted text with appropriate line breaks
    """
    if not segments:
        return ""

    if config is None:
        config = FormattingConfig()

    formatted_parts = []
    prev_end = None

    for segment in segments:
        text = segment.get("text", "").strip()
        if not text:
            continue

        start = segment.get("start")
        end = segment.get("end")

        # Handle first segment
        if prev_end is None:
            formatted_parts.append(text)
            prev_end = end
            continue

        # Calculate pause duration
        if start is not None and prev_end is not None:
            pause = start - prev_end

            # Determine break type based on pause duration
            if pause < config.min_pause:
                # Very short or negative pause - just add space
                separator = " "
            elif pause < config.short_pause_threshold:
                # Short pause - space only
                separator = " "
            elif pause < config.medium_pause_threshold:
                # Medium pause - single line break
                separator = "\n"
            else:
                # Long pause - paragraph break
                separator = "\n\n"
        else:
            # No timing info - default to space
            separator = " "

        formatted_parts.append(separator + text)
        prev_end = end

    return "".join(formatted_parts).strip()


def format_text_simple(text: str) -> str:
    """
    Simple fallback formatting when segments aren't available.
    Just cleans up the text.

    Args:
        text: Raw transcription text

    Returns:
        Cleaned text
    """
    return text.strip()
