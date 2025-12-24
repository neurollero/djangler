# DJANGLER

**Semantic Lyric Search Engine** - Find songs by meaning, theme, and mood rather than just keywords.

DJANGLER is a semantic search system that uses vector embeddings to understand the meaning and emotional content of song lyrics. Unlike traditional keyword search, it can find songs that match your query conceptually, making it perfect for discovering music based on themes, moods, or lyrical content.

## Features

- **Semantic Search**: Find songs by meaning, not just keywords
- **Section-Level Matching**: Search within specific song sections (verses, choruses, bridges)
- **Hybrid Scoring**: Combines full-song and section-level relevance for better results
- **Metadata Integration**: Enriched with Spotify data including genres and artist popularity
- **Local & Private**: All processing happens on your machine using open-source tools

## Architecture

### Data Pipeline

```
1. Spotify Scraper (spotifylib.py)
   ↓ Pulls songs from curated playlists
   ↓ Output: songs_list_*.json
   
2. Genius Lyrics Fetcher (fetchlib.py)
   ↓ Fetches lyrics for each song
   ↓ Consolidates into master dataset
   ↓ Output: songs_data.json (single source of truth)
   
3. ChromaDB Embedder (chromalib.py)
   ↓ Creates vector embeddings
   ↓ Stores in two collections:
   ↓   - Full songs
   ↓   - Individual sections
   ↓ Output: ./lyrics_db/
   
4. Search Interface (chromasearchlib.py)
   ↓ Hybrid search across both collections
   ↓ Weighted scoring and deduplication
   ↓ Returns ranked results
```

### Tech Stack

- **Embeddings**: `all-mpnet-base-v2` (768 dimensions)
- **Vector Database**: ChromaDB (persistent, local storage)
- **APIs**: Spotify API (metadata), Genius API (lyrics)
- **Libraries**: sentence-transformers, spotipy, beautifulsoup4

## Installation

### Prerequisites

- Python 3.8+
- Spotify API credentials ([Get them here](https://developer.spotify.com/dashboard))
- Genius API token ([Get it here](https://genius.com/api-clients))

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/djangler.git
cd djangler

# Install dependencies
pip install chromadb sentence-transformers spotipy requests beautifulsoup4

# Set up environment variables
export SPOTIFY_CLIENT_ID='your_spotify_client_id'
export SPOTIFY_CLIENT_SECRET='your_spotify_client_secret'
export GENIUS_ACCESS_TOKEN='your_genius_token'
```

## Usage

### 1. Collect Songs from Spotify

```python
from spotifylib import get_songs_from_playlists, save_song_list

# Define playlist IDs you want to scrape
playlist_ids = [
    "37i9dQZF1DXcBWIGoYBM5M",  # Example: Today's Top Hits
    "37i9dQZF1DX0XUsuxWHRQd"   # Example: RapCaviar
]

# Fetch songs (deduplicates automatically)
songs = get_songs_from_playlists(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    playlist_ids=playlist_ids,
    target_count=2000
)

# Save to temporary file
save_song_list(songs, filename="songs_list_batch1.json")
```

### 2. Fetch Lyrics and Build Master Dataset

```python
from fetchlib import process_song_list

# Process the song list and append to master dataset
process_song_list(
    songs_json="songs_list_batch1.json",
    output_json="songs_data.json",  # Master dataset
    genius_token=GENIUS_ACCESS_TOKEN
)
```

**Note**: Run steps 1-2 multiple times with different playlists to expand your dataset. All data consolidates into `songs_data.json`.

### 3. Create Vector Embeddings

```python
from chromalib import setup_chroma, create_collections, load_and_embed_all

# Embed all songs into ChromaDB
load_and_embed_all(
    json_path="songs_data.json",
    db_path="./lyrics_db",
    model_name="all-mpnet-base-v2"
)
```

### 4. Search for Songs

```python
from chromasearchlib import search_songs, print_results

# Search by meaning/theme
results = search_songs(
    query="feeling lost and searching for purpose",
    n_results=10
)

# Display results
print_results(results, show_sections=True)
```

## File Structure

```
djangler/
├── spotifylib.py          # Spotify playlist scraping
├── fetchlib.py            # Genius lyrics fetching & cleaning
├── chromalib.py           # Vector embedding & storage
├── chromasearchlib.py     # Semantic search interface
├── songs_data.json        # Master dataset (generated)
├── lyrics_db/             # ChromaDB storage (generated)
├── dev_notebook.ipynb     # Development notebook
└── README.md
```

## Data Format

### songs_data.json Structure

```json
[
  {
    "metadata": {
      "title": "Bohemian Rhapsody",
      "artist": "Queen",
      "genius_id": 12345,
      "url": "https://genius.com/...",
      "release_date": "1975-10-31",
      "spotify_id": "abc123",
      "genres": ["classic rock", "progressive rock"],
      "artist_popularity": 92
    },
    "full_lyrics": "Is this the real life? Is this just fantasy?...",
    "sections": [
      {
        "section_type": "verse",
        "section_number": 1,
        "text": "Is this the real life?..."
      },
      {
        "section_type": "chorus",
        "section_number": 1,
        "text": "I see a little silhouetto of a man..."
      }
    ]
  }
]
```

## Configuration

### Key Constants

**chromalib.py**:
- `EMBEDDING_MODEL`: Default is `"all-mpnet-base-v2"` (768 dims, better quality)
- Alternative: `"all-MiniLM-L6-v2"` (384 dims, faster)

**chromasearchlib.py**:
- `DEFAULT_SONG_WEIGHT`: 0.5 (weight for full-song matches)
- `DEFAULT_SECTION_WEIGHT`: 0.6 (weight for section matches)
- `SONG_QUERY_LIMIT`: 50 (songs to fetch before scoring)
- `SECTION_QUERY_LIMIT`: 100 (sections to fetch before scoring)

**fetchlib.py**:
- `OUTPUT_PATH`: "songs_data.json" (master dataset location)
- `API_PAUSE`: 0.2 seconds (rate limiting for Genius API)
- `TITLE_SIMILARITY`: 0.7 (fuzzy matching threshold)

## Current Dataset Stats

- **Songs**: ~4,000 tracks
- **Storage**: ~315MB total
  - lyrics JSON: ~15MB
  - Vector database: ~300MB
- **Search Speed**: <100ms per query
- **Coverage**: Diverse genres from curated Spotify playlists

## Workflow Patterns

### Iterative Dataset Expansion

1. Run Spotify scraper with different playlists → creates `songs_list_*.json`
2. Run fetchlib on each list → appends to `songs_data.json`
3. Re-run embedding pipeline → updates `lyrics_db/`
4. Search uses the consolidated dataset automatically

### Caching & Efficiency

- API responses are cached to avoid duplicate calls
- Checkpoint saving for processing large datasets
- Deduplication based on Spotify track IDs
- Batch processing for audio features

## Limitations

### Spotify API

Currently uses **Client Credentials** flow:
- ✅ Access to public playlists, tracks, albums
- ✅ Genre and artist popularity data
- ❌ Audio features (energy, valence, tempo) - requires OAuth
- ❌ User-specific data (saved tracks, playlists)

### Genius API

- Rate limit: 10,000 requests/day
- Non-commercial use only (current license)
- Some lyrics may be incomplete or unavailable

## Roadmap

### Immediate Next Steps
- [ ] Build CLI interface for easier interaction
- [ ] Add metadata-based ranking (genre boosting, popularity weighting)
- [ ] Implement query expansion for better semantic matching
- [ ] Create test suite for search quality evaluation

### Future Enhancements
- [ ] OAuth integration for Spotify audio features
- [ ] Advanced filtering (decade, genre, mood, tempo)
- [ ] Playlist generation from search results
- [ ] Export to Spotify/Apple Music
- [ ] Multi-language support
- [ ] Web interface (Streamlit/Gradio)

## Development

### Running the Development Notebook

```bash
jupyter notebook dev_notebook.ipynb
```

The notebook contains:
- Complete pipeline demonstrations
- Testing functions for each module
- Search quality experiments
- Database inspection utilities

### Modular Architecture

The codebase follows a clean separation:
- **spotifylib.py**: Data acquisition (Spotify)
- **fetchlib.py**: Data enrichment (Genius)
- **chromalib.py**: Data storage (embeddings)
- **chromasearchlib.py**: Data retrieval (search)

Each module can be imported and used independently.

## Contributing

This project is currently in active development. Contributions are welcome for:
- Additional data sources
- Search quality improvements
- Performance optimizations
- Documentation enhancements

## License

This project is intended for personal, non-commercial use. Genius API usage must comply with their terms of service (non-commercial use only).

## Acknowledgments

- **Spotify Web API** for music metadata
- **Genius API** for lyrics data
- **ChromaDB** for vector storage
- **sentence-transformers** for embedding models
- **Hugging Face** for hosting the embedding models

## Troubleshooting

### Common Issues

**Empty search results**:
- Ensure `songs_data.json` exists and contains data
- Check that ChromaDB has been populated (`chromalib.load_and_embed_all()`)
- Verify the database path matches in search functions

**API rate limits**:
- Genius: Max 10,000 requests/day (add delays in `fetchlib.py`)
- Spotify: No explicit limit for Client Credentials, but use responsibly

**Memory issues**:
- Process large datasets in batches
- Use checkpoint saving in fetchlib
- Consider using the smaller MiniLM model for embeddings

**Duplicate songs**:
- Deduplication happens at Spotify scraping stage
- To force re-processing, delete `songs_data.json` and re-run pipeline

## Contact

For questions, suggestions, or bug reports, please open an issue on GitHub.

---

**Built with ❤️ for music lovers who want to explore lyrics semantically**