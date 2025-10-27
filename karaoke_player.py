"""
🎤 AI-Powered Karaoke Lyrics Player
Character-by-character display with Whisper AI transcription
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager
from enum import Enum

import pygame
from yt_dlp import YoutubeDL
import whisper


# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

class DisplayMode(Enum):
    """Display modes for lyrics"""
    CHARACTER = "character"  # Character-by-character (typewriter effect)
    WORD = "word"           # Word-by-word
    LINE = "line"           # Line-by-line

WHISPER_MODELS = [
    'tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small',
    'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3',
    'large', 'large-v3-turbo', 'turbo'
]

# Best model for speed + accuracy balance
DEFAULT_MODEL = "large-v3-turbo"  # Fast large model with excellent accuracy


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class Config:
    """Configuration settings for the karaoke player"""
    song_query: str = ""
    audio_filename: str = "temp_audio.mp3"
    audio_file_base: str = "temp_audio"
    whisper_model: str = DEFAULT_MODEL
    display_mode: DisplayMode = DisplayMode.CHARACTER
    new_line_threshold: float = 0.5  # Lower = more line breaks
    max_line_length: int = 50  # Maximum characters per line
    audio_quality: str = "192"
    timing_offset: float = 0.0
    cleanup_on_exit: bool = True
    
    def __post_init__(self):
        """Validate configuration"""
        if self.whisper_model not in WHISPER_MODELS:
            logger.warning(
                f"⚠️  Model '{self.whisper_model}' not in standard list. "
                f"Using default: {DEFAULT_MODEL}"
            )
            self.whisper_model = DEFAULT_MODEL


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# UI HELPERS
# ============================================================================

class UI:
    """Console UI utilities"""
    
    # Colors
    CYAN = '\033[1;36m'
    GREEN = '\033[1;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[1;31m'
    MAGENTA = '\033[1;35m'
    BLUE = '\033[1;34m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def clear():
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_header():
        """Print application header"""
        UI.clear()
        print(f"\n{UI.MAGENTA}{'=' * 60}{UI.RESET}")
        print(f"{UI.CYAN}{UI.BOLD}🎤  AI-POWERED KARAOKE LYRICS PLAYER  🎵{UI.RESET}")
        print(f"{UI.MAGENTA}{'=' * 60}{UI.RESET}\n")
    
    @staticmethod
    def print_section(title: str):
        """Print section header"""
        print(f"\n{UI.BLUE}{'─' * 60}{UI.RESET}")
        print(f"{UI.BOLD}{title}{UI.RESET}")
        print(f"{UI.BLUE}{'─' * 60}{UI.RESET}\n")
    
    @staticmethod
    def print_success(message: str):
        """Print success message"""
        print(f"{UI.GREEN}✓ {message}{UI.RESET}")
    
    @staticmethod
    def print_error(message: str):
        """Print error message"""
        print(f"{UI.RED}✗ {message}{UI.RESET}")
    
    @staticmethod
    def print_info(message: str):
        """Print info message"""
        print(f"{UI.CYAN}ℹ {message}{UI.RESET}")
    
    @staticmethod
    def print_warning(message: str):
        """Print warning message"""
        print(f"{UI.YELLOW}⚠ {message}{UI.RESET}")
    
    @staticmethod
    def get_input(prompt: str, default: str = "") -> str:
        """Get user input with colored prompt"""
        if default:
            prompt_text = f"{UI.CYAN}{prompt} [{default}]: {UI.RESET}"
        else:
            prompt_text = f"{UI.CYAN}{prompt}: {UI.RESET}"
        
        value = input(prompt_text).strip()
        return value if value else default
    
    @staticmethod
    def get_choice(prompt: str, options: List[str], default: int = 0) -> int:
        """Get user choice from options"""
        print(f"\n{UI.CYAN}{prompt}{UI.RESET}")
        for i, option in enumerate(options, 1):
            marker = f"{UI.GREEN}►{UI.RESET}" if i-1 == default else " "
            print(f"  {marker} {i}. {option}")
        
        while True:
            choice = input(f"\n{UI.CYAN}Enter choice [1-{len(options)}] (default: {default+1}): {UI.RESET}").strip()
            
            if not choice:
                return default
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return idx
                UI.print_error(f"Please enter a number between 1 and {len(options)}")
            except ValueError:
                UI.print_error("Please enter a valid number")


# ============================================================================
# KARAOKE PLAYER
# ============================================================================

class KaraokePlayer:
    """Main karaoke player with AI transcription"""
    
    def __init__(self, config: Config):
        self.config = config
        self.audio_path = Path(config.audio_filename)
        self._model = None
    
    # ------------------------------------------------------------------------
    # Context Managers
    # ------------------------------------------------------------------------
    
    @contextmanager
    def _pygame_context(self):
        """Context manager for pygame initialization/cleanup"""
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        try:
            yield
        finally:
            pygame.mixer.quit()
            pygame.quit()
    
    # ------------------------------------------------------------------------
    # Audio Management
    # ------------------------------------------------------------------------
    
    def cleanup_audio_file(self):
        """Remove temporary audio file"""
        if self.config.cleanup_on_exit and self.audio_path.exists():
            try:
                self.audio_path.unlink()
                UI.print_info(f"Cleaned up {self.audio_path}")
            except Exception as e:
                UI.print_warning(f"Could not delete audio file: {e}")
    
    def download_audio(self) -> bool:
        """Download audio from YouTube"""
        UI.print_section("📥 STEP 1: DOWNLOADING AUDIO")
        UI.print_info(f"Searching for: '{self.config.song_query}'")
        
        # Clean up existing file
        if self.audio_path.exists():
            self.audio_path.unlink()
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': self.config.audio_quality,
            }],
            'outtmpl': self.config.audio_file_base,
            'default_search': 'ytsearch1',
            'quiet': True,
            'noprogress': True,
            'no_warnings': True,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.config.song_query, download=True)
                if info:
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)
                    UI.print_success(f"Found: {title}")
                    UI.print_info(f"Duration: {duration//60}:{duration%60:02d}")
            
            if not self.audio_path.exists():
                raise RuntimeError("Audio file was not created")
            
            UI.print_success("Download complete!")
            return True
            
        except Exception as e:
            UI.print_error(f"Download failed: {e}")
            return False
    
    # ------------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------------
    
    def transcribe_audio(self) -> Optional[List[Dict[str, Any]]]:
        """Transcribe audio using Whisper AI"""
        UI.print_section("🤖 STEP 2: AI TRANSCRIPTION")
        UI.print_info(f"Model: Whisper '{self.config.whisper_model}'")
        
        if not self.audio_path.exists():
            UI.print_error(f"Audio file not found: {self.audio_path}")
            return None
        
        try:
            # Load model
            if self._model is None:
                UI.print_info("Loading AI model (first run may take a moment)...")
                self._model = whisper.load_model(self.config.whisper_model)
                UI.print_success("Model loaded successfully")
            
            # Transcribe
            UI.print_info("Transcribing audio with word-level timestamps...")
            result = self._model.transcribe(
                str(self.audio_path),
                verbose=False,
                word_timestamps=True,
                language="en"
            )
            
            # Extract words
            words = []
            for segment in result.get('segments', []):
                words.extend(segment.get('words', []))
            
            if not words:
                UI.print_error("No words found in transcription")
                return None
            
            UI.print_success(f"Transcription complete: {len(words)} words detected")
            return words
            
        except FileNotFoundError as e:
            if "ffmpeg" in str(e).lower():
                UI.print_error("FATAL: ffmpeg not found. Install it and add to PATH.")
            else:
                UI.print_error(f"File error: {e}")
            return None
        except Exception as e:
            UI.print_error(f"Transcription error: {e}")
            return None
    
    # ------------------------------------------------------------------------
    # Timing Generation
    # ------------------------------------------------------------------------
    
    def _generate_character_timings(self, words: List[Dict[str, Any]]) -> List[Tuple[str, float, bool]]:
        """Generate character-level timings from word timestamps with smart line breaks"""
        char_timings = []
        last_word_end = 0.0
        current_line_length = 0
        
        for word_idx, word_info in enumerate(words):
            word_start = word_info.get('start', 0)
            word_end = word_info.get('end', word_start + 0.3)
            word_text = word_info.get('word', '').strip()
            
            # Calculate gap from last word
            gap = word_start - last_word_end if word_idx > 0 else 0
            
            # Smart line break detection
            should_break = False
            if word_idx > 0:
                # Break on significant pauses
                if gap > self.config.new_line_threshold:
                    should_break = True
                # Break on shorter pauses if line is getting long
                elif gap > 0.3 and current_line_length > self.config.max_line_length * 0.7:
                    should_break = True
                # Force break if line is too long
                elif current_line_length > self.config.max_line_length:
                    should_break = True
            
            if should_break:
                char_timings.append(('\n', word_start - 0.05, True))
                current_line_length = 0
            
            # Calculate character timing
            if len(word_text) > 0:
                word_duration = word_end - word_start
                char_duration = word_duration / len(word_text)
                
                for char_idx, char in enumerate(word_text):
                    char_time = word_start + (char_idx * char_duration)
                    char_timings.append((char, char_time, False))
                    current_line_length += 1
                
                # Add space after word
                if word_idx < len(words) - 1:
                    char_timings.append((' ', word_end, False))
                    current_line_length += 1
            
            last_word_end = word_end
        
        return char_timings
    
    def _generate_word_timings(self, words: List[Dict[str, Any]]) -> List[Tuple[str, float, bool]]:
        """Generate word-level timings with smart line breaks"""
        word_timings = []
        last_word_end = 0.0
        current_line_length = 0
        
        for word_idx, word_info in enumerate(words):
            word_start = word_info.get('start', 0)
            word_end = word_info.get('end', word_start + 0.3)
            word_text = word_info.get('word', '').strip()
            
            # Calculate gap from last word
            gap = word_start - last_word_end if word_idx > 0 else 0
            
            # Smart line break detection
            should_break = False
            if word_idx > 0:
                # Break on significant pauses
                if gap > self.config.new_line_threshold:
                    should_break = True
                # Break on shorter pauses if line is getting long
                elif gap > 0.3 and current_line_length > self.config.max_line_length * 0.7:
                    should_break = True
                # Force break if line is too long
                elif current_line_length + len(word_text) > self.config.max_line_length:
                    should_break = True
            
            if should_break:
                word_timings.append(('\n', word_start - 0.05, True))
                current_line_length = 0
            
            if word_text:
                word_timings.append((word_text + ' ', word_start, False))
                current_line_length += len(word_text) + 1
            
            last_word_end = word_end
        
        return word_timings
    
    def _generate_line_timings(self, words: List[Dict[str, Any]]) -> List[Tuple[str, float, bool]]:
        """Generate line-level timings with smart line breaks"""
        line_timings = []
        current_line = []
        line_start = 0.0
        last_word_end = 0.0
        current_line_length = 0
        
        for word_idx, word_info in enumerate(words):
            word_start = word_info.get('start', 0)
            word_end = word_info.get('end', word_start + 0.3)
            word_text = word_info.get('word', '').strip()
            
            # Calculate gap from last word
            gap = word_start - last_word_end if word_idx > 0 else 0
            
            # Smart line break detection
            should_break = False
            if word_idx > 0:
                # Break on significant pauses
                if gap > self.config.new_line_threshold:
                    should_break = True
                # Break on shorter pauses if line is getting long
                elif gap > 0.3 and current_line_length > self.config.max_line_length * 0.7:
                    should_break = True
                # Force break if line is too long
                elif current_line_length + len(word_text) > self.config.max_line_length:
                    should_break = True
            
            if should_break and current_line:
                line_text = ' '.join(current_line)
                line_timings.append((line_text, line_start, False))
                line_timings.append(('\n', word_start - 0.05, True))
                current_line = []
                current_line_length = 0
            
            if not current_line:
                line_start = word_start
            
            if word_text:
                current_line.append(word_text)
                current_line_length += len(word_text) + 1
            
            last_word_end = word_end
        
        # Add final line
        if current_line:
            line_text = ' '.join(current_line)
            line_timings.append((line_text, line_start, False))
        
        return line_timings
    
    # ------------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------------
    
    def play_karaoke(self, words: List[Dict[str, Any]]):
        """Play audio with synchronized lyrics"""
        UI.print_section("🎤 STEP 3: KARAOKE MODE")
        
        # Generate timings based on mode
        if self.config.display_mode == DisplayMode.CHARACTER:
            timings = self._generate_character_timings(words)
            UI.print_info(f"Mode: Character-by-character ({len(timings)} characters)")
        elif self.config.display_mode == DisplayMode.WORD:
            timings = self._generate_word_timings(words)
            UI.print_info(f"Mode: Word-by-word ({len(timings)} words)")
        else:
            timings = self._generate_line_timings(words)
            UI.print_info(f"Mode: Line-by-line ({len(timings)} lines)")
        
        UI.print_info("Starting playback in 2 seconds...")
        time.sleep(2)
        UI.clear()
        
        with self._pygame_context():
            try:
                pygame.mixer.music.load(str(self.audio_path))
                pygame.mixer.music.play()
            except pygame.error as e:
                UI.print_error(f"Error loading audio: {e}")
                return
            
            start_time = time.time()
            current_idx = 0
            
            print(f"\n{UI.CYAN}🎵 ", end='', flush=True)
            
            try:
                while pygame.mixer.music.get_busy() and current_idx < len(timings):
                    elapsed = time.time() - start_time + self.config.timing_offset
                    
                    text, timing, is_newline = timings[current_idx]
                    
                    if elapsed >= timing:
                        if is_newline:
                            print(f"{UI.RESET}\n{UI.CYAN}🎵 ", end='', flush=True)
                        else:
                            print(f"{UI.CYAN}{text}{UI.RESET}", end='', flush=True)
                        current_idx += 1
                    
                    time.sleep(0.005)
                
                # Wait for song to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
            except KeyboardInterrupt:
                print(f"\n\n{UI.YELLOW}⏸️  Stopped by user{UI.RESET}")
                pygame.mixer.music.stop()
            
            print(f"\n\n{UI.GREEN}✨ {'─' * 20} Song Finished {'─' * 20} ✨{UI.RESET}\n")
    
    # ------------------------------------------------------------------------
    # Main Flow
    # ------------------------------------------------------------------------
    
    def run(self) -> bool:
        """Execute the complete karaoke flow"""
        try:
            if not self.download_audio():
                return False
            
            words = self.transcribe_audio()
            if not words:
                return False
            
            self.play_karaoke(words)
            return True
            
        finally:
            self.cleanup_audio_file()


# ============================================================================
# INTERACTIVE SETUP
# ============================================================================

def interactive_setup() -> Config:
    """Interactive configuration setup"""
    UI.print_header()
    UI.print_section("⚙️  CONFIGURATION")
    
    # Song query
    song_query = UI.get_input(
        "Enter song name (artist + title recommended)",
        "Imagine Dragons Believer lyric video"
    )
    
    # Display mode
    print()
    modes = ["Character-by-character (Typewriter effect)", "Word-by-word", "Line-by-line"]
    mode_idx = UI.get_choice("Select display mode:", modes, default=0)
    mode_map = [DisplayMode.CHARACTER, DisplayMode.WORD, DisplayMode.LINE]
    
    # Advanced options
    print()
    show_advanced = UI.get_input("Show advanced options? (y/n)", "n").lower() == 'y'
    
    whisper_model = DEFAULT_MODEL
    timing_offset = 0.0
    line_break_sensitivity = 0.5  # Default
    max_line_length = 50  # Default
    
    if show_advanced:
        # Model selection
        print()
        UI.print_info(f"Available models: {', '.join(WHISPER_MODELS)}")
        custom_model = UI.get_input(
            f"Whisper model (default: {DEFAULT_MODEL})",
            DEFAULT_MODEL
        )
        if custom_model in WHISPER_MODELS:
            whisper_model = custom_model
        
        # Line break sensitivity
        print()
        UI.print_info("Line Break Settings:")
        sensitivity_input = UI.get_input(
            "Line break sensitivity in seconds (0.3=more breaks, 0.8=fewer breaks)",
            "0.5"
        )
        try:
            line_break_sensitivity = float(sensitivity_input)
        except ValueError:
            line_break_sensitivity = 0.5
        
        max_length_input = UI.get_input(
            "Max characters per line (30-80 recommended)",
            "50"
        )
        try:
            max_line_length = int(max_length_input)
        except ValueError:
            max_line_length = 50
        
        # Timing offset
        timing_input = UI.get_input("Timing offset in seconds (0.0 for none)", "0.0")
        try:
            timing_offset = float(timing_input)
        except ValueError:
            timing_offset = 0.0
    
    config = Config(
        song_query=song_query,
        whisper_model=whisper_model,
        display_mode=mode_map[mode_idx],
        new_line_threshold=line_break_sensitivity,
        max_line_length=max_line_length,
        timing_offset=timing_offset
    )
    
    return config


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    try:
        config = interactive_setup()
        
        UI.print_section("🚀 STARTING KARAOKE PLAYER")
        UI.print_info(f"Song: {config.song_query}")
        UI.print_info(f"Model: {config.whisper_model}")
        UI.print_info(f"Mode: {config.display_mode.value}")
        
        time.sleep(1)
        
        player = KaraokePlayer(config)
        success = player.run()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{UI.YELLOW}👋 Goodbye!{UI.RESET}\n")
        sys.exit(0)
    except Exception as e:
        UI.print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

# python karaoke_player.py