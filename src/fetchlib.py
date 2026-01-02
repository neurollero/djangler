"""
Genius Lyrics Scraper - Modular ETL Pipeline
Fetches, parses, cleans, and saves song lyrics from Genius API
"""

import os
import re
import json
import time
from typing import Dict, List, Optional
import requests
import unicodedata
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import os
from dotenv import load_dotenv

load_dotenv()

# Genius API limit
MAX_DAILY_REQUESTS = 10000
API_PAUSE = 0.1

# Similarity threshold for fuzzy title match
TITLE_SIMILARITY = 0.7

# Path for the saved output with lyrics, metadata
OUTPUT_PATH = "songs_data.json"

# File with list of songs get lyrics from, output of spotifylib.save_song_list
SAVED_SONG_JSON = "songs_list_batch1.json"

# Test songs
TEST_SONGS = [
    ("Blinding Lights", "The Weeknd"),
    ("Bohemian Rhapsody", "Queen"),
    ("Old Town Road", "Lil Nas X"),
    ("Respect", "Aretha Franklin"),
    ("Smells Like Teen Spirit", "Nirvana"),
    ("God's Plan", "Drake"),
    ("Rolling in the Deep", "Adele"),
    ("Sweet Child O' Mine", "Guns N' Roses"),
    ("Levitating", "Dua Lipa"),
    ("Lose Yourself", "Eminem")
]


def fetch_lyrics(song_title: str, artist: str, access_token: str, timeout: int = 15) -> Optional[Dict]:
    """
    Fetch raw lyrics from Genius API
    
    Args:
        song_title: Title of the song
        artist: Artist name
        access_token: Genius API access token
        timeout: Request timeout in seconds (default: 15)
    
    Returns:
        Dict with 'lyrics' (raw text) and 'metadata' (title, artist, url, etc.)
        None if song not found
    """
    base_url = "https://api.genius.com"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Search for song
    search_url = f"{base_url}/search"
    params = {"q": f"{song_title} {artist}"}
    
    try:
        response = requests.get(search_url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        search_data = response.json()
        
        if not search_data['response']['hits']:
            print(f"No results found for '{song_title}' by {artist}")
            return None
        
        # Get first result
        song_info = search_data['response']['hits'][0]['result']
        song_url = song_info['url']
        
        # Scrape lyrics from song page
        page = requests.get(song_url, timeout=timeout)
        html = BeautifulSoup(page.text, 'html.parser')
        
        # Genius stores lyrics in div with specific data attribute
        lyrics_divs = html.find_all('div', {'data-lyrics-container': 'true'})
        
        if not lyrics_divs:
            print(f"Could not extract lyrics for '{song_title}'")
            return None
        
        # Combine all lyric divs and preserve line breaks
        raw_lyrics = '\n'.join([div.get_text(separator='\n') for div in lyrics_divs])
        
        metadata = {
            'title': song_info['title'],
            'artist': song_info['primary_artist']['name'],
            'url': song_url,
            'release_date': song_info.get('release_date_for_display'),
            'genius_id': song_info['id']
        }
        
        return {
            'lyrics': raw_lyrics,
            'metadata': metadata
        }
        
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout fetching '{song_title}' by {artist} - skipping")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print(f"⚠️  Rate limited on '{song_title}' - will retry")
            raise  # Re-raise to trigger retry logic in caller
        print(f"HTTP error fetching '{song_title}': {str(e)}")
        return None
    except Exception as e:
        print(f"Error fetching lyrics for '{song_title}': {str(e)}")
        return None


def parse_sections(raw_lyrics: str) -> List[Dict]:
    """
    Split lyrics into sections (verse, chorus, bridge, etc.)
    
    Args:
        raw_lyrics: Raw lyrics text with section headers like [Verse 1], [Chorus]
    
    Returns:
        List of dicts: [{'section_type': 'verse', 'section_number': 1, 'text': '...'}]
    """
    sections = []
    
    # Split by section headers (e.g., [Verse 1], [Chorus], [Bridge])
    # Pattern matches [Text] or [Text Number]
    section_pattern = r'\[([^\]]+)\]'
    parts = re.split(section_pattern, raw_lyrics)
    
    # parts will be: ['', 'Intro', 'lyrics...', 'Verse 1', 'lyrics...', 'Chorus', 'lyrics...']
    current_section = None
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
            
        # Check if this is a section header
        if i % 2 == 1:  # Odd indices are section headers (due to split behavior)
            current_section = part
        else:  # Even indices are lyrics
            if current_section and part:
                # Parse section type and number
                section_match = re.match(r'(.+?)\s*(\d+)?', current_section)
                if section_match:
                    section_type = section_match.group(1).lower().strip()
                    section_number = int(section_match.group(2)) if section_match.group(2) else None
                    
                    sections.append({
                        'section_type': section_type,
                        'section_number': section_number,
                        'text': part
                    })
    
    # If no sections found, treat entire lyrics as one section
    if not sections and raw_lyrics.strip():
        sections.append({
            'section_type': 'full',
            'section_number': None,
            'text': raw_lyrics.strip()
        })
    
    return sections


def clean_lyrics(text: str) -> str:
    """
    Clean lyrics text: remove annotations, extra whitespace, normalize
    
    Args:
        text: Raw lyrics text
    
    Returns:
        Cleaned lyrics text
    """
    # Remove text in parentheses (often production notes)
    text = re.sub(r'\([^)]*\)', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Normalize quotes
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace(''', "'").replace(''', "'")
    
    return text


def save_song_data(song_data: Dict, output_path: str = "songs_data.json"):
    """
    Save structured song data to JSON file
    
    Args:
        song_data: Dict with song information
        output_path: Path to output JSON file
    """
    # Load existing data if file exists
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            all_songs = json.load(f)
    else:
        all_songs = []
    
    # Add new song
    all_songs.append(song_data)
    
    # Save back to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_songs, f, indent=2, ensure_ascii=False)
    
    print(f"Saved '{song_data['metadata']['title']}' to {output_path}")


def normalize_title(text):
    """Normalize unicode characters for comparison"""
    text = unicodedata.normalize('NFKD', text)
    text = text.lower().strip()
    # Normalize apostrophes
    # text = text.replace("'", "'").replace("'", "'")
    text = re.sub(r"['`´'']", "", text)  # Remove all apostrophes
    # Remove feat. tags
    text = re.sub(r'\(feat\..*?\)', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_song(song_title: str, artist: str, access_token: str, 
                 output_path: str = "songs_data.json",
                 timeout: int = 15) -> Optional[Dict]:
    """
    Complete ETL pipeline for a single song
    
    Args:
        song_title: Title of the song
        artist: Artist name
        access_token: Genius API access token
        output_path: Path to save JSON output
        timeout: Request timeout in seconds (default: 15)
    
    Returns:
        Processed song data dict, or None if failed
    """
    # Check if already processed
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_songs = json.load(f)
            query_title_norm = normalize_title(song_title)
            query_artist_norm = artist.lower().strip()
            
            for song in existing_songs:
                existing_title_norm = normalize_title(song['metadata']['title'])
                existing_artist_norm = song['metadata']['artist'].lower().strip()
                
                if existing_title_norm == query_title_norm and existing_artist_norm == query_artist_norm:
                    print(f"Skipping: '{song_title}' already processed")
                    return None
    
    print(f"\nProcessing: '{song_title}' by {artist}")
    
    # 1. Fetch (with timeout)
    result = fetch_lyrics(song_title, artist, access_token, timeout=timeout)
    if not result:
        return None
    
    # 2. Verify Genius result matches our query
    genius_title_raw = result['metadata']['title']
    genius_artist_raw = result['metadata']['artist']
    
    query_title = normalize_title(song_title)
    genius_title = normalize_title(genius_title_raw)

    # Check artist match
    genius_artist = genius_artist_raw.lower().strip()
    if artist.lower().strip() not in genius_artist and genius_artist not in artist.lower().strip():
        print(f"Skipping: Wrong artist ({genius_artist_raw} != {artist})")
        return None
    
    # Check title match with fuzzy matching
    similarity = SequenceMatcher(None, query_title, genius_title).ratio()
    print(f"Fuzzy Similarity: {similarity:.3f}")
    
    if similarity < TITLE_SIMILARITY:
        print(f"Skipping: Genius returned '{genius_title_raw}' instead of '{song_title}'")
        return None
    
    raw_lyrics = result['lyrics']
    metadata = result['metadata']
    
    # 3. Parse sections
    sections = parse_sections(raw_lyrics)
    
    # 4. Clean each section
    for section in sections:
        section['text'] = clean_lyrics(section['text'])
    
    # 5. Structure data
    song_data = {
        'metadata': metadata,
        'sections': sections,
        'full_lyrics': clean_lyrics(raw_lyrics)
    }
    
    # 6. Save
    save_song_data(song_data, output_path)
    
    return song_data

def load_songs_as_tuples(json_path: str = "song_list.json") -> List[tuple]:
    """Load song list and convert to (title, artist) tuples"""
    with open(json_path, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    return [(song['title'], song['artist']) for song in songs]


# Example usage
if __name__ == "__main__":
    song_lyrics_to_get = load_songs_as_tuples(SAVED_SONG_JSON)
    
    # GENIUS_ACCESS_TOKEN = "-XneXPQ8TZn0D1Z6cGM_PtgeyN_WowjM65Raw2Ph0Hemn0G8a-HKSjP9CzCdW4fg"
    GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
    
    if GENIUS_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN_HERE":
        print("Please set your Genius API access token!")
    else:
        processed = 0
        skipped = 0
        
        for i, (title, artist) in enumerate(song_lyrics_to_get):
            # Progress tracking
            if i % 100 == 0 and i > 0:
                print(f"\n=== Progress: {i}/{len(song_lyrics_to_get)} (processed: {processed}, skipped: {skipped}) ===\n")
            
            # Rate limit handling
            try:
                result = process_song(title, artist, GENIUS_ACCESS_TOKEN, OUTPUT_PATH)
                if result:
                    processed += 1
                else:
                    skipped += 1
                    
                time.sleep(API_PAUSE)
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    print(f"\n⚠️  Rate limited. Pausing 60 seconds...\n")
                    time.sleep(60)
                    # Retry this song
                    result = process_song(title, artist, GENIUS_ACCESS_TOKEN, OUTPUT_PATH)
                    if result:
                        processed += 1
                else:
                    print(f"HTTP error: {e}")
                    skipped += 1
                    
            except Exception as e:
                print(f"Unexpected error: {e}")
                skipped += 1
        
        print(f"\n✓ Complete! Processed: {processed}, Skipped: {skipped}")