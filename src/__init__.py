# ===== src/__init__.py =====
"""
Karaoke Player Pro - Source Package
"""

__version__ = "2.0.0"
__author__ = "Karaoke Team"
__license__ = "MIT"

from .core.config import AppConfig, load_config
from .core.exceptions import KaraokeError

__all__ = [
    "AppConfig",
    "load_config",
    "KaraokeError",
]