"""
Enrich songs_data.json with Spotify genres
Adds genre metadata to the consolidated source of truth
"""

import json
import time
from typing import List, Dict
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from collections import Counter

SPOTIFY_CLIENT_ID = "dc02e1a590e344558af75713c5f95e02"
SPOTIFY_CLIENT_SECRET = "921349166f544ae88d4f599b4f72b5dc"


def setup_spotify(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET):
    """Initialize Spotify client"""
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_artist_info(sp: spotipy.Spotify, artist_name: str) -> Dict:
    """Get genres and popularity for an artist"""
    try:
        results = sp.search(q=f"artist:{artist_name}", type='artist', limit=1)
        if results['artists']['items']:
            artist = results['artists']['items'][0]
            return {
                'genres': artist['genres'],
                'popularity': artist.get('popularity', 0)
            }
    except Exception as e:
        print(f"Error getting info for {artist_name}: {e}")
    return {'genres': [], 'popularity': 0}


def enrich_songs_data(input_path: str = "songs_data.json", 
                      output_path: str = None,
                      save_frequency: int = 100):
    """
    Add genres to songs_data.json
    
    Args:
        input_path: Path to songs_data.json
        output_path: Output path (default: overwrites input)
        save_frequency: Save progress every N songs
    """
    if output_path is None:
        output_path = input_path
    
    sp = setup_spotify()
    
    with open(input_path, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    print(f"Loaded {len(songs)} songs from {input_path}")
    
    # Check if already have genres
    already_enriched = sum(1 for s in songs if s.get('metadata', {}).get('genres'))
    print(f"Already enriched: {already_enriched}/{len(songs)}")
    
    artist_cache = {}  # Cache to avoid duplicate lookups
    updated_count = 0
    
    for i, song in enumerate(songs):
        metadata = song.get('metadata', {})
        artist = metadata.get('artist', 'Unknown')
        
        # Skip if already has genres
        if metadata.get('genres'):
            continue
        
        # Get artist info (genres + popularity)
        if artist not in artist_cache:
            artist_cache[artist] = get_artist_info(sp, artist)
            time.sleep(0.1)  # Rate limiting
        
        artist_info = artist_cache[artist]
        metadata['genres'] = artist_info['genres']
        metadata['artist_popularity'] = artist_info['popularity']
        updated_count += 1
        
        # Progress tracking
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(songs)} ({updated_count} updated)")
        
        # Periodic saves
        if (i + 1) % save_frequency == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(songs, f, indent=2, ensure_ascii=False)
            print(f"  💾 Saved checkpoint at {i + 1} songs")
    
    # Final save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Enriched {updated_count} songs with genres")
    print(f"✓ Saved to {output_path}")
    
    # Print summary
    print_genre_summary(songs)


def print_genre_summary(songs: List[Dict]):
    """Print genre distribution summary"""
    print("\n" + "="*60)
    print("GENRE SUMMARY")
    print("="*60)
    
    all_genres = []
    for song in songs:
        all_genres.extend(song.get('metadata', {}).get('genres', []))
    
    genre_counts = Counter(all_genres)
    
    print(f"\nTotal unique genres: {len(genre_counts)}")
    print(f"\nTop 20 genres:")
    for genre, count in genre_counts.most_common(20):
        print(f"  {genre}: {count}")
    
    # Songs with no genre
    no_genre = sum(1 for s in songs if not s.get('metadata', {}).get('genres'))
    print(f"\nSongs without genres: {no_genre} ({no_genre/len(songs)*100:.1f}%)")


def analyze_genre_gaps(songs_path: str = "songs_data.json"):
    """Identify genre gaps in dataset"""
    with open(songs_path) as f:
        songs = json.load(f)
    
    all_genres = []
    for song in songs:
        all_genres.extend(song.get('metadata', {}).get('genres', []))
    
    genre_counts = Counter(all_genres)
    
    print("\n" + "="*60)
    print("GENRE COVERAGE ANALYSIS")
    print("="*60)
    
    categories = {
        'rock': ['rock', 'indie', 'alternative', 'punk', 'metal'],
        'hip_hop': ['hip hop', 'rap', 'trap'],
        'electronic': ['edm', 'house', 'techno', 'electronic'],
        'pop': ['pop'],
        'rnb_soul': ['r&b', 'soul'],
        'country': ['country'],
        'jazz': ['jazz'],
        'folk': ['folk', 'singer-songwriter']
    }
    
    for category, keywords in categories.items():
        matching_songs = 0
        for song in songs:
            song_genres = [g.lower() for g in song.get('metadata', {}).get('genres', [])]
            if any(kw in ' '.join(song_genres) for kw in keywords):
                matching_songs += 1
        
        pct = matching_songs / len(songs) * 100
        status = "✓" if matching_songs > len(songs) * 0.05 else "⚠️"
        print(f"{status} {category.replace('_', ' ').title()}: {matching_songs} ({pct:.1f}%)")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add genre metadata to songs_data.json')
    parser.add_argument('input', nargs='?', default='songs_data.json', help='Input JSON file (default: songs_data.json)')
    parser.add_argument('-o', '--output', help='Output JSON file (default: overwrites input)')
    parser.add_argument('--analyze', action='store_true', help='Run genre gap analysis')
    parser.add_argument('--save-freq', type=int, default=100, help='Save checkpoint every N songs (default: 100)')
    
    args = parser.parse_args()
    
    # Enrich with genres
    enrich_songs_data(
        input_path=args.input,
        output_path=args.output,
        save_frequency=args.save_freq
    )
    
    # Analyze if requested
    if args.analyze:
        output = args.output if args.output else args.input
        analyze_genre_gaps(output)
