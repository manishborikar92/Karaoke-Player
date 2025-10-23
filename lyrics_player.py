import pygame
import re
import time
import os

# --- Configuration ---
# !!! IMPORTANT: Change these two lines to point to your files !!!
SONG_MP3 = 'song.mp3'
LYRICS_LRC = 'song.lrc'
# ---------------------

def parse_lrc(filepath):
    """
    Parses an .lrc file and returns a sorted list of (time_in_seconds, text) tuples.
    """
    lyrics = []
    # Regex to capture [mm:ss.xx] timestamp and lyric text
    lrc_regex = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'

    if not os.path.exists(filepath):
        print(f"Error: Lyrics file not found at: {filepath}")
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            match = re.match(lrc_regex, line)
            if match:
                # Extract time components
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                # Handle 2 or 3 digit centiseconds/milliseconds
                centiseconds_str = match.group(3)
                if len(centiseconds_str) == 2:
                    centiseconds = int(centiseconds_str)
                else: # len is 3 (milliseconds)
                    centiseconds = int(centiseconds_str) / 10.0
                
                text = match.group(4).strip()
                
                # Calculate total time in seconds
                total_seconds = (minutes * 60) + seconds + (centiseconds / 100.0)
                
                if text: # Only add lines that have lyrics
                    lyrics.append((total_seconds, text))
            
    # Sort lyrics by time, as some LRC files can be out of order
    lyrics.sort()
    return lyrics

def play_song_with_lyrics(song_path, lrc_path):
    """
    Plays a song and prints synchronized lyrics to the console.
    """
    # 1. Load and parse the lyrics
    lyrics = parse_lrc(lrc_path)
    if lyrics is None:
        return # Error message already printed by parse_lrc

    if not lyrics:
        print("No valid lyric timestamps found in the file.")
        return

    # 2. Initialize Pygame mixer
    try:
        pygame.init()
        pygame.mixer.init()
    except Exception as e:
        print(f"Error initializing pygame: {e}")
        return

    # 3. Load and play the song
    if not os.path.exists(song_path):
        print(f"Error: Song file not found at: {song_path}")
        pygame.quit()
        return
        
    try:
        pygame.mixer.music.load(song_path)
        print(f"\n--- Playing: {os.path.basename(song_path)} ---")
        pygame.mixer.music.play()
    except pygame.error as e:
        print(f"Error playing audio file '{song_path}': {e}")
        pygame.quit()
        return

    # 4. Synchronization loop
    current_lyric_index = 0
    
    try:
        # Loop as long as the music is playing
        while pygame.mixer.music.get_busy():
            # Get current song time in seconds
            current_song_time_sec = pygame.mixer.music.get_pos() / 1000.0

            # Check if we have lyrics left to display
            if current_lyric_index < len(lyrics):
                next_lyric_time, next_lyric_text = lyrics[current_lyric_index]

                # Check if it's time to display the next lyric
                if current_song_time_sec >= next_lyric_time:
                    # Clear the console (optional, can be noisy)
                    # os.system('cls' if os.name == 'nt' else 'clear')
                    
                    print(f"\n🎤 {next_lyric_text}")
                    current_lyric_index += 1
            
            # Small delay to prevent 100% CPU usage
            time.sleep(0.05) # Check 20 times per second

        # Wait for the last bit of music to finish if lyrics end early
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping playback...")
        pygame.mixer.music.stop()
    
    finally:
        print("\n--- Song Finished ---")
        pygame.quit()

# --- Main execution ---
if __name__ == "__main__":
    play_song_with_lyrics(SONG_MP3, LYRICS_LRC)