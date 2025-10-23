# 🎤 AI-Powered Karaoke Lyrics Player

A sophisticated karaoke-style lyrics player that uses AI (OpenAI Whisper) to automatically transcribe and synchronize lyrics word-by-word with audio downloaded from YouTube.

## ✨ Features

- 🎵 **Automatic YouTube Download**: Fetches audio from any YouTube video
- 🤖 **AI Transcription**: Uses Whisper AI for accurate word-level timestamps
- 🎯 **Perfect Sync**: Word-by-word karaoke-style display
- 🎨 **Visual Feedback**: Color-coded lyrics with automatic line breaks
- ⚡ **Optimized Performance**: Efficient timing algorithm and resource management
- 🛠️ **Configurable**: Adjustable models, timing offsets, and display settings

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

## 📊 Key Improvements Over Original

### 1. **Architecture**
- ✅ Class-based design for better organization
- ✅ Configuration dataclass for easy customization
- ✅ Context managers for proper resource cleanup
- ✅ Type hints throughout for better IDE support

### 2. **Performance**
- ✅ More accurate timing using `time.time()` instead of relying solely on pygame's `get_pos()`
- ✅ Model caching (loads once, reuses)
- ✅ Optimized pygame mixer settings
- ✅ Configurable buffer sizes

### 3. **Error Handling**
- ✅ Comprehensive try-catch blocks
- ✅ Graceful degradation
- ✅ Specific error messages with solutions
- ✅ Proper cleanup on all exit paths

### 4. **Features**
- ✅ Timing offset adjustment for sync issues
- ✅ Configurable Whisper models (tiny → medium)
- ✅ Color-coded terminal output
- ✅ Better line break detection
- ✅ Video metadata display

### 5. **Code Quality**
- ✅ Proper logging instead of print statements
- ✅ PEP 8 compliant
- ✅ Docstrings for all functions
- ✅ No hardcoded values

## ⚙️ Configuration Options

```python
@dataclass
class Config:
    song_query: str = "Your song here"
    
    # Whisper model: tiny.en, base.en, small.en, medium.en
    # Larger = more accurate but slower
    whisper_model: str = "base.en"
    
    # Seconds of silence before new line
    new_line_threshold: float = 0.8
    
    # Audio quality (128, 192, 256, 320)
    audio_quality: str = "192"
    
    # Sync adjustment (positive = delay lyrics, negative = advance)
    timing_offset: float = 0.0
    
    # Auto-delete audio file after playing
    cleanup_on_exit: bool = True
```

## 🎯 Model Comparison

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| tiny.en | ⚡⚡⚡⚡ | ⭐⭐ | 1GB | Quick tests |
| base.en | ⚡⚡⚡ | ⭐⭐⭐ | 1GB | Default choice |
| small.en | ⚡⚡ | ⭐⭐⭐⭐ | 2GB | High accuracy |
| medium.en | ⚡ | ⭐⭐⭐⭐⭐ | 5GB | Best quality |

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
- Upgrade model: `whisper_model="small.en"`
- Use lyric videos (contain actual lyrics)
- Ensure clear audio without background noise

### Out of memory
- Use smaller model: `whisper_model="tiny.en"`
- Close other applications
- Reduce audio quality

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
    config = Config(song_query=f"{song} lyrics")
    player = KaraokePlayer(config)
    player.run()
```

## 📝 Technical Details

### Timing Algorithm
The player uses a hybrid timing approach:
1. `time.time()` for primary timing (more accurate)
2. Word timestamps from Whisper AI
3. Configurable offset for manual adjustment
4. Gap detection for intelligent line breaks

### Why This Works Better
- Original code relied on `pygame.mixer.music.get_pos()` which can drift
- New approach uses system time for consistent accuracy
- Word-level timestamps from Whisper are highly accurate
- Combined approach provides best of both worlds

## 🤝 Contributing

Suggestions for improvement:
- [ ] GUI interface
- [ ] Lyrics file export
- [ ] Multiple language support
- [ ] Karaoke scoring system
- [ ] Real-time pitch detection

## 📄 License

MIT License - feel free to use and modify!

## 🙏 Credits

- OpenAI Whisper for AI transcription
- yt-dlp for YouTube downloads
- pygame for audio playback

---

**Note**: This tool is for personal use only. Respect copyright laws when downloading and using content.
