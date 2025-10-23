"""
Audio playback engine with precise synchronization.
"""

import time
from pathlib import Path
from typing import Optional, Callable, List, Tuple
from enum import Enum

import pygame

from .config import AppConfig, DisplayMode
from .transcriber import Transcription, Word
from .exceptions import AudioPlaybackError
from .logger import get_logger


logger = get_logger(__name__)


class PlaybackState(Enum):
    """Playback state enumeration."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"


class AudioPlayer:
    """High-precision audio player with lyrics synchronization."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.audio_config = config.audio
        self.display_config = config.display
        self.state = PlaybackState.STOPPED
        self._initialized = False
        self._start_time: Optional[float] = None
        self._pause_time: Optional[float] = None
        self._paused_duration: float = 0.0
    
    def _initialize_pygame(self) -> None:
        """Initialize pygame mixer."""
        if not self._initialized:
            try:
                pygame.init()
                pygame.mixer.init(
                    frequency=self.audio_config.sample_rate,
                    size=-16,
                    channels=self.audio_config.channels,
                    buffer=self.audio_config.buffer_size
                )
                self._initialized = True
                logger.info("Audio system initialized")
            except pygame.error as e:
                raise AudioPlaybackError(f"Failed to initialize audio: {e}")
    
    def load(self, audio_path: Path) -> None:
        """
        Load audio file.
        
        Args:
            audio_path: Path to audio file
            
        Raises:
            AudioPlaybackError: If loading fails
        """
        if not audio_path.exists():
            raise AudioPlaybackError(f"Audio file not found: {audio_path}")
        
        self._initialize_pygame()
        
        try:
            pygame.mixer.music.load(str(audio_path))
            logger.info(f"Loaded audio: {audio_path.name}")
        except pygame.error as e:
            raise AudioPlaybackError(f"Failed to load audio: {e}")
    
    def play(self) -> None:
        """Start or resume playback."""
        if not self._initialized:
            raise AudioPlaybackError("Audio not loaded")
        
        try:
            if self.state == PlaybackState.PAUSED:
                pygame.mixer.music.unpause()
                self._paused_duration += time.time() - self._pause_time
                logger.info("Playback resumed")
            else:
                pygame.mixer.music.play()
                self._start_time = time.time()
                self._paused_duration = 0.0
                logger.info("Playback started")
            
            self.state = PlaybackState.PLAYING
        except pygame.error as e:
            raise AudioPlaybackError(f"Playback failed: {e}")
    
    def pause(self) -> None:
        """Pause playback."""
        if self.state == PlaybackState.PLAYING:
            pygame.mixer.music.pause()
            self._pause_time = time.time()
            self.state = PlaybackState.PAUSED
            logger.info("Playback paused")
    
    def stop(self) -> None:
        """Stop playback."""
        if self._initialized:
            pygame.mixer.music.stop()
            self.state = PlaybackState.STOPPED
            self._start_time = None
            self._pause_time = None
            self._paused_duration = 0.0
            logger.info("Playback stopped")
    
    def get_position(self) -> float:
        """
        Get current playback position in seconds.
        
        Returns:
            float: Current position (0.0 if not playing)
        """
        if self.state == PlaybackState.PLAYING and self._start_time is not None:
            return time.time() - self._start_time - self._paused_duration + self.config.timing_offset
        return 0.0
    
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self.state == PlaybackState.PLAYING and pygame.mixer.music.get_busy()
    
    def set_volume(self, volume: float) -> None:
        """
        Set playback volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(volume)
    
    def cleanup(self) -> None:
        """Clean up audio resources."""
        if self._initialized:
            self.stop()
            pygame.mixer.quit()
            pygame.quit()
            self._initialized = False
            logger.info("Audio system cleaned up")


class LyricsSync:
    """Synchronizes lyrics with audio playback."""
    
    def __init__(self, config: AppConfig, transcription: Transcription):
        self.config = config
        self.transcription = transcription
        self.display_config = config.display
        self.current_index = 0
        self._character_timings: Optional[List[Tuple[str, float, bool]]] = None
    
    def _generate_character_timings(self) -> List[Tuple[str, float, bool]]:
        """
        Generate character-level timings from word-level timestamps.
        
        Returns:
            List of (character, timestamp, is_newline) tuples
        """
        if self._character_timings is not None:
            return self._character_timings
        
        char_timings = []
        last_word_end = 0.0
        
        for word_idx, word in enumerate(self.transcription.words):
            # Check for line break before this word
            if word_idx > 0:
                gap = word.start - last_word_end
                if gap > self.display_config.new_line_threshold:
                    char_timings.append(('\n', word.start - 0.05, True))
            
            # Calculate character timing
            word_text = word.text
            if len(word_text) > 0:
                word_duration = word.duration()
                char_duration = word_duration / len(word_text)
                
                for char_idx, char in enumerate(word_text):
                    char_time = word.start + (char_idx * char_duration)
                    char_timings.append((char, char_time, False))
                
                # Add space after word (unless it's the last word)
                if word_idx < len(self.transcription.words) - 1:
                    char_timings.append((' ', word.end, False))
            
            last_word_end = word.end
        
        self._character_timings = char_timings
        return char_timings
    
    def get_current_items(self, position: float) -> List[Tuple[str, bool]]:
        """
        Get items (words or characters) to display at current position.
        
        Args:
            position: Current playback position in seconds
            
        Returns:
            List of (text, is_newline) tuples
        """
        items = []
        
        if self.display_config.mode == DisplayMode.CHARACTER_BY_CHARACTER:
            char_timings = self._generate_character_timings()
            
            while self.current_index < len(char_timings):
                char, char_time, is_newline = char_timings[self.current_index]
                
                if position >= char_time:
                    items.append((char, is_newline))
                    self.current_index += 1
                else:
                    break
        else:
            # Word-by-word mode
            while self.current_index < len(self.transcription.words):
                word = self.transcription.words[self.current_index]
                
                if position >= word.start:
                    # Check for line break
                    if self.current_index > 0:
                        prev_word = self.transcription.words[self.current_index - 1]
                        gap = word.start - prev_word.end
                        if gap > self.display_config.new_line_threshold:
                            items.append(('\n', True))
                    
                    items.append((word.text + ' ', False))
                    self.current_index += 1
                else:
                    break
        
        return items
    
    def reset(self) -> None:
        """Reset synchronization state."""
        self.current_index = 0


if __name__ == "__main__":
    # Demo usage
    from .config import AppConfig
    from .transcriber import Transcription, Word
    
    config = AppConfig()
    player = AudioPlayer(config)
    
    # Example words
    words = [
        Word("Hello", 0.0, 0.5),
        Word("World", 0.6, 1.0),
    ]
    transcription = Transcription(
        words=words,
        text="Hello World",
        language="en",
        duration=1.0,
        model="base.en"
    )
    
    sync = LyricsSync(config, transcription)
    print(f"Initialized with {len(transcription.words)} words")
