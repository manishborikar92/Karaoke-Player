#!/usr/bin/env python3
"""
Karaoke Lyrics Player - Professional Edition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A sophisticated karaoke-style lyrics player with both CLI and GUI interfaces.
Features AI-powered transcription, YouTube integration, and real-time synchronization.

:copyright: (c) 2025
:license: MIT
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.config import AppConfig, load_config
from src.core.logger import setup_logging, get_logger
from src.cli.interface import CLIInterface
from src.gui.application import GUIApplication
from src.core.exceptions import KaraokeError


__version__ = "2.0.0"
__author__ = "Karaoke Team"


logger = get_logger(__name__)


def main() -> int:
    """
    Main entry point for the Karaoke Player application.
    
    Returns:
        int: Exit code (0 for success, non-zero for errors)
    """
    try:
        # Setup logging
        setup_logging()
        logger.info(f"Karaoke Player v{__version__} starting...")
        
        # Load configuration
        config = load_config()
        
        # Determine interface mode
        if len(sys.argv) > 1 and sys.argv[1] in ['--cli', '-c']:
            # CLI mode
            logger.info("Starting in CLI mode")
            interface = CLIInterface(config)
            return interface.run()
        elif len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
            # Show help
            print_help()
            return 0
        else:
            # GUI mode (default)
            logger.info("Starting in GUI mode")
            app = GUIApplication(config)
            return app.run()
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130
    except KaraokeError as e:
        logger.error(f"Application error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


def print_help() -> None:
    """Print help information."""
    help_text = f"""
Karaoke Player v{__version__}
{'=' * 50}

Usage:
    karaoke_player.py [OPTIONS]

Options:
    --gui, -g          Launch GUI interface (default)
    --cli, -c          Launch CLI interface
    --help, -h         Show this help message
    --version, -v      Show version information

Examples:
    karaoke_player.py              # Launch GUI
    karaoke_player.py --cli        # Launch CLI
    
Configuration:
    Edit config.yaml to customize settings

Features:
    • AI-powered transcription (Whisper)
    • YouTube audio download
    • Character-by-character sync
    • Multiple display themes
    • Playlist management
    
For more information, visit: https://github.com/yourusername/karaoke-player
"""
    print(help_text)


if __name__ == "__main__":
    sys.exit(main())
