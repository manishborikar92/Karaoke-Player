"""
YouTube audio downloader with caching and progress tracking.
"""

import hashlib
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YtDlpDownloadError

from .config import AppConfig, DownloadConfig
from .exceptions import DownloadError
from .logger import get_logger


logger = get_logger(__name__)


class ProgressHook:
    """Progress callback for downloads."""
    
    def __init__(self, callback: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.callback = callback
    
    def __call__(self, d: Dict[str, Any]) -> None:
        """Handle progress updates."""
        if d['status'] == 'downloading':
            if self.callback:
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                
                self.callback({
                    'percent': percent,
                    'speed': speed,
                    'eta': eta,
                    'downloaded': d.get('downloaded_bytes', 0),
                    'total': d.get('total_bytes', 0),
                })
        elif d['status'] == 'finished':
            if self.callback:
                self.callback({'status': 'finished'})


class YouTubeDownloader:
    """YouTube audio downloader with intelligent caching."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.download_config = config.download
        self.audio_config = config.audio
        self.cache_dir = config.cache_dir / "audio"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_cached_file(self, query: str) -> Optional[Path]:
        """Check if audio is already cached."""
        if not self.config.enable_cache:
            return None
        
        cache_key = self._generate_cache_key(query)
        audio_file = self.cache_dir / f"{cache_key}.{self.audio_config.format}"
        
        if audio_file.exists():
            logger.info(f"Found cached audio for: {query}")
            return audio_file
        
        return None
    
    def download(
        self,
        query: str,
        output_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Path:
        """
        Download audio from YouTube.
        
        Args:
            query: Search query or URL
            output_path: Optional output path (uses cache if None)
            progress_callback: Optional progress callback
            
        Returns:
            Path: Path to downloaded audio file
            
        Raises:
            DownloadError: If download fails
        """
        # Check cache first
        if output_path is None:
            cached = self._get_cached_file(query)
            if cached:
                return cached
            
            cache_key = self._generate_cache_key(query)
            output_path = self.cache_dir / cache_key
        
        logger.info(f"Downloading audio for: {query}")
        
        # Configure yt-dlp
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.audio_config.format,
                'preferredquality': self.audio_config.quality,
            }],
            'outtmpl': str(output_path),
            'default_search': self.download_config.default_search,
            'quiet': True,
            'noprogress': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'noplaylist': True,
        }
        
        # Add progress hook if callback provided
        if progress_callback:
            ydl_opts['progress_hooks'] = [ProgressHook(progress_callback)]
        
        # Prefer lyric videos if configured
        if self.download_config.prefer_lyric_video and not query.startswith('http'):
            query = f"{query} lyrics"
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                # Extract info
                info = ydl.extract_info(query, download=True)
                
                if not info:
                    raise DownloadError("Failed to extract video information")
                
                # Get video metadata
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                uploader = info.get('uploader', 'Unknown')
                
                logger.info(f"Downloaded: {title} ({duration}s) by {uploader}")
                
                # Verify file exists
                audio_file = Path(f"{output_path}.{self.audio_config.format}")
                if not audio_file.exists():
                    raise DownloadError("Audio file was not created")
                
                return audio_file
                
        except YtDlpDownloadError as e:
            logger.error(f"yt-dlp download error: {e}")
            raise DownloadError(f"Failed to download audio: {e}")
        except Exception as e:
            logger.error(f"Unexpected download error: {e}")
            raise DownloadError(f"Download failed: {e}")
    
    def get_video_info(self, query: str) -> Dict[str, Any]:
        """
        Get video information without downloading.
        
        Args:
            query: Search query or URL
            
        Returns:
            Dict: Video information
            
        Raises:
            DownloadError: If info extraction fails
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': self.download_config.default_search,
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                
                if not info:
                    raise DownloadError("Failed to extract video information")
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', ''),
                    'view_count': info.get('view_count', 0),
                    'url': info.get('webpage_url', ''),
                }
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            raise DownloadError(f"Info extraction failed: {e}")
    
    def clear_cache(self) -> int:
        """
        Clear all cached audio files.
        
        Returns:
            int: Number of files deleted
        """
        count = 0
        for file in self.cache_dir.glob(f"*.{self.audio_config.format}"):
            try:
                file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file}: {e}")
        
        logger.info(f"Cleared {count} cached audio files")
        return count


if __name__ == "__main__":
    # Demo usage
    from .config import AppConfig
    
    config = AppConfig()
    downloader = YouTubeDownloader(config)
    
    try:
        audio_file = downloader.download("Imagine Dragons Believer")
        print(f"Downloaded to: {audio_file}")
    except DownloadError as e:
        print(f"Error: {e}")
