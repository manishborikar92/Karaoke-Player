"""
Custom exceptions for Karaoke Player.
"""


class KaraokeError(Exception):
    """Base exception for all karaoke-related errors."""
    pass


class DownloadError(KaraokeError):
    """Raised when YouTube download fails."""
    pass


class TranscriptionError(KaraokeError):
    """Raised when audio transcription fails."""
    pass


class AudioPlaybackError(KaraokeError):
    """Raised when audio playback fails."""
    pass


class ConfigurationError(KaraokeError):
    """Raised when configuration is invalid."""
    pass


class DependencyError(KaraokeError):
    """Raised when required dependency is missing."""
    pass


class InvalidInputError(KaraokeError):
    """Raised when user input is invalid."""
    pass


class FileOperationError(KaraokeError):
    """Raised when file operations fail."""
    pass


class CacheError(KaraokeError):
    """Raised when cache operations fail."""
    pass
