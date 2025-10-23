# ===== src/core/__init__.py =====
"""
Core functionality for Karaoke Player.
"""

from .config import (
    AppConfig,
    AudioConfig,
    TranscriptionConfig,
    DisplayConfig,
    DownloadConfig,
    WhisperModel,
    DisplayMode,
    Theme,
    load_config,
    create_default_config,
)
from .exceptions import (
    KaraokeError,
    DownloadError,
    TranscriptionError,
    AudioPlaybackError,
    ConfigurationError,
    DependencyError,
    InvalidInputError,
    FileOperationError,
    CacheError,
)
from .logger import setup_logging, get_logger
from .downloader import YouTubeDownloader
from .transcriber import Transcriber, Transcription, Word
from .player import AudioPlayer, LyricsSync, PlaybackState

__all__ = [
    # Config
    "AppConfig",
    "AudioConfig",
    "TranscriptionConfig",
    "DisplayConfig",
    "DownloadConfig",
    "WhisperModel",
    "DisplayMode",
    "Theme",
    "load_config",
    "create_default_config",
    # Exceptions
    "KaraokeError",
    "DownloadError",
    "TranscriptionError",
    "AudioPlaybackError",
    "ConfigurationError",
    "DependencyError",
    "InvalidInputError",
    "FileOperationError",
    "CacheError",
    # Logging
    "setup_logging",
    "get_logger",
    # Core classes
    "YouTubeDownloader",
    "Transcriber",
    "Transcription",
    "Word",
    "AudioPlayer",
    "LyricsSync",
    "PlaybackState",
]