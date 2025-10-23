"""
Graphical user interface for Karaoke Player using tkinter.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from pathlib import Path
from typing import Optional

from ..core.config import AppConfig, DisplayMode, WhisperModel
from ..core.downloader import YouTubeDownloader
from ..core.transcriber import Transcriber, Transcription
from ..core.player import AudioPlayer, LyricsSync
from ..core.exceptions import KaraokeError
from ..core.logger import get_logger


logger = get_logger(__name__)


class GUIApplication:
    """Main GUI application class."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.downloader = YouTubeDownloader(config)
        self.transcriber = Transcriber(config)
        self.player = AudioPlayer(config)
        
        self.root: Optional[tk.Tk] = None
        self.current_transcription: Optional[Transcription] = None
        self.current_audio_file: Optional[Path] = None
        self.lyrics_sync: Optional[LyricsSync] = None
        self.is_playing = False
        self.playback_thread: Optional[threading.Thread] = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the main UI window."""
        self.root = tk.Tk()
        self.root.title("Karaoke Player Pro 2.0")
        self.root.geometry(f"{self.config.display.window_width}x{self.config.display.window_height}")
        
        # Configure theme
        self._apply_theme()
        
        # Create main layout
        self._create_menu()
        self._create_control_panel()
        self._create_lyrics_display()
        self._create_status_bar()
        
        # Protocol handlers
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _apply_theme(self) -> None:
        """Apply visual theme."""
        # Configure colors based on theme
        if self.config.display.theme.value == "dark":
            bg_color = "#1e1e1e"
            fg_color = "#ffffff"
            accent_color = "#00d4ff"
        elif self.config.display.theme.value == "light":
            bg_color = "#ffffff"
            fg_color = "#000000"
            accent_color = "#0066cc"
        elif self.config.display.theme.value == "neon":
            bg_color = "#0a0a0a"
            fg_color = "#00ff00"
            accent_color = "#ff00ff"
        else:  # classic
            bg_color = "#f0f0f0"
            fg_color = "#000000"
            accent_color = "#3366cc"
        
        self.root.configure(bg=bg_color)
        
        # Store theme colors
        self.theme_colors = {
            'bg': bg_color,
            'fg': fg_color,
            'accent': accent_color,
        }
    
    def _create_menu(self) -> None:
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Audio File", command=self._open_audio_file)
        file_menu.add_separator()
        file_menu.add_command(label="Clear Cache", command=self._clear_cache)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Preferences", command=self._show_preferences)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_control_panel(self) -> None:
        """Create control panel."""
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X, side=tk.TOP)
        
        # Search input
        ttk.Label(control_frame, text="Song:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.search_var = tk.StringVar(value="Imagine Dragons Believer lyrics")
        search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=50)
        search_entry.grid(row=0, column=1, columnspan=3, sticky=tk.EW, padx=5)
        
        # Buttons
        self.download_btn = ttk.Button(
            control_frame,
            text="📥 Download",
            command=self._download_song
        )
        self.download_btn.grid(row=1, column=0, padx=5, pady=10)
        
        self.play_btn = ttk.Button(
            control_frame,
            text="▶️ Play",
            command=self._toggle_playback,
            state=tk.DISABLED
        )
        self.play_btn.grid(row=1, column=1, padx=5, pady=10)
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="⏹️ Stop",
            command=self._stop_playback,
            state=tk.DISABLED
        )
        self.stop_btn.grid(row=1, column=2, padx=5, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            control_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=2, column=0, columnspan=4, sticky=tk.EW, padx=5, pady=5)
        
        control_frame.columnconfigure(1, weight=1)
    
    def _create_lyrics_display(self) -> None:
        """Create lyrics display area."""
        # Frame
        lyrics_frame = ttk.Frame(self.root)
        lyrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text widget with scrollbar
        scrollbar = ttk.Scrollbar(lyrics_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lyrics_text = tk.Text(
            lyrics_frame,
            wrap=tk.WORD,
            font=('Arial', self.config.display.font_size),
            bg=self.theme_colors['bg'],
            fg=self.theme_colors['fg'],
            insertbackground=self.theme_colors['accent'],
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED
        )
        self.lyrics_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.lyrics_text.yview)
        
        # Configure tags for styling
        self.lyrics_text.tag_configure(
            "current",
            foreground=self.theme_colors['accent'],
            font=('Arial', self.config.display.font_size, 'bold')
        )
    
    def _create_status_bar(self) -> None:
        """Create status bar."""
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(
            self.root,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _update_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def _append_lyrics(self, text: str, is_newline: bool = False) -> None:
        """Append text to lyrics display."""
        self.lyrics_text.config(state=tk.NORMAL)
        
        if is_newline:
            self.lyrics_text.insert(tk.END, "\n")
        else:
            self.lyrics_text.insert(tk.END, text, "current")
        
        self.lyrics_text.see(tk.END)
        self.lyrics_text.config(state=tk.DISABLED)
    
    def _clear_lyrics(self) -> None:
        """Clear lyrics display."""
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete(1.0, tk.END)
        self.lyrics_text.config(state=tk.DISABLED)
    
    def _download_song(self) -> None:
        """Download song in background thread."""
        query = self.search_var.get().strip()
        
        if not query:
            messagebox.showwarning("Input Required", "Please enter a song name or URL")
            return
        
        # Disable controls
        self.download_btn.config(state=tk.DISABLED)
        self._update_status("Downloading...")
        self.progress_var.set(0)
        
        def download_task():
            try:
                def progress_callback(info):
                    if 'percent' in info:
                        try:
                            percent_str = info['percent'].replace('%', '')
                            progress = float(percent_str)
                            self.root.after(0, lambda: self.progress_var.set(progress))
                        except ValueError:
                            pass
                
                audio_file = self.downloader.download(query, progress_callback=progress_callback)
                self.current_audio_file = audio_file
                
                self.root.after(0, lambda: self._update_status("Download complete. Transcribing..."))
                self.root.after(0, lambda: self.progress_var.set(0))
                
                # Transcribe
                def transcribe_callback(stage, progress):
                    self.root.after(0, lambda: self._update_status(f"Transcribing: {stage}"))
                    self.root.after(0, lambda: self.progress_var.set(progress * 100))
                
                transcription = self.transcriber.transcribe(
                    audio_file,
                    progress_callback=transcribe_callback
                )
                self.current_transcription = transcription
                
                self.root.after(0, self._on_download_complete)
                
            except KaraokeError as e:
                logger.error(f"Download/transcription failed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.root.after(0, lambda: self.download_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self._update_status("Ready"))
        
        thread = threading.Thread(target=download_task, daemon=True)
        thread.start()
    
    def _on_download_complete(self) -> None:
        """Handle download completion."""
        self.download_btn.config(state=tk.NORMAL)
        self.play_btn.config(state=tk.NORMAL)
        self._update_status("Ready to play")
        self.progress_var.set(100)
        
        messagebox.showinfo(
            "Success",
            f"Downloaded and transcribed!\n"
            f"Words: {len(self.current_transcription.words)}\n"
            f"Duration: {self.current_transcription.duration:.1f}s"
        )
    
    def _toggle_playback(self) -> None:
        """Toggle play/pause."""
        if not self.current_audio_file or not self.current_transcription:
            messagebox.showwarning("No Song", "Please download a song first")
            return
        
        if self.is_playing:
            self._pause_playback()
        else:
            self._start_playback()
    
    def _start_playback(self) -> None:
        """Start karaoke playback."""
        if self.playback_thread and self.playback_thread.is_alive():
            return
        
        self.is_playing = True
        self.play_btn.config(text="⏸️ Pause")
        self.stop_btn.config(state=tk.NORMAL)
        self._clear_lyrics()
        self._update_status("Playing...")
        
        def playback_task():
            try:
                self.player.load(self.current_audio_file)
                self.player.play()
                
                self.lyrics_sync = LyricsSync(self.config, self.current_transcription)
                last_position = 0.0
                
                while self.player.is_playing() and self.is_playing:
                    position = self.player.get_position()
                    
                    if position > last_position:
                        items = self.lyrics_sync.get_current_items(position)
                        
                        for text, is_newline in items:
                            self.root.after(0, lambda t=text, n=is_newline: self._append_lyrics(t, n))
                        
                        last_position = position
                    
                    threading.Event().wait(self.config.display.character_delay)
                
                self.root.after(0, self._on_playback_finished)
                
            except Exception as e:
                logger.exception("Playback error")
                self.root.after(0, lambda: messagebox.showerror("Playback Error", str(e)))
                self.root.after(0, self._stop_playback)
        
        self.playback_thread = threading.Thread(target=playback_task, daemon=True)
        self.playback_thread.start()
    
    def _pause_playback(self) -> None:
        """Pause playback."""
        self.player.pause()
        self.is_playing = False
        self.play_btn.config(text="▶️ Resume")
        self._update_status("Paused")
    
    def _stop_playback(self) -> None:
        """Stop playback."""
        self.is_playing = False
        self.player.stop()
        self.play_btn.config(text="▶️ Play")
        self.stop_btn.config(state=tk.DISABLED)
        self._update_status("Stopped")
        
        if self.lyrics_sync:
            self.lyrics_sync.reset()
    
    def _on_playback_finished(self) -> None:
        """Handle playback completion."""
        self.is_playing = False
        self.play_btn.config(text="▶️ Play")
        self.stop_btn.config(state=tk.DISABLED)
        self._update_status("Finished")
        
        self._append_lyrics("\n\n✨ --- Song Finished --- ✨", False)
    
    def _open_audio_file(self) -> None:
        """Open audio file dialog."""
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.flac"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            messagebox.showinfo("Feature", "Direct audio file loading will be implemented soon!")
    
    def _clear_cache(self) -> None:
        """Clear all caches."""
        result = messagebox.askyesno(
            "Clear Cache",
            "This will delete all cached audio and transcriptions.\nContinue?"
        )
        
        if result:
            audio_count = self.downloader.clear_cache()
            trans_count = self.transcriber.clear_cache()
            
            messagebox.showinfo(
                "Cache Cleared",
                f"Deleted:\n"
                f"• {audio_count} audio files\n"
                f"• {trans_count} transcriptions"
            )
    
    def _show_preferences(self) -> None:
        """Show preferences dialog."""
        pref_window = tk.Toplevel(self.root)
        pref_window.title("Preferences")
        pref_window.geometry("500x400")
        
        notebook = ttk.Notebook(pref_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Display tab
        display_frame = ttk.Frame(notebook)
        notebook.add(display_frame, text="Display")
        
        ttk.Label(display_frame, text="Display Mode:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        mode_var = tk.StringVar(value=self.config.display.mode.value)
        mode_combo = ttk.Combobox(
            display_frame,
            textvariable=mode_var,
            values=["word", "character"],
            state="readonly"
        )
        mode_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(display_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        font_size_var = tk.IntVar(value=self.config.display.font_size)
        font_size_spin = ttk.Spinbox(display_frame, from_=12, to=48, textvariable=font_size_var)
        font_size_spin.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Transcription tab
        trans_frame = ttk.Frame(notebook)
        notebook.add(trans_frame, text="Transcription")
        
        ttk.Label(trans_frame, text="Whisper Model:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        model_var = tk.StringVar(value=self.config.transcription.model.value)
        model_combo = ttk.Combobox(
            trans_frame,
            textvariable=model_var,
            values=["tiny.en", "base.en", "small.en", "medium.en"],
            state="readonly"
        )
        model_combo.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Save button
        def save_preferences():
            from ..core.config import DisplayMode, WhisperModel
            
            self.config.display.mode = DisplayMode(mode_var.get())
            self.config.display.font_size = font_size_var.get()
            self.config.transcription.model = WhisperModel(model_var.get())
            
            # Update font size
            self.lyrics_text.config(font=('Arial', self.config.display.font_size))
            
            messagebox.showinfo("Saved", "Preferences updated successfully!")
            pref_window.destroy()
        
        ttk.Button(pref_window, text="Save", command=save_preferences).pack(pady=10)
    
    def _show_about(self) -> None:
        """Show about dialog."""
        about_text = """
Karaoke Player Pro 2.0

A professional karaoke application with:
• AI-powered transcription (Whisper)
• YouTube integration
• Character-by-character synchronization
• Multiple themes and display modes

Powered by:
• OpenAI Whisper
• yt-dlp
• pygame

© 2025 Karaoke Team
MIT License
"""
        messagebox.showinfo("About", about_text)
    
    def _on_closing(self) -> None:
        """Handle window closing."""
        if self.is_playing:
            result = messagebox.askyesno(
                "Confirm Exit",
                "Playback is active. Are you sure you want to exit?"
            )
            if not result:
                return
        
        self.is_playing = False
        self.player.cleanup()
        
        # Cleanup temp files
        if self.config.auto_cleanup and self.current_audio_file:
            if self.current_audio_file.exists():
                try:
                    self.current_audio_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to cleanup audio file: {e}")
        
        self.root.quit()
        self.root.destroy()
    
    def run(self) -> int:
        """
        Run the GUI application.
        
        Returns:
            int: Exit code
        """
        try:
            self.root.mainloop()
            return 0
        except Exception as e:
            logger.exception("GUI error")
            messagebox.showerror("Error", f"Application error: {e}")
            return 1


if __name__ == "__main__":
    from ..core.config import AppConfig
    
    config = AppConfig()
    app = GUIApplication(config)
    app.run()
