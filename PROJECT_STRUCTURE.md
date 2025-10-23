# Karaoke Player Pro 2.0 - Project Structure

## 📁 Directory Layout (PEP 8 Compliant)

```
karaoke-player/
├── karaoke_player.py          # Main entry point
├── config.yaml                # Configuration file
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── README.md                  # Documentation
├── LICENSE                    # MIT License
│
├── src/                       # Source code
│   ├── __init__.py
│   │
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration management
│   │   ├── logger.py          # Logging system
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── downloader.py      # YouTube downloader
│   │   ├── transcriber.py     # AI transcription
│   │   └── player.py          # Audio player & sync
│   │
│   ├── cli/                   # CLI interface
│   │   ├── __init__.py
│   │   └── interface.py       # CLI implementation
│   │
│   └── gui/                   # GUI interface
│       ├── __init__.py
│       ├── application.py     # Main GUI app
│       └── widgets.py         # Custom widgets (future)
│
├── tests/                     # Unit tests
│   ├── __init__.py
│   ├── test_downloader.py
│   ├── test_transcriber.py
│   └── test_player.py
│
├── cache/                     # Cache directory (auto-created)
│   ├── audio/                 # Cached audio files
│   └── transcriptions/        # Cached transcriptions
│
├── temp/                      # Temporary files (auto-created)
├── playlists/                 # User playlists (auto-created)
├── logs/                      # Log files (auto-created)
│
└── docs/                      # Documentation
    ├── API.md                 # API documentation
    ├── CONTRIBUTING.md        # Contribution guide
    └── CHANGELOG.md           # Version history
```

## 📄 File Descriptions

### Root Level

- **karaoke_player.py**: Main entry point, handles CLI/GUI mode selection
- **config.yaml**: User configuration (auto-generated on first run)
- **requirements.txt**: All Python dependencies
- **setup.py**: Package installation and distribution

### src/core/

Core business logic, independent of UI:

- **config.py**: Configuration dataclasses and management
- **logger.py**: Centralized logging with colors and emojis
- **exceptions.py**: Custom exception hierarchy
- **downloader.py**: YouTube download with caching
- **transcriber.py**: Whisper AI integration with word timestamps
- **player.py**: Audio playback and lyrics synchronization

### src/cli/

Command-line interface:

- **interface.py**: Terminal-based karaoke player with colors

### src/gui/

Graphical user interface:

- **application.py**: tkinter-based GUI application
- **widgets.py**: Custom widgets (for future expansion)

### tests/

Unit tests using pytest:

- Test coverage for all core modules
- Integration tests for workflows
- Mock tests for external dependencies

## 🔧 Module Dependencies

```
karaoke_player.py
    ├── src.core.config
    ├── src.core.logger
    ├── src.cli.interface (if --cli)
    └── src.gui.application (if --gui)

src.cli.interface
    ├── src.core.downloader
    ├── src.core.transcriber
    └── src.core.player

src.gui.application
    ├── src.core.downloader
    ├── src.core.transcriber
    └── src.core.player

src.core.downloader
    ├── src.core.config
    ├── src.core.exceptions
    └── yt_dlp (external)

src.core.transcriber
    ├── src.core.config
    ├── src.core.exceptions
    └── whisper (external)

src.core.player
    ├── src.core.config
    ├── src.core.exceptions
    └── pygame (external)
```

## 🎯 Design Patterns Used

### 1. **Separation of Concerns**
- UI layer (CLI/GUI) separate from business logic (core)
- Easy to add new interfaces (web, mobile)

### 2. **Dependency Injection**
- All modules receive `AppConfig` in constructor
- Makes testing and configuration easier

### 3. **Factory Pattern**
- Configuration loading with defaults
- Model loading with caching

### 4. **Observer Pattern**
- Progress callbacks for long operations
- Event-driven UI updates

### 5. **Singleton Pattern**
- Logger instances (via `get_logger()`)
- Model caching in transcriber

### 6. **Strategy Pattern**
- Different display modes (word/character)
- Different themes (dark/light/neon)

## 🚀 Running the Application

### CLI Mode
```bash
python karaoke_player.py --cli
```

### GUI Mode (Default)
```bash
python karaoke_player.py
# or
python karaoke_player.py --gui
```

### As a Module
```python
from src.core.config import AppConfig
from src.gui.application import GUIApplication

config = AppConfig()
app = GUIApplication(config)
app.run()
```

## 📦 Installation

### Development Installation
```bash
# Clone repository
git clone https://github.com/yourusername/karaoke-player.git
cd karaoke-player

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### User Installation
```bash
pip install karaoke-player-pro
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_downloader.py
```

## 📝 Configuration

Configuration is managed through `config.yaml`:

```yaml
# Audio settings
audio:
  quality: "192"
  sample_rate: 44100
  buffer_size: 512

# Transcription settings
transcription:
  model: "base.en"
  language: "en"

# Display settings
display:
  mode: "character"
  theme: "dark"
  font_size: 24
  new_line_threshold: 0.8

# General settings
auto_cleanup: true
timing_offset: 0.0
enable_cache: true
```

## 🔌 Extensibility

### Adding New Display Modes

1. Add enum to `src/core/config.py`:
```python
class DisplayMode(Enum):
    YOUR_MODE = "your_mode"
```

2. Implement in `src/core/player.py`:
```python
def get_current_items(self, position):
    if self.mode == DisplayMode.YOUR_MODE:
        # Your implementation
        pass
```

### Adding New Themes

1. Add enum to `src/core/config.py`
2. Update `_apply_theme()` in GUI/CLI

### Adding New Features

- **Playlist support**: Extend `src/core/player.py`
- **Scoring system**: Add new module `src/core/scorer.py`
- **Recording**: Add new module `src/core/recorder.py`
- **Web interface**: Create `src/web/` directory

## 📊 Performance Considerations

- **Caching**: Both audio and transcriptions are cached
- **Lazy loading**: Whisper model loaded only when needed
- **Threading**: Long operations run in background threads
- **Memory**: Model is loaded once and reused
- **GPU**: Automatic CUDA detection for faster transcription

## 🔒 Security

- Input validation on all user inputs
- Path sanitization for file operations
- No code execution from external sources
- Proper exception handling throughout

## 📄 License

MIT License - See LICENSE file for details
