"""
Spotify Playlist Scraper - Get popular songs
Fetches tracks from curated playlists to build song list
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Set
import json


# Popular playlist IDs (from Spotify)
DEFAULT_PLAYLISTS = [
    "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
    "37i9dQZF1DX0XUsuxWHRQd",  # RapCaviar
    "37i9dQZF1DWXRqgc9PhiG5",  # Rock Classics
    "37i9dQZF1DX4dyzvuaRJ0n",  # mint (indie/alternative)
    "37i9dQZF1DX1lVhptIYRda",  # Hot Country
    "37i9dQZF1DX4SBhb3fqCJd",  # Are & Be (R&B)
    "37i9dQZF1DX0kbJZpiYdZl",  # Hot Hits USA
    "37i9dQZF1DX4UtSsGT1Sbe",  # All Out 80s
    "37i9dQZF1DX4o1oenSJRJd",  # All Out 90s
    "37i9dQZF1DX3rxVfibe1L0",  # Mood Booster
]

SPOTIFY_CLIENT_ID = "dc02e1a590e344558af75713c5f95e02"
SPOTIFY_CLIENT_SECRET = "921349166f544ae88d4f599b4f72b5dc"


def setup_spotify(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET) -> spotipy.Spotify:
    """
    Initialize Spotify client
    
    Args:
        client_id: Spotify API client ID
        client_secret: Spotify API client secret
    
    Returns:
        Spotify client instance
    """
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[Dict]:
    """
    Get all tracks from a Spotify playlist with metadata
    
    Args:
        sp: Spotify client
        playlist_id: Spotify playlist ID
    
    Returns:
        List of track dicts with title, artist, spotify_id, and audio features
    """
    tracks = []
    results = sp.playlist_tracks(playlist_id)
    
    while results:
        # Collect track IDs for batch audio features request
        track_ids = []
        track_items = []
        
        for item in results['items']:
            if item['track'] and item['track']['name']:
                track = item['track']
                track_ids.append(track['id'])
                track_items.append(track)
        
        # Get audio features in batch (more efficient)
        audio_features_list = sp.audio_features(track_ids) if track_ids else []
        
        # Combine track info with audio features
        for track, audio_features in zip(track_items, audio_features_list):
            audio_features = audio_features or {}  # Handle None
            
            tracks.append({
                'title': track['name'],
                'artist': track['artists'][0]['name'],
                'spotify_id': track['id'],
                'album': track['album']['name'],
                'release_date': track['album'].get('release_date', ''),
                'popularity': track.get('popularity'),
                'energy': audio_features.get('energy'),
                'valence': audio_features.get('valence'),
                'danceability': audio_features.get('danceability'),
                'acousticness': audio_features.get('acousticness'),
                'tempo': audio_features.get('tempo')
            })
        
        # Pagination
        results = sp.next(results) if results['next'] else None
    
    return tracks


def get_songs_from_playlists(client_id: str,
                             client_secret: str,
                             playlist_ids: List[str] = DEFAULT_PLAYLISTS,
                             target_count: int = 2000) -> List[Dict]:
    """
    Fetch songs from multiple playlists until target count reached
    
    Args:
        client_id: Spotify API client ID
        client_secret: Spotify API client secret
        playlist_ids: List of Spotify playlist IDs
        target_count: Target number of unique songs
    
    Returns:
        List of unique song dicts
    """
    sp = setup_spotify(client_id, client_secret)
    
    all_tracks = []
    seen_ids = set()
    
    for playlist_id in playlist_ids:
        print(f"Fetching playlist: {playlist_id}")
        
        try:
            playlist_info = sp.playlist(playlist_id)
            print(f"  - {playlist_info['name']} ({playlist_info['tracks']['total']} tracks)")
            
            tracks = get_playlist_tracks(sp, playlist_id)
            
            # Dedupe
            for track in tracks:
                if track['spotify_id'] not in seen_ids:
                    seen_ids.add(track['spotify_id'])
                    all_tracks.append(track)
            
            print(f"  - Total unique songs: {len(all_tracks)}")
            
            if len(all_tracks) >= target_count:
                break
                
        except Exception as e:
            print(f"  - Error: {e}")
            continue
    
    return all_tracks[:target_count]


def save_song_list(tracks: List[Dict], output_path: str = "song_list.json"):
    """
    Save song list to JSON
    
    Args:
        tracks: List of track dicts
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(tracks, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(tracks)} songs to {output_path}")


def load_song_list(input_path: str = "song_list.json") -> List[Dict]:
    """
    Load song list from JSON
    
    Args:
        input_path: Input file path
    
    Returns:
        List of track dicts
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        tracks = json.load(f)
    
    return tracks


# Example usage
if __name__ == "__main__":
    # Get credentials from: https://developer.spotify.com/dashboard
    SPOTIFY_CLIENT_ID = "YOUR_CLIENT_ID"
    SPOTIFY_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
    
    if SPOTIFY_CLIENT_ID == "YOUR_CLIENT_ID":
        print("Please set your Spotify credentials!")
        print("Get them from: https://developer.spotify.com/dashboard")
    else:
        # Fetch songs
        songs = get_songs_from_playlists(
            SPOTIFY_CLIENT_ID,
            SPOTIFY_CLIENT_SECRET,
            target_count=2000
        )
        
        # Save
        save_song_list(songs)
        
        print(f"\nSample songs:")
        for song in songs[:5]:
            print(f"  - {song['title']} by {song['artist']}")