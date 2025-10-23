"""
AI-powered audio transcription with word-level timestamps.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, asdict

import whisper
import torch

from .config import AppConfig, WhisperModel
from .exceptions import TranscriptionError, DependencyError
from .logger import get_logger


logger = get_logger(__name__)


@dataclass
class Word:
    """Represents a word with timing information."""
    text: str
    start: float
    end: float
    probability: float = 1.0
    
    def duration(self) -> float:
        """Get word duration in seconds."""
        return self.end - self.start
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Transcription:
    """Complete transcription with metadata."""
    words: List[Word]
    text: str
    language: str
    duration: float
    model: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'words': [w.to_dict() for w in self.words],
            'text': self.text,
            'language': self.language,
            'duration': self.duration,
            'model': self.model,
        }
    
    def save(self, path: Path) -> None:
        """Save transcription to JSON file."""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Transcription saved to {path}")
    
    @classmethod
    def load(cls, path: Path) -> 'Transcription':
        """Load transcription from JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        words = [Word(**w) for w in data['words']]
        return cls(
            words=words,
            text=data['text'],
            language=data['language'],
            duration=data['duration'],
            model=data['model'],
        )


class Transcriber:
    """AI transcription engine with caching and optimization."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.transcription_config = config.transcription
        self.cache_dir = config.cache_dir / "transcriptions"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._model: Optional[whisper.Whisper] = None
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        try:
            import whisper
            import torch
        except ImportError as e:
            raise DependencyError(
                f"Missing required dependency: {e}. "
                "Install with: pip install openai-whisper torch"
            )
        
        # Check for FFmpeg
        try:
            import subprocess
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise DependencyError(
                "FFmpeg is not installed or not in PATH. "
                "Please install FFmpeg to use transcription."
            )
    
    def _load_model(self) -> whisper.Whisper:
        """Load Whisper model (cached after first load)."""
        if self._model is None:
            model_name = self.transcription_config.model.value
            logger.info(f"Loading Whisper model: {model_name}")
            
            # Check if GPU is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            try:
                self._model = whisper.load_model(model_name, device=device)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise TranscriptionError(f"Model loading failed: {e}")
        
        return self._model
    
    def _generate_cache_key(self, audio_path: Path) -> str:
        """Generate cache key from audio file."""
        # Use file hash + model name for cache key
        with open(audio_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        model_name = self.transcription_config.model.value
        cache_key = f"{file_hash}_{model_name}"
        return cache_key
    
    def _get_cached_transcription(self, audio_path: Path) -> Optional[Transcription]:
        """Check if transcription is already cached."""
        if not self.config.enable_cache:
            return None
        
        cache_key = self._generate_cache_key(audio_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                logger.info(f"Found cached transcription for: {audio_path.name}")
                return Transcription.load(cache_file)
            except Exception as e:
                logger.warning(f"Failed to load cached transcription: {e}")
        
        return None
    
    def transcribe(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Transcription:
        """
        Transcribe audio file with word-level timestamps.
        
        Args:
            audio_path: Path to audio file
            progress_callback: Optional callback(stage, progress)
            
        Returns:
            Transcription: Complete transcription with word timings
            
        Raises:
            TranscriptionError: If transcription fails
        """
        if not audio_path.exists():
            raise TranscriptionError(f"Audio file not found: {audio_path}")
        
        # Check cache
        cached = self._get_cached_transcription(audio_path)
        if cached:
            return cached
        
        logger.info(f"Transcribing: {audio_path.name}")
        
        if progress_callback:
            progress_callback("Loading model", 0.0)
        
        try:
            # Load model
            model = self._load_model()
            
            if progress_callback:
                progress_callback("Transcribing", 0.2)
            
            # Transcribe with word timestamps
            result = model.transcribe(
                str(audio_path),
                language=self.transcription_config.language,
                word_timestamps=True,
                beam_size=self.transcription_config.beam_size,
                temperature=self.transcription_config.temperature,
                compression_ratio_threshold=self.transcription_config.compression_ratio_threshold,
                no_speech_threshold=self.transcription_config.no_speech_threshold,
                verbose=False,
            )
            
            if progress_callback:
                progress_callback("Processing", 0.8)
            
            # Extract words from segments
            words = []
            for segment in result.get('segments', []):
                segment_words = segment.get('words', [])
                for word_data in segment_words:
                    word = Word(
                        text=word_data.get('word', '').strip(),
                        start=word_data.get('start', 0.0),
                        end=word_data.get('end', 0.0),
                        probability=word_data.get('probability', 1.0),
                    )
                    words.append(word)
            
            if not words:
                raise TranscriptionError("No words found in transcription")
            
            # Create transcription object
            transcription = Transcription(
                words=words,
                text=result.get('text', '').strip(),
                language=result.get('language', self.transcription_config.language),
                duration=words[-1].end if words else 0.0,
                model=self.transcription_config.model.value,
            )
            
            logger.info(f"Transcription complete: {len(words)} words")
            
            # Cache if enabled
            if self.config.save_transcriptions:
                cache_key = self._generate_cache_key(audio_path)
                cache_file = self.cache_dir / f"{cache_key}.json"
                transcription.save(cache_file)
            
            if progress_callback:
                progress_callback("Complete", 1.0)
            
            return transcription
            
        except TranscriptionError:
            raise
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise TranscriptionError(f"Failed to transcribe audio: {e}")
    
    def clear_cache(self) -> int:
        """
        Clear all cached transcriptions.
        
        Returns:
            int: Number of files deleted
        """
        count = 0
        for file in self.cache_dir.glob("*.json"):
            try:
                file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")
        
        logger.info(f"Cleared {count} cached transcriptions")
        return count


if __name__ == "__main__":
    # Demo usage
    from .config import AppConfig
    
    config = AppConfig()
    transcriber = Transcriber(config)
    
    # Example with a test file
    audio_file = Path("test_audio.mp3")
    if audio_file.exists():
        try:
            transcription = transcriber.transcribe(audio_file)
            print(f"Transcribed {len(transcription.words)} words")
            print(f"Full text: {transcription.text[:100]}...")
        except TranscriptionError as e:
            print(f"Error: {e}")