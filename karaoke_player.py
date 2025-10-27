"""
Karaoke-Style Lyrics Player with AI Transcription
Character-by-character display for dramatic typewriter effect
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

import pygame
from yt_dlp import YoutubeDL
import whisper

# --- Configuration ---
# Available Whisper Models
WHISPER_MODELS = [
    'tiny.en',      # English-only, fastest, ~1GB RAM
    'tiny',         # Multilingual, fastest, ~1GB RAM
    'base.en',      # English-only, fast, ~1GB RAM
    'base',         # Multilingual, fast, ~1GB RAM
    'small.en',     # English-only, balanced, ~2GB RAM
    'small',        # Multilingual, balanced, ~2GB RAM
    'medium.en',    # English-only, accurate, ~5GB RAM
    'medium',       # Multilingual, accurate, ~5GB RAM
    'large-v1',     # Multilingual, very accurate, ~10GB RAM
    'large-v2',     # Multilingual, very accurate, ~10GB RAM
    'large-v3',     # Multilingual, most accurate, ~10GB RAM
    'large',        # Alias for latest large model, ~10GB RAM
    'large-v3-turbo', # Multilingual, fast large model, ~6GB RAM
    'turbo',        # Alias for large-v3-turbo, ~6GB RAM
]

@dataclass
class Config:
    """Configuration settings for the karaoke player"""
    song_query: str = "Imagine Dragons Believer lyric video"
    audio_filename: str = "temp_audio.mp3"
    audio_file_base: str = "temp_audio"
    whisper_model: str = "base.en"  # Choose from WHISPER_MODELS list
    new_line_threshold: float = 0.8  # Seconds of silence before new line
    audio_quality: str = "192"
    timing_offset: float = 0.0  # Adjust if audio/lyrics are out of sync (seconds)
    cleanup_on_exit: bool = True
    character_mode: bool = True  # Display character-by-character

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.whisper_model not in WHISPER_MODELS:
            logger.warning(
                f"⚠️  Model '{self.whisper_model}' not in standard list. "
                f"Available models: {', '.join(WHISPER_MODELS)}"
            )

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class KaraokePlayer:
    """Main karaoke player class with character-by-character display"""
    
    def __init__(self, config: Config):
        self.config = config
        self.audio_path = Path(config.audio_filename)
        self._model = None
        
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
    
    def _clear_console(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def cleanup_audio_file(self):
        """Remove temporary audio file"""
        if self.config.cleanup_on_exit and self.audio_path.exists():
            try:
                self.audio_path.unlink()
                logger.info(f"🧹 Cleaned up {self.audio_path}")
            except Exception as e:
                logger.warning(f"Could not delete audio file: {e}")
    
    def download_audio(self) -> bool:
        """
        Downloads audio from YouTube with optimized settings.
        Returns True if successful, False otherwise.
        """
        logger.info(f"[1/3] 📥 Downloading audio for '{self.config.song_query}'...")
        
        # Clean up any existing file
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
            'default_search': 'ytsearch1',  # Only get first result
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
                    logger.info(f"📺 Video: {title} ({duration//60}:{duration%60:02d})")
            
            if not self.audio_path.exists():
                raise RuntimeError("Audio file was not created after download")
            
            logger.info(f"✅ Audio saved to {self.audio_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error downloading audio: {e}")
            return False
    
    def transcribe_audio(self) -> Optional[List[Dict[str, Any]]]:
        """
        Transcribes audio using Whisper with word-level timestamps.
        Returns list of word dictionaries or None on failure.
        """
        logger.info(f"[2/3] 🤖 Transcribing with Whisper '{self.config.whisper_model}'...")
        
        if not self.audio_path.exists():
            logger.error(f"❌ Audio file not found: {self.audio_path}")
            return None
        
        try:
            # Load model (cached after first load)
            if self._model is None:
                logger.info(f"📦 Loading model '{self.config.whisper_model}'...")
                self._model = whisper.load_model(self.config.whisper_model)
                logger.info("✅ Model loaded successfully")
            
            # Transcribe with word-level timestamps
            result = self._model.transcribe(
                str(self.audio_path),
                verbose=False,
                word_timestamps=True,
                language="en"
            )
            
            # Extract words from segments
            words = []
            for segment in result.get('segments', []):
                segment_words = segment.get('words', [])
                words.extend(segment_words)
            
            if not words:
                logger.error("❌ No words found in transcription")
                return None
            
            logger.info(f"✅ Transcription complete: {len(words)} words")
            return words
            
        except FileNotFoundError as e:
            if "ffmpeg" in str(e).lower():
                logger.error("❌ FATAL: ffmpeg not found. Install it and add to PATH.")
            else:
                logger.error(f"❌ File error: {e}")
            return None
        except RuntimeError as e:
            if "model" in str(e).lower():
                logger.error(f"❌ Model '{self.config.whisper_model}' not available.")
                logger.error(f"   Available models: {', '.join(WHISPER_MODELS[:8])}")
            else:
                logger.error(f"❌ Runtime error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Transcription error: {e}")
            return None
    
    def _generate_character_timings(self, words: List[Dict[str, Any]]) -> List[Tuple[str, float, bool]]:
        """
        Generates character-level timings from word-level timestamps.
        Returns list of (character, timestamp, is_newline) tuples.
        """
        char_timings = []
        last_word_end = 0.0
        
        for word_idx, word_info in enumerate(words):
            word_start = word_info.get('start', 0)
            word_end = word_info.get('end', word_start + 0.3)
            word_text = word_info.get('word', '').strip()
            
            # Check for line break before this word
            if word_idx > 0:
                gap = word_start - last_word_end
                if gap > self.config.new_line_threshold:
                    char_timings.append(('\n', word_start - 0.05, True))
            
            # Calculate character timing
            if len(word_text) > 0:
                word_duration = word_end - word_start
                char_duration = word_duration / len(word_text)
                
                for char_idx, char in enumerate(word_text):
                    char_time = word_start + (char_idx * char_duration)
                    char_timings.append((char, char_time, False))
                
                # Add space after word (unless it's the last word)
                if word_idx < len(words) - 1:
                    space_time = word_end
                    char_timings.append((' ', space_time, False))
            
            last_word_end = word_end
        
        return char_timings
    
    def play_karaoke(self, words: List[Dict[str, Any]]):
        """
        Plays audio with synchronized character-by-character lyrics display.
        Creates a dramatic typewriter effect.
        """
        logger.info("\n[3/3] 🎤 Starting karaoke mode (character-by-character)...")
        time.sleep(1.5)
        self._clear_console()
        
        # Generate character timings
        char_timings = self._generate_character_timings(words)
        logger.info(f"✨ Generated {len(char_timings)} character timings")
        time.sleep(0.5)
        self._clear_console()
        
        with self._pygame_context():
            try:
                pygame.mixer.music.load(str(self.audio_path))
                pygame.mixer.music.play()
            except pygame.error as e:
                logger.error(f"❌ Error loading audio: {e}")
                return
            
            start_time = time.time()
            current_char_idx = 0
            
            print("\n🎵 ", end='', flush=True)
            
            try:
                while pygame.mixer.music.get_busy() and current_char_idx < len(char_timings):
                    # Calculate elapsed time
                    elapsed = time.time() - start_time + self.config.timing_offset
                    
                    char, char_time, is_newline = char_timings[current_char_idx]
                    
                    # Check if it's time to display this character
                    if elapsed >= char_time:
                        if is_newline:
                            print("\n🎵 ", end='', flush=True)
                        else:
                            # Print character with color
                            print(f"\033[1;36m{char}\033[0m", end='', flush=True)
                        
                        current_char_idx += 1
                    
                    time.sleep(0.005)  # Smaller sleep for smoother character display
                
                # Wait for song to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("\n\n⏸️  Stopped by user")
                pygame.mixer.music.stop()
            
            print("\n\n✨ --- Song Finished --- ✨\n")
    
    def run(self):
        """Main execution flow"""
        try:
            # Step 1: Download
            if not self.download_audio():
                return False
            
            # Step 2: Transcribe
            words = self.transcribe_audio()
            if not words:
                return False
            
            # Step 3: Play
            self.play_karaoke(words)
            
            return True
            
        finally:
            self.cleanup_audio_file()


def main():
    """Entry point with configuration"""
    config = Config(
        song_query="Imagine Dragons Believer lyric video",
        whisper_model="base.en",  # See WHISPER_MODELS for all options
        new_line_threshold=0.8,
        timing_offset=0.0,  # Adjust if lyrics are ahead/behind audio
        character_mode=True,  # Character-by-character display
    )
    
    player = KaraokePlayer(config)
    
    try:
        success = player.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()