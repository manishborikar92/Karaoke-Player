import os
import re
import time
import subprocess
import pygame
from yt_dlp import YoutubeDL
import whisper
import requests
from fuzzywuzzy import process
from bs4 import BeautifulSoup 

# --- Configuration ---
# CHANGED SONG to find a working video
SONG_QUERY = "Imagine Dragons Believer lyric video" 

# !! FIXED THE FILENAME BUG HERE !!
AUDIO_FILENAME = "temp_audio.mp3"  # The final filename we want
AUDIO_FILE_BASE = "temp_audio"     # The base name we give to yt-dlp
LYRICS_FILE = "temp_lyrics.txt" 
# ---------------------

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- MANUAL LYRIC FUNCTION ---
def get_lyrics_manually(query, token):
    api_query = query.replace("lyric video", "").strip()
    print(f"[1/5] 🕵️ Searching for lyrics for '{api_query}' on Genius...")
    try:
        SEARCH_URL = "https://api.genius.com/search"
        headers = {'Authorization': f'Bearer {token}'}
        params = {'q': api_query}
        
        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=10)
        json_data = response.json()

        if response.status_code != 200 or json_data.get('meta', {}).get('status') != 200:
            print(f"❌ API Error: {json_data.get('meta', {}).get('message', 'Unknown error')}")
            return None
        
        hits = json_data.get('response', {}).get('hits', [])
        if not hits:
            print("❌ Lyrics not found on Genius.")
            return None
            
        song_path = hits[0]['result']['path']
        full_title = hits[0]['result']['full_title']
        print(f"✅ Found: {full_title}")
        print(f"[1.5/5] 🕸️ Scraping lyrics from song page...")

        page_url = f"https://genius.com{song_path}"
        scraper_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        page_response = requests.get(page_url, headers=scraper_headers, timeout=10)
        
        if page_response.status_code != 200:
            print(f"❌ Failed to scrape lyrics page (Status: {page_response.status_code})")
            return None

        soup = BeautifulSoup(page_response.text, 'html.parser')
        lyric_containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        
        if not lyric_containers:
            print("❌ Could not find lyrics on page. Genius may have updated its layout.")
            return None

        lyrics = ""
        for container in lyric_containers:
            lyrics += container.get_text(separator="\n") + "\n"
        
        lyrics = os.linesep.join([s for s in lyrics.splitlines() if s.strip()])

        with open(LYRICS_FILE, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        
        return lyrics.splitlines()

    except requests.exceptions.Timeout:
        print("❌ Connection to Genius.com timed out.")
        return None
    except Exception as e:
        print(f"❌ Error scraping lyrics: {e}")
        return None

# --- YOUTUBE DOWNLOAD FUNCTION ---
def download_youtube_audio(query):
    print(f"[2/5] 📥 Downloading audio for '{query}'...")
    
    if os.path.exists(AUDIO_FILENAME):
        os.remove(AUDIO_FILENAME)

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # !! FIXED: Use the base name, so postprocessor adds ".mp3" correctly
        'outtmpl': AUDIO_FILE_BASE, 
        'default_search': 'ytsearch',
        'quiet': True,
        'noprogress': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([query])
        
        # !! FIXED: Check for the correct final filename
        if not os.path.exists(AUDIO_FILENAME):
             raise RuntimeError("Audio file was not created.")
             
        print(f"✅ Audio saved to {AUDIO_FILENAME}")
        return True
    except Exception as e:
        print(f"❌ Error downloading audio: {e}")
        return False

# --- AI TRANSCRIPTION FUNCTION ---
def transcribe_with_ai(audio_file):
    print("[3/5] 🤖 Transcribing audio with AI (this may take a minute)...")
    try:
        model = whisper.load_model("tiny.en") 
        result = model.transcribe(audio_file, verbose=False)
        
        ai_lines = []
        for segment in result['segments']:
            ai_lines.append((segment['start'], segment['text'].strip()))
        
        print(f"✅ AI transcription complete.")
        return ai_lines
    except Exception as e:
        print(f"❌ Error during AI transcription: {e}")
        if "No such file or directory: 'ffmpeg'" in str(e):
            print("FATAL ERROR: ffmpeg is not installed or not in your PATH.")
        return None

# --- LYRIC ALIGNMENT FUNCTION ---
def align_lyrics(clean_lyrics, ai_lyrics):
    print("[4/5] 🧠 Aligning lyrics...")
    
    synced_lyrics = []
    ai_text_list = [text for time, text in ai_lyrics]
    
    for clean_line in clean_lyrics:
        if not clean_line.strip():
            continue
            
        best_match, score = process.extractOne(clean_line, ai_text_list)
        
        if score > 70:
            for ai_time, ai_text in ai_lyrics:
                if ai_text == best_match:
                    synced_lyrics.append((ai_time, clean_line))
                    if (ai_time, ai_text) in ai_lyrics:
                        ai_lyrics.remove((ai_time, ai_text))
                    if ai_text in ai_text_list:
                        ai_text_list.remove(ai_text)
                    break
        
    synced_lyrics.sort()
    
    if not synced_lyrics:
        print("❌ Alignment failed. No matches found.")
        return None
        
    print(f"✅ Alignment successful. {len(synced_lyrics)} lines synced.")
    return synced_lyrics

# --- PYGAME PLAYER FUNCTION ---
def play_synced_song(audio_file, synced_lyrics):
    print("\n[5/5] 🚀 Starting playback...")
    time.sleep(2)
    clear_console()

    pygame.init()
    pygame.mixer.init()

    try:
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
    except pygame.error as e:
        print(f"❌ Error playing audio: {e}")
        pygame.quit()
        return

    current_lyric_index = 0
    start_time = time.time()
    
    try:
        while pygame.mixer.music.get_busy() and current_lyric_index < len(synced_lyrics):
            current_song_time_sec = pygame.mixer.music.get_pos() / 1000.0
            next_lyric_time, next_lyric_text = synced_lyrics[current_lyric_index]

            if current_song_time_sec >= next_lyric_time:
                clear_console()
                
                if current_lyric_index > 1:
                    print(f"  {synced_lyrics[current_lyric_index-2][1]}")
                if current_lyric_index > 0:
                    print(f"  {synced_lyrics[current_lyric_index-1][1]}")

                print(f"\n🎤 ** {next_lyric_text} **\n")
                
                current_lyric_index += 1
            
            time.sleep(0.05)

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopping...")
        pygame.mixer.music.stop()
    
    finally:
        print("\n--- Song Finished ---")
        pygame.quit()
        # !! FIXED: Clean up the correct filename
        if os.path.exists(AUDIO_FILENAME):
            os.remove(AUDIO_FILENAME)
        if os.path.exists(LYRICS_FILE):
            os.remove(LYRICS_FILE)

# --- Main Execution ---
if __name__ == "__main__":
    
    GENIUS_API_TOKEN = "2eQ4C0UIkhJe4M_BZpF2zbNU0I3NC8FjUgwVaM-qu8pvvfHyqGydFh3f75Ef6tae" 
    
    
    clean_lyrics = get_lyrics_manually(SONG_QUERY, GENIUS_API_TOKEN)
    if not clean_lyrics:
        exit()
    
    # !! FIXED: Pass the correct filename to all functions
    if not download_youtube_audio(SONG_QUERY):
        exit()
        
    ai_lyrics = transcribe_with_ai(AUDIO_FILENAME)
    if not ai_lyrics:
        exit()
        
    synced_lyrics = align_lyrics(clean_lyrics, ai_lyrics)
    if not synced_lyrics:
        exit()

    play_synced_song(AUDIO_FILENAME, synced_lyrics)