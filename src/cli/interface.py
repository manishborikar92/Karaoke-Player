"""
Command-line interface for Karaoke Player.
"""

import sys
import os
import time
from pathlib import Path
from typing import Optional

from ..core.config import AppConfig
from ..core.downloader import YouTubeDownloader
from ..core.transcriber import Transcriber
from ..core.player import AudioPlayer, LyricsSync, PlaybackState
from ..core.exceptions import KaraokeError
from ..core.logger import get_logger


logger = get_logger(__name__)


class CLIInterface:
    """Command-line interface for karaoke playback."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.downloader = YouTubeDownloader(config)
        self.transcriber = Transcriber(config)
        self.player = AudioPlayer(config)
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _print_banner(self) -> None:
        """Print application banner."""
        if not self.config.show_banner:
            return
        
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🎤 KARAOKE PLAYER PRO 2.0 🎤                 ║
║                                                           ║
║           AI-Powered Lyrics Synchronization               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def _get_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Get user input with optional default."""
        if default:
            prompt = f"{prompt} [{default}]: "
        else:
            prompt = f"{prompt}: "
        
        value = input(prompt).strip()
        return value if value else (default or "")
    
    def _colorize(self, text: str, color: str = "cyan") -> str:
        """Colorize text for terminal output."""
        if not self.config.colored_output:
            return text
        
        colors = {
            'red': '\033[31m',
            'green': '\033[32m',
            'yellow': '\033[33m',
            'blue': '\033[34m',
            'magenta': '\033[35m',
            'cyan': '\033[36m',
            'white': '\033[37m',
            'bold': '\033[1m',
            'reset': '\033[0m',
        }
        
        return f"{colors.get(color, '')}{text}{colors['reset']}"
    
    def _show_progress(self, message: str, progress: float) -> None:
        """Show progress bar."""
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        percent = int(progress * 100)
        
        sys.stdout.write(f'\r{message}: [{bar}] {percent}%')
        sys.stdout.flush()
        
        if progress >= 1.0:
            print()
    
    def run(self) -> int:
        """
        Run CLI interface.
        
        Returns:
            int: Exit code
        """
        try:
            self._clear_screen()
            self._print_banner()
            
            # Get song query
            query = self._get_input(
                "\n🎵 Enter song name or YouTube URL",
                "Imagine Dragons Believer lyrics"
            )
            
            if not query:
                print(self._colorize("❌ No song specified", "red"))
                return 1
            
            print()
            
            # Download audio
            print(self._colorize("[1/3] 📥 Downloading audio...", "bold"))
            
            def download_progress(info):
                if 'percent' in info:
                    # Parse percent string
                    try:
                        percent_str = info['percent'].replace('%', '')
                        progress = float(percent_str) / 100.0
                        self._show_progress("Downloading", progress)
                    except ValueError:
                        pass
            
            try:
                audio_file = self.downloader.download(query, progress_callback=download_progress)
                print(self._colorize(f"✅ Audio downloaded: {audio_file.name}", "green"))
            except KaraokeError as e:
                print(self._colorize(f"❌ Download failed: {e}", "red"))
                return 1
            
            print()
            
            # Transcribe audio
            print(self._colorize("[2/3] 🤖 Transcribing with AI...", "bold"))
            print(self._colorize(f"Model: {self.config.transcription.model.value}", "cyan"))
            
            def transcribe_progress(stage, progress):
                self._show_progress(stage, progress)
            
            try:
                transcription = self.transcriber.transcribe(
                    audio_file,
                    progress_callback=transcribe_progress
                )
                print(self._colorize(
                    f"✅ Transcribed {len(transcription.words)} words",
                    "green"
                ))
            except KaraokeError as e:
                print(self._colorize(f"❌ Transcription failed: {e}", "red"))
                return 1
            
            print()
            
            # Play karaoke
            print(self._colorize("[3/3] 🎤 Starting karaoke mode...", "bold"))
            print(self._colorize(
                f"Display mode: {self.config.display.mode.value}",
                "cyan"
            ))
            print(self._colorize("\nControls: Space=Pause, Q=Quit\n", "yellow"))
            
            time.sleep(2)
            self._clear_screen()
            
            # Run playback
            result = self._play_karaoke(audio_file, transcription)
            
            # Cleanup
            if self.config.auto_cleanup and audio_file.exists():
                audio_file.unlink()
            
            return result
            
        except KeyboardInterrupt:
            print(self._colorize("\n\n⏸️  Interrupted by user", "yellow"))
            return 130
        except Exception as e:
            logger.exception("Unexpected error in CLI")
            print(self._colorize(f"\n❌ Error: {e}", "red"))
            return 1
        finally:
            self.player.cleanup()
    
    def _play_karaoke(self, audio_file: Path, transcription) -> int:
        """
        Play karaoke with lyrics display.
        
        Args:
            audio_file: Path to audio file
            transcription: Transcription object
            
        Returns:
            int: Exit code
        """
        try:
            # Load and start playback
            self.player.load(audio_file)
            self.player.play()
            
            # Initialize lyrics sync
            sync = LyricsSync(self.config, transcription)
            
            # Display header
            print("\n" + self._colorize("🎵 ", "magenta"), end='', flush=True)
            
            last_position = 0.0
            
            while self.player.is_playing():
                position = self.player.get_position()
                
                # Get new lyrics items
                if position > last_position:
                    items = sync.get_current_items(position)
                    
                    for text, is_newline in items:
                        if is_newline:
                            print("\n" + self._colorize("🎵 ", "magenta"), end='', flush=True)
                        else:
                            # Colorize text
                            colored_text = self._colorize(text, "cyan")
                            print(colored_text, end='', flush=True)
                    
                    last_position = position
                
                # Small sleep to prevent CPU spinning
                time.sleep(self.config.display.character_delay)
            
            # Wait for song to finish
            while self.player.is_playing():
                time.sleep(0.1)
            
            print("\n\n" + self._colorize("✨ --- Song Finished --- ✨", "green"))
            print()
            
            return 0
            
        except KeyboardInterrupt:
            self.player.stop()
            raise
        except Exception as e:
            logger.exception("Playback error")
            print(self._colorize(f"\n❌ Playback error: {e}", "red"))
            return 1


if __name__ == "__main__":
    from ..core.config import AppConfig
    
    config = AppConfig()
    cli = CLIInterface(config)
    sys.exit(cli.run())
