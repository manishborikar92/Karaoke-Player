"""
Configuration management for Karaoke Player.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
import json
from enum import Enum

from .logger import get_logger


logger = get_logger(__name__)


class WhisperModel(Enum):
    """Available Whisper models."""
    TINY = "tiny.en"
    BASE = "base.en"
    SMALL = "small.en"
    MEDIUM = "medium.en"
    LARGE = "large"


class DisplayMode(Enum):
    """Lyrics display modes."""
    WORD_BY_WORD = "word"
    CHARACTER_BY_CHARACTER = "character"


class Theme(Enum):
    """Visual themes."""
    DARK = "dark"
    LIGHT = "light"
    NEON = "neon"
    CLASSIC = "classic"


@dataclass
class AudioConfig:
    """Audio processing configuration."""
    quality: str = "192"
    sample_rate: int = 44100
    buffer_size: int = 512
    channels: int = 2
    format: str = "mp3"


@dataclass
class TranscriptionConfig:
    """Transcription settings."""
    model: WhisperModel = WhisperModel.BASE
    language: str = "en"
    enable_word_timestamps: bool = True
    beam_size: int = 5
    temperature: float = 0.0
    compression_ratio_threshold: float = 2.4
    no_speech_threshold: float = 0.6


@dataclass
class DisplayConfig:
    """Display settings."""
    mode: DisplayMode = DisplayMode.CHARACTER_BY_CHARACTER
    theme: Theme = Theme.DARK
    font_size: int = 24
    line_spacing: float = 1.5
    new_line_threshold: float = 0.8
    character_delay: float = 0.005
    word_delay: float = 0.01
    show_progress_bar: bool = True
    show_timestamps: bool = False
    fullscreen: bool = False
    window_width: int = 1024
    window_height: int = 768


@dataclass
class DownloadConfig:
    """YouTube download settings."""
    default_search: str = "ytsearch1"
    prefer_lyric_video: bool = True
    max_duration: int = 600  # seconds
    skip_ads: bool = True
    extract_audio_only: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    # Paths
    temp_dir: Path = field(default_factory=lambda: Path("temp"))
    cache_dir: Path = field(default_factory=lambda: Path("cache"))
    playlist_dir: Path = field(default_factory=lambda: Path("playlists"))
    
    # Sub-configurations
    audio: AudioConfig = field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    
    # General settings
    auto_cleanup: bool = True
    timing_offset: float = 0.0
    enable_cache: bool = True
    save_transcriptions: bool = True
    log_level: str = "INFO"
    
    # GUI-specific
    remember_window_position: bool = True
    enable_animations: bool = True
    show_visualizer: bool = True
    
    # CLI-specific
    colored_output: bool = True
    show_banner: bool = True
    
    def __post_init__(self):
        """Create directories after initialization."""
        self._ensure_directories()
        
        # Convert string enums if needed
        if isinstance(self.transcription.model, str):
            self.transcription.model = WhisperModel(self.transcription.model)
        if isinstance(self.display.mode, str):
            self.display.mode = DisplayMode(self.display.mode)
        if isinstance(self.display.theme, str):
            self.display.theme = Theme(self.display.theme)
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        for directory in [self.temp_dir, self.cache_dir, self.playlist_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    def save(self, path: Path) -> None:
        """Save configuration to file."""
        data = self.to_dict()
        
        # Convert enum values to strings
        data['transcription']['model'] = self.transcription.model.value
        data['display']['mode'] = self.display.mode.value
        data['display']['theme'] = self.display.theme.value
        
        # Convert Path objects to strings
        data['temp_dir'] = str(self.temp_dir)
        data['cache_dir'] = str(self.cache_dir)
        data['playlist_dir'] = str(self.playlist_dir)
        
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {path}")


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from file or create default.
    
    Args:
        config_path: Path to config file. If None, uses default locations.
        
    Returns:
        AppConfig: Loaded or default configuration
    """
    if config_path is None:
        # Try standard locations
        config_locations = [
            Path("config.yaml"),
            Path("config.yml"),
            Path.home() / ".karaoke" / "config.yaml",
        ]
        
        for loc in config_locations:
            if loc.exists():
                config_path = loc
                break
    
    if config_path and config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Convert string paths back to Path objects
            if 'temp_dir' in data:
                data['temp_dir'] = Path(data['temp_dir'])
            if 'cache_dir' in data:
                data['cache_dir'] = Path(data['cache_dir'])
            if 'playlist_dir' in data:
                data['playlist_dir'] = Path(data['playlist_dir'])
            
            # Nested config objects
            if 'audio' in data:
                data['audio'] = AudioConfig(**data['audio'])
            if 'transcription' in data:
                data['transcription'] = TranscriptionConfig(**data['transcription'])
            if 'display' in data:
                data['display'] = DisplayConfig(**data['display'])
            if 'download' in data:
                data['download'] = DownloadConfig(**data['download'])
            
            return AppConfig(**data)
            
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
    else:
        logger.info("No configuration file found, using defaults")
    
    return AppConfig()


def create_default_config(path: Path = Path("config.yaml")) -> None:
    """Create a default configuration file."""
    config = AppConfig()
    config.save(path)
    logger.info(f"Default configuration created at {path}")


if __name__ == "__main__":
    # Create default config when run directly
    create_default_config()
