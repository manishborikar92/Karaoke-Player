# 🎤 AI-Powered Karaoke Lyrics Player

A sophisticated karaoke-style lyrics player that uses AI (OpenAI Whisper) to automatically transcribe and synchronize lyrics character-by-character with audio downloaded from YouTube.

## ✨ Features

- 🎵 **Automatic YouTube Download**: Fetches audio from any YouTube video
- 🤖 **AI Transcription**: Uses Whisper AI for accurate word-level timestamps
- 🎯 **Perfect Sync**: Character-by-character karaoke-style display with typewriter effect
- 🎨 **Visual Feedback**: Color-coded lyrics with automatic line breaks
- ⚡ **Optimized Performance**: Efficient timing algorithm and resource management
- 🛠️ **Configurable**: Adjustable models, timing offsets, and display settings
- 🌍 **Multi-language Support**: Available through multilingual Whisper models

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **ffmpeg** (required for audio processing)

#### Installing ffmpeg:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

### Installation

```bash
# Clone or download the project
cd karaoke-player

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

**Basic usage:**
```bash
python karaoke_player.py
```

**Custom song:**
```python
config = Config(
    song_query="Queen Bohemian Rhapsody lyrics",
    whisper_model="small.en",  # Better accuracy
)
```

## 🎙️ Supported Whisper Models

The player supports all official Whisper models. Choose based on your accuracy needs and hardware capabilities:

### English-Only Models (Optimized for English)
| Model | Speed | Accuracy | RAM | Best For |
|-------|-------|----------|-----|----------|
| `tiny.en` | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1GB | Quick tests, low-end hardware |
| `base.en` | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1GB | **Default**, balanced performance |
| `small.en` | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2GB | High accuracy, recommended |
| `medium.en` | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5GB | Best English accuracy |

### Multilingual Models (99 Languages)
| Model | Speed | Accuracy | RAM | Best For |
|-------|-------|----------|-----|----------|
| `tiny` | ⚡⚡⚡⚡⚡ | ⭐⭐ | ~1GB | Quick multilingual tests |
| `base` | ⚡⚡⚡⚡ | ⭐⭐⭐ | ~1GB | Fast multilingual |
| `small` | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~2GB | Balanced multilingual |
| `medium` | ⚡⚡ | ⭐⭐⭐⭐⭐ | ~5GB | Accurate multilingual |
| `large-v1` | ⚡ | ⭐⭐⭐⭐⭐ | ~10GB | Very accurate (legacy) |
| `large-v2` | ⚡ | ⭐⭐⭐⭐⭐ | ~10GB | Improved accuracy (legacy) |
| `large-v3` | ⚡ | ⭐⭐⭐⭐⭐⭐ | ~10GB | Best overall accuracy |
| `large` | ⚡ | ⭐⭐⭐⭐⭐⭐ | ~10GB | Alias for latest large model |

### Turbo Models (New)
| Model | Speed | Accuracy | RAM | Best For |
|-------|-------|----------|-----|----------|
| `large-v3-turbo` | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~6GB | Fast + accurate multilingual |
| `turbo` | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ~6GB | Alias for large-v3-turbo |

### Model Selection Guide

**For English songs (recommended):**
- Start with `base.en` (default)
- Upgrade to `small.en` for better accuracy
- Use `medium.en` if you have powerful hardware

**For non-English songs:**
- Use `small` or `medium` for best results
- Try `turbo` for faster processing with good accuracy
- Use `large-v3` for maximum accuracy

**Hardware considerations:**
- **Low RAM (<4GB)**: Use `tiny` or `base` models
- **Medium RAM (4-8GB)**: Use `small` or `medium` models
- **High RAM (>8GB)**: Use `large` or `turbo` models

**Example configurations:**
```python
# High accuracy English
config = Config(
    song_query="Your song here",
    whisper_model="medium.en"
)

# Fast multilingual
config = Config(
    song_query="Your song here",
    whisper_model="turbo"
)

# Maximum accuracy (slow)
config = Config(
    song_query="Your song here",
    whisper_model="large-v3"
)
```

## ⚙️ Configuration Options

```python
@dataclass
class Config:
    song_query: str = "Your song here"
    
    # Whisper model - choose from complete list above
    whisper_model: str = "base.en"
    
    # Seconds of silence before new line
    new_line_threshold: float = 0.8
    
    # Audio quality (128, 192, 256, 320)
    audio_quality: str = "192"
    
    # Sync adjustment (positive = delay lyrics, negative = advance)
    timing_offset: float = 0.0
    
    # Auto-delete audio file after playing
    cleanup_on_exit: bool = True
    
    # Character-by-character display (typewriter effect)
    character_mode: bool = True
```

## 📊 Key Improvements Over Original

### 1. **Architecture**
- ✅ Class-based design for better organization
- ✅ Configuration dataclass with validation
- ✅ Context managers for proper resource cleanup
- ✅ Type hints throughout for better IDE support

### 2. **Performance**
- ✅ More accurate timing using `time.time()` instead of relying solely on pygame's `get_pos()`
- ✅ Model caching (loads once, reuses)
- ✅ Optimized pygame mixer settings
- ✅ Character-by-character display for dramatic effect

### 3. **Error Handling**
- ✅ Comprehensive try-catch blocks
- ✅ Graceful degradation
- ✅ Specific error messages with solutions
- ✅ Proper cleanup on all exit paths
- ✅ Model validation on startup

### 4. **Features**
- ✅ Timing offset adjustment for sync issues
- ✅ All 14 Whisper models supported
- ✅ Color-coded terminal output
- ✅ Better line break detection
- ✅ Video metadata display
- ✅ Typewriter effect for lyrics

### 5. **Code Quality**
- ✅ Proper logging instead of print statements
- ✅ PEP 8 compliant
- ✅ Docstrings for all functions
- ✅ No hardcoded values
- ✅ Complete model documentation

## 🐛 Troubleshooting

### "ffmpeg not found"
- Ensure ffmpeg is installed and in your PATH
- Test with: `ffmpeg -version`

### Lyrics ahead/behind audio
- Adjust `timing_offset` in config:
  - Positive value: delays lyrics
  - Negative value: advances lyrics
  - Try increments of 0.1 seconds

### Poor transcription quality
- Upgrade model: `whisper_model="small.en"` or `whisper_model="medium.en"`
- Use lyric videos (contain actual lyrics in audio)
- Ensure clear audio without excessive background noise
- Try `turbo` model for faster processing with good accuracy

### Out of memory
- Use smaller model: `whisper_model="tiny.en"` or `whisper_model="base"`
- Close other applications
- Reduce audio quality in config

### Model not found
- Ensure you're using a valid model name from the supported list
- First run will download the model (may take time)
- Check internet connection during first model download

## 🔧 Advanced Usage

### Using as a Module

```python
from karaoke_player import KaraokePlayer, Config

config = Config(
    song_query="Taylor Swift Shake It Off",
    whisper_model="small.en",
    timing_offset=-0.2  # Advance lyrics by 0.2s
)

player = KaraokePlayer(config)
player.run()
```

### Batch Processing

```python
songs = [
    "Imagine Dragons Believer",
    "Queen Bohemian Rhapsody",
    "Journey Don't Stop Believin"
]

for song in songs:
    config = Config(
        song_query=f"{song} lyrics",
        whisper_model="small.en"
    )
    player = KaraokePlayer(config)
    player.run()
```

### Multilingual Example

```python
# Spanish song
config = Config(
    song_query="Luis Fonsi Despacito",
    whisper_model="medium",  # Multilingual model
)

# French song with turbo model
config = Config(
    song_query="Edith Piaf La Vie en Rose",
    whisper_model="turbo",  # Fast multilingual
)
```

## 📝 Technical Details

### Timing Algorithm
The player uses a hybrid timing approach:
1. `time.time()` for primary timing (more accurate)
2. Word timestamps from Whisper AI
3. Character-level interpolation for smooth display
4. Configurable offset for manual adjustment
5. Gap detection for intelligent line breaks

### Why This Works Better
- Original code relied on `pygame.mixer.music.get_pos()` which can drift
- New approach uses system time for consistent accuracy
- Word-level timestamps from Whisper are highly accurate
- Character interpolation creates smooth typewriter effect
- Combined approach provides best of both worlds

### Model Download & Caching
- Models are automatically downloaded on first use
- Cached in `~/.cache/whisper/` for subsequent runs
- Model loading happens once per session
- Download times vary by model size (1-10GB)

## 🤝 Contributing

Suggestions for improvement:
- [ ] GUI interface with Qt or Tkinter
- [ ] Lyrics file export (SRT, LRC formats)
- [ ] Multiple language support in UI
- [ ] Karaoke scoring system with pitch detection
- [ ] Real-time pitch visualization
- [ ] Playlist support
- [ ] Custom color schemes

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Credits

- OpenAI Whisper for AI transcription
- yt-dlp for YouTube downloads
- pygame for audio playback

## ⚠️ Disclaimer

This tool is for personal use only. Respect copyright laws when downloading and using content. Always ensure you have the right to download and use any content.

---

**Made with ❤️ for karaoke enthusiasts**