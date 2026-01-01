# DJANGLER

**Find songs by what they mean, not just what they say.**

**Semantic Lyric Search Engine** - Find songs by meaning, theme, and mood rather than keywords.

Uses vector embeddings to understand lyrical content. Search for "feeling lost and searching for purpose" instead of keyword matching.

## Features

- **Semantic Search**: Match by meaning, not just keywords
- **Section-Level Matching**: Find specific verses, choruses, bridges
- **Genre Boosting**: Weight results by musical style
- **Hybrid Scoring**: Combines full-song and section-level relevance
- **Local & Private**: All processing on your machine

## Current Status

**Dataset**: ~9,000 songs with lyrics, metadata, and genre tags

**Collections**:
- Full song embeddings (overall mood/theme)
- Section-level embeddings (verse/chorus/bridge)
- Spotify metadata (genres, popularity, release dates)

**Search**: CLI tool with genre-aware ranking

## Quick Start

### Prerequisites
```bash
pip install chromadb sentence-transformers spotipy requests beautifulsoup4
```

### API Keys

- Spotify: https://developer.spotify.com/dashboard
- Genius: https://genius.com/api-clients
```bash
export SPOTIFY_CLIENT_ID='your_id'
export SPOTIFY_CLIENT_SECRET='your_secret'
export GENIUS_ACCESS_TOKEN='your_token'
```

### Search (CLI)
```bash
# Basic search
python chromasearchlib.py feeling lost searching for meaning

# With genre boosting
python chromasearchlib.py indie rock songs about rebellion --genre-boost 1.5

# More results
python chromasearchlib.py childhood memories -n 20

# Database stats
python chromasearchlib.py --stats
```

### Search (API)
```python
from chromasearchlib import search_songs, print_results

results = search_songs(
    query="heartbreak and longing",
    n_results=10,
    genre_boost=1.5  # 50% boost for genre matches
)

print_results(results, show_sections=True)
```

## Building Your Own Dataset

### 1. Scrape Playlists
```python
from spotifylib import get_songs_from_playlists, save_song_list

playlist_ids = ["37i9dQZF1DXcBWIGoYBM5M"]  # Spotify playlist IDs

songs = get_songs_from_playlists(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    playlist_ids=playlist_ids,
    target_count=2000
)

save_song_list(songs, "songs_list_batch1.json")
```

### 2. Fetch Lyrics
```python
from fetchlib import process_song, load_songs_as_tuples
import time

song_list = load_songs_as_tuples("songs_list_batch1.json")

for title, artist in song_list:
    process_song(title, artist, GENIUS_ACCESS_TOKEN, output_path="songs_data.json")
    time.sleep(0.1)  # Rate limiting
```

### 3. Add Genre Metadata
```python
from enrich_songs_data import enrich_songs_data

enrich_songs_data(
    input_path="songs_data.json",
    save_frequency=100
)
```

### 4. Create Embeddings
```python
from chromalib import load_and_embed_all

load_and_embed_all(
    json_path="songs_data.json",
    db_path="./lyrics_db",
    model_name="all-mpnet-base-v2"
)
```

## Architecture
```
Spotify API → song_list.json (titles, IDs, metadata)
     ↓
Genius API → songs_data.json (lyrics + sections)
     ↓
Embeddings → lyrics_db/ (vector database)
     ↓
Search → ranked results
```

### File Structure
```
songs_data.json         # Master dataset (lyrics + metadata)
lyrics_db/              # ChromaDB vector storage
  ├── songs collection  # Full-song embeddings
  └── sections collection  # Section-level embeddings
```

### Data Format
```json
{
  "metadata": {
    "title": "Song Title",
    "artist": "Artist Name",
    "genius_id": 12345,
    "genres": ["indie rock", "alternative"],
    "artist_popularity": 85
  },
  "sections": [
    {"section_type": "verse", "section_number": 1, "text": "..."},
    {"section_type": "chorus", "section_number": 1, "text": "..."}
  ],
  "full_lyrics": "complete lyrics text"
}
```

## Configuration

**Search weights** (chromasearchlib.py):
- `DEFAULT_SONG_WEIGHT`: 0.5 (full-song match weight)
- `DEFAULT_SECTION_WEIGHT`: 0.6 (section match weight)
- `DEFAULT_GENRE_BOOST`: 1.5 (genre match multiplier)

**Embedding model** (chromalib.py):
- Default: `all-mpnet-base-v2` (768 dims, better quality)
- Alternative: `all-MiniLM-L6-v2` (384 dims, faster/smaller)

**Genre keywords** (chromasearchlib.py):
- Rock, indie, pop, hip hop, R&B, electronic, folk, jazz, metal, etc.
- Add custom genres to `GENRE_KEYWORDS` dict

## Development Notebook
```bash
jupyter notebook dev_notebook_clean.ipynb
```

Includes complete pipeline demos, search experiments, and database utilities.

## Next Steps

### Immediate
- [x] CLI search interface
- [ ] **Metadata-only distribution** (songs_data.json without lyrics for easy sharing)
- [ ] **Streamlit UI** (search interface with filters)
- [ ] Deploy demo on Hugging Face Spaces

### Future Enhancements
- [ ] **Last.fm mood/vibe tags** (crowdsourced metadata for better semantic matching)
- [ ] Playlist generation from search results
- [ ] Export to Spotify/Apple Music
- [ ] Query expansion (LLM-based synonym generation)
- [ ] Audio features integration (energy, valence, tempo)
- [ ] Multi-language support

## Tech Stack

- **Embeddings**: sentence-transformers (all-mpnet-base-v2)
- **Vector DB**: ChromaDB (persistent, local)
- **APIs**: Spotify (metadata), Genius (lyrics)
- **Search**: Hybrid semantic + metadata ranking

## Limitations

**Genius API**: Non-commercial use only. Users must obtain their own API keys.

**Audio Features**: Requires Spotify OAuth (not implemented). Currently using Client Credentials for metadata only.

**Dataset Size**: ~9k songs (~300MB embeddings). Larger datasets require more RAM.

## License

Personal/non-commercial use. Genius API terms require non-commercial usage. Lyrics are copyrighted material - not included in repository distributions.

## Contributing

Built for music discovery through semantic lyric search. Contributions welcome for:
- Dataset expansion (curated playlists)
- Search quality improvements
- UI/UX enhancements
- Documentation
---

