"""
Setup script for Karaoke Player Pro.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r') as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.startswith('#') and not line.startswith('=')
        ]

setup(
    name="karaoke-player-pro",
    version="2.0.0",
    author="Karaoke Team",
    author_email="team@karaoke-player.com",
    description="Professional karaoke player with AI-powered lyrics synchronization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/karaoke-player",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/karaoke-player/issues",
        "Documentation": "https://karaoke-player.readthedocs.io",
        "Source Code": "https://github.com/yourusername/karaoke-player",
    },
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: X11 Applications",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "pylint>=3.0.0",
            "mypy>=1.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
        "gpu": [
            # GPU-accelerated PyTorch for faster transcription
            # Install manually: pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
        ],
    },
    entry_points={
        "console_scripts": [
            "karaoke=karaoke_player:main",
            "karaoke-cli=karaoke_player:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json"],
    },
    keywords=[
        "karaoke",
        "lyrics",
        "music",
        "audio",
        "youtube",
        "transcription",
        "whisper",
        "ai",
        "synchronization",
        "player",
    ],
    zip_safe=False,
)