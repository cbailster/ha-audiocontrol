"""Custom exceptions for AudioControl library."""


class AudioControlControlException(Exception):
    """Base exception for all AudioControl errors."""


class AudioControlConnectionError(AudioControlControlException):
    """Raised when unable to establish or maintain connection to matrix."""


class AudioControlCommandError(AudioControlControlException):
    """Raised when a command execution fails."""


class AudioControlTimeoutError(AudioControlControlException):
    """Raised when a command times out."""
