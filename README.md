# 🎤 Karaoke Player Pro 2.0

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-PEP8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

A **professional-grade karaoke application** featuring AI-powered transcription, YouTube integration, and pixel-perfect lyrics synchronization. Built with modern Python practices following PEP 8 standards.

![Karaoke Player Demo](docs/demo.gif)

## ✨ Features

### 🎵 Core Features
- **AI-Powered Transcription**: Uses OpenAI Whisper for accurate word-level timestamps
- **YouTube Integration**: Download any song directly from YouTube
- **Character-by-Character Sync**: Dramatic typewriter effect that follows the vocalist
- **Word-by-Word Mode**: Traditional karaoke display
- **Smart Line Breaks**: Automatically detects pauses and creates natural line breaks
- **Intelligent Caching**: Never download or transcribe the same song twice

### 🎨 User Interface
- **Dual Interface**: Both CLI and GUI modes
- **Multiple Themes**: Dark, Light, Neon, and Classic
- **Customizable Display**: Adjust font size, colors, and timing
- **Progress Tracking**: Real-time progress for downloads and transcription
- **Responsive Controls**: Play, pause, stop with keyboard shortcuts

### ⚡ Performance
- **GPU Acceleration**: Automatic CUDA detection for 5-10x faster transcription
- **Model Caching**: Whisper model loads once and reuses
- **Background Threading**: UI remains responsive during long operations
- **Optimized Timing**: High-precision synchronization using system time

## 📋 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **FFmpeg**: Required for audio processing
- **RAM**: 2GB minimum (4GB recommended)
- **GPU** (Optional): NVIDIA GPU with CUDA for faster transcription

### Python Dependencies
```
yt-dlp>=2024.10.0
openai-whisper>=20231117
pygame>=2.5.0
torch>=2.0.0
PyYAML>=6.0.0
```

## 🚀 Quick Start

### Installation

#### 1. Install FFmpeg

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
1. Download from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH

**Verify installation:**
```bash
ffmpeg -version
```

#### 2. Install Karaoke Player

**From PyPI (when published):**
```bash
pip install karaoke-player-pro
```

**From Source:**
```bash
# Clone repository
git clone https://github.com/yourusername/karaoke-player.git
cd karaoke-player

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

### Usage

#### GUI Mode (Default)
```bash
python karaoke_player.py
# or simply
karaoke
```

#### CLI Mode
```bash
python karaoke_player.py --cli
# or
karaoke-cli
```

#### First Run
On first run, the application will:
1. Create necessary directories (`cache/`, `temp/`, `playlists/`)
2. Generate a default `config.yaml`
3. Download the Whisper model (~150MB for base.en)

## 📖 Usage Guide

### GUI Workflow

1. **Enter Song Name**: Type song name or YouTube URL
2. **Download**: Click "📥 Download" button
3. **Wait for Transcription**: AI processes the audio (1-3 minutes)
4. **Play Karaoke**: Click "▶️ Play" and sing along!

### CLI Workflow

1. **Run Application**: `python karaoke_player.py --cli`
2. **Enter Song**: Input song name when prompted
3. **Automatic Processing**: Download and transcription happen automatically
4. **Enjoy**: Lyrics appear in real-time!

### Configuration

Edit `config.yaml` to customize:

```yaml
# Choose display mode
display:
  mode: character  # or "word"
  theme: dark      # or "light", "neon", "classic"
  font_size: 24

# Choose Whisper model
transcription:
  model: base.en   # or "tiny.en", "small.en", "medium.en"

# Adjust timing if needed
timing_offset: 0.0  # positive=delay, negative=advance
```

## 🎯 Model Comparison

| Model | Size | Speed | Accuracy | Memory | Best For |
|-------|------|-------|----------|--------|----------|
| tiny.en | 75MB | ⚡⚡⚡⚡ | ⭐⭐ | 1GB | Quick tests |
| **base.en** | 150MB | ⚡⚡⚡ | ⭐⭐⭐ | 1GB | **Default choice** |
| small.en | 500MB | ⚡⚡ | ⭐⭐⭐⭐ | 2GB | High quality |
| medium.en | 1.5GB | ⚡ | ⭐⭐⭐⭐⭐ | 5GB | Best quality |

## 🔧 Advanced Features

### GPU Acceleration

For NVIDIA GPUs with CUDA:

```bash
# Uninstall CPU version
pip uninstall torch torchaudio

# Install GPU version
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU support
python -c "import torch; print(torch.cuda.is_available())"
```

**Speed improvement**: 5-10x faster transcription!

### Timing Adjustment

If lyrics appear ahead or behind the audio:

```yaml
# In config.yaml
timing_offset: 0.2  # Delay lyrics by 0.2 seconds
# or
timing_offset: -0.2  # Advance lyrics by 0.2 seconds
```

### Cache Management

```python
from src.core.downloader import YouTubeDownloader
from src.core.transcriber import Transcriber
from src.core.config import AppConfig

config = AppConfig()
downloader = YouTubeDownloader(config)
transcriber = Transcriber(config)

# Clear caches
downloader.clear_cache()
transcriber.clear_cache()
```

### Playlist Support (Coming Soon)

```python
# Future feature
from src.core.playlist import Playlist

playlist = Playlist("My Favorites")
playlist.add("Imagine Dragons Believer")
playlist.add("Queen Bohemian Rhapsody")
playlist.play()
```

## 🏗️ Architecture

### Project Structure
```
karaoke-player/
├── karaoke_player.py       # Main entry point
├── config.yaml             # Configuration
├── src/
│   ├── core/              # Business logic
│   │   ├── config.py      # Configuration management
│   │   ├── downloader.py  # YouTube downloader
│   │   ├── transcriber.py # AI transcription
│   │   └── player.py      # Audio player
│   ├── cli/               # CLI interface
│   └── gui/               # GUI interface
└── tests/                 # Unit tests
```

### Design Patterns
- **Separation of Concerns**: UI separate from business logic
- **Dependency Injection**: Config passed to all modules
- **Factory Pattern**: Model loading and caching
- **Observer Pattern**: Progress callbacks
- **Strategy Pattern**: Display modes and themes

## 🧪 Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# View coverage
open htmlcov/index.html
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Lint code
flake8 src/ tests/
pylint src/ tests/

# Type checking
mypy src/
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### "FFmpeg not found"
- Ensure FFmpeg is installed: `ffmpeg -version`
- Add FFmpeg to system PATH
- Restart terminal after installation

### Lyrics are out of sync
- Adjust `timing_offset` in `config.yaml`
- Try increments of 0.1 seconds
- Positive values delay lyrics, negative values advance them

### Poor transcription quality
- Use a better model: `model: small.en` or `medium.en`
- Search for "lyric video" versions
- Ensure clear audio without background noise

### Out of memory
- Use smaller model: `model: tiny.en` or `base.en`
- Close other applications
- Reduce audio quality in config

### Slow transcription
- Enable GPU acceleration (see above)
- Use smaller model
- Upgrade to faster CPU

## 📊 Performance Tips

1. **Use GPU acceleration** for 5-10x speed boost
2. **Enable caching** to avoid re-downloading
3. **Choose appropriate model**: base.en for most cases
4. **Prefer lyric videos**: Better transcription accuracy
5. **Adjust buffer size**: Lower latency vs CPU usage tradeoff

## 🔒 Privacy & Legal

- **No data collection**: Everything runs locally
- **Respect copyright**: For personal use only
- **YouTube ToS**: Follow YouTube's Terms of Service
- **Fair use**: Do not distribute copyrighted material

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **OpenAI Whisper**: AI transcription engine
- **yt-dlp**: YouTube download library
- **pygame**: Audio playback
- **Python community**: Amazing ecosystem

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/karaoke-player/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/karaoke-player/discussions)
- **Email**: support@karaoke-player.com

## 🗺️ Roadmap

- [ ] Web-based interface
- [ ] Mobile app (Android/iOS)
- [ ] Pitch detection and scoring
- [ ] Voice recording
- [ ] Social features (sharing, leaderboards)
- [ ] Multi-language support
- [ ] Custom backing tracks
- [ ] Real-time effects (reverb, echo)

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

---

**Made with ❤️ by the Karaoke Team**

[Website](https://karaoke-player.com) | [Documentation](https://docs.karaoke-player.com) | [Blog](https://blog.karaoke-player.com)
