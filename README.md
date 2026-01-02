# DJANGLER

**Find songs by what they mean, not what they say.**

## Live Demo

Try DJANGLER without any setup: **[🎵 DJANGLER on Hugging Face Spaces 🤗](https://huggingface.co/spaces/neurollero/djangler)**

Search semantically through 9,000+ songs directly in your browser.    

## Overview

DJANGLER is a semantic search engine for song lyrics. Instead of keyword matching, it understands meaning, themes, and emotions using vector embeddings.

**Search examples:**
- "feeling lost and searching for meaning" → finds songs about existential uncertainty
- "indie rock songs about rebellion" → combines lyrical themes with genre filtering
- "childhood summers" → nostalgic warm-weather songs

**How it works:**
- Dataset of ~9,000 popular songs with lyrics, metadata, and genre tags
- Vector embeddings capture semantic meaning of full songs and individual sections
- Hybrid search ranks by both overall theme and specific lyric matches
- Genre boosting weights results by musical style

**Features:**
- Local & private (all processing on your machine)
- Section-level matching (see the exact verse/chorus that matches)
- Genre-aware ranking
- Fast (~100ms search on 9k songs)

---

## Quick Start

Get up and running in 3 steps: download curated metadata, fetch lyrics, create embeddings.

### 1. Clone & Install

```bash
git clone https://github.com/youruser/djangler.git
cd djangler
pip install chromadb sentence-transformers requests beautifulsoup4
```

### 2. Download & Populate Dataset

**Get the curated metadata** (~1MB, no copyrighted content):
```bash
# Download from releases
wget https://github.com/youruser/djangler/releases/latest/download/metadata_distribution.json.gz
```

**Fetch lyrics** using your own Genius API key ([get one here](https://genius.com/api-clients)):
```bash
export GENIUS_ACCESS_TOKEN='your_token_here'
python populate_from_metadata.py metadata_distribution.json.gz
```

This takes ~30 minutes for 9k songs. Progress is checkpointed every 100 songs.

### 3. Create Embeddings

```bash
python chromalib.py
```

Takes ~10 minutes. Creates `./lyrics_db/` with vector embeddings.

### 4. Search!

```bash
# Basic search
python chromasearchlib.py feeling lost searching for meaning

# With genre filtering
python chromasearchlib.py indie songs about loneliness --genre-boost 1.5

# More results
python chromasearchlib.py heartbreak -n 20
```

**Web interface**:
```bash
pip install streamlit
streamlit run app.py
```

---

## Full Documentation

### CLI Reference

**Search with options:**
```bash
# Basic search
python chromasearchlib.py <your query here>

# With genre boosting (0 = disabled, 1.5 = default, 3.0 = max)
python chromasearchlib.py indie rock rebellion --genre-boost 1.5

# Number of results (5-20)
python chromasearchlib.py childhood memories -n 20

# Database statistics
python chromasearchlib.py --stats
```

**Genre keywords** (automatically detected in queries):
- Rock: `rock`, `indie rock`, `alternative rock`, `classic rock`, `punk rock`
- Pop: `pop`, `dance pop`, `electropop`, `synth pop`, `k-pop`
- Hip Hop: `hip hop`, `rap`, `trap`, `drill`, `boom bap`
- Electronic: `edm`, `house`, `techno`, `dubstep`, `trance`
- R&B: `r&b`, `rnb`, `soul`, `neo soul`
- And many more... (see `chromasearchlib.py` for full list)

### Python API

```python
from chromasearchlib import search_songs, print_results

# Basic search
results = search_songs(
    query="heartbreak and longing",
    n_results=10,
    genre_boost=1.5  # 50% boost for genre matches
)

print_results(results, show_sections=True)

# Advanced: section-only search
from chromasearchlib import search_sections_only

sections = search_sections_only(
    query="summer nights and freedom",
    n_results=10
)

for section in sections:
    print(f"{section['title']} - [{section['section_type']}]")
    print(section['text'][:100])
```

### Configuration

**Search weights** (in `chromasearchlib.py`):
```python
DEFAULT_SONG_WEIGHT = 0.5      # Full-song match weight
DEFAULT_SECTION_WEIGHT = 0.6   # Section match weight
DEFAULT_GENRE_BOOST = 1.5      # Genre match multiplier
```

**Embedding model** (in `chromalib.py`):
```python
EMBEDDING_MODEL = "all-mpnet-base-v2"  # 768 dims, better quality
# Alternative: "all-MiniLM-L6-v2"      # 384 dims, faster/smaller
```

### Building Your Own Dataset

If you want to build from scratch instead of using the metadata distribution:

#### 1. Scrape Spotify Playlists

```python
from spotifylib import get_songs_from_playlists, save_song_list

# Get API credentials from https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = "your_client_id"
SPOTIFY_CLIENT_SECRET = "your_client_secret"

# Use public playlists or find your own
playlist_ids = [
    "37i9dQZF1DXcBWIGoYBM5M",  # Today's Top Hits
    "37i9dQZF1DX0XUsuxWHRQd",  # RapCaviar
    # ... add more
]

songs = get_songs_from_playlists(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    playlist_ids=playlist_ids,
    target_count=2000
)

save_song_list(songs, "songs_list_batch1.json")
```

**Finding playlists:**
```python
from spotifylib import setup_spotify

sp = setup_spotify(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)

# Search by genre/theme
results = sp.search(q="indie folk", type='playlist', limit=5)
playlist_ids = [p['id'] for p in results['playlists']['items']]
```

#### 2. Fetch Lyrics

```python
from fetchlib import process_song, load_songs_as_tuples
import time

# Get Genius API token from https://genius.com/api-clients
GENIUS_ACCESS_TOKEN = "your_token_here"

song_list = load_songs_as_tuples("songs_list_batch1.json")

for title, artist in song_list:
    process_song(
        title, 
        artist, 
        GENIUS_ACCESS_TOKEN, 
        output_path="songs_data.json"
    )
    time.sleep(0.1)  # Rate limiting
```

#### 3. Add Genre Metadata

```python
from enrich_songs_data import enrich_songs_data

enrich_songs_data(
    input_path="songs_data.json",
    save_frequency=100  # Checkpoint every 100 songs
)
```

#### 4. Create Embeddings

```python
from chromalib import load_and_embed_all

load_and_embed_all(
    json_path="songs_data.json",
    db_path="./lyrics_db",
    model_name="all-mpnet-base-v2"
)
```

### Data Architecture

```
Spotify API → song_list.json (titles, IDs, metadata)
     ↓
Genius API → songs_data.json (lyrics + sections)
     ↓
Embeddings → lyrics_db/ (vector database)
     ↓
Search → ranked results
```

**File structure:**
```
songs_data.json         # Master dataset (lyrics + metadata)
lyrics_db/              # ChromaDB vector storage
  ├── songs/            # Full-song embeddings
  └── sections/         # Section-level embeddings
```

**Data format** (`songs_data.json`):
```json
{
  "metadata": {
    "title": "Song Title",
    "artist": "Artist Name",
    "genius_id": 12345,
    "url": "https://genius.com/...",
    "genres": ["indie rock", "alternative"],
    "artist_popularity": 85,
    "release_date": "2020-01-01"
  },
  "sections": [
    {
      "section_type": "verse",
      "section_number": 1,
      "text": "lyrics here..."
    },
    {
      "section_type": "chorus",
      "section_number": 1,
      "text": "lyrics here..."
    }
  ],
  "full_lyrics": "complete lyrics text"
}
```

### Development

**Jupyter notebook:**
```bash
jupyter notebook dev_notebook_clean.ipynb
```

Includes complete pipeline demos, search experiments, and database utilities.

**Analysis scripts:**
```bash
# Dataset statistics
python -c "from enrich_songs_data import print_genre_summary; print_genre_summary('songs_data.json')"

# Genre gap analysis
python enrich_songs_data.py --analyze

# Extract test subset
python extract_subset.py songs_data.json 100 -o test_songs.json
```

### Deployment

**Streamlit (local):**
```bash
streamlit run app.py
```

## Advanced Topics

### Genre Boosting Deep Dive

Genre boosting multiplies the relevance score for songs whose genres match keywords in your query.

**How it works:**
1. Query is parsed for genre keywords (e.g., "indie rock")
2. Semantic search runs on remaining terms
3. Results with matching genres get score × `genre_boost`
4. Results are re-ranked

**Example:**
```python
# Query: "indie rock songs about rebellion"
# 
# Without boosting (genre_boost=0):
#   1. "Rage Against the Machine - Killing in the Name" (rap metal)
#   2. "Arctic Monkeys - I Bet You Look Good on the Dancefloor" (indie rock)
#
# With boosting (genre_boost=1.5):
#   1. "Arctic Monkeys - I Bet You Look Good on the Dancefloor" (indie rock) ← boosted
#   2. "The Strokes - Last Nite" (indie rock) ← boosted
#   3. "Rage Against the Machine - Killing in the Name" (rap metal)
```

**Tuning:**
- `1.0` = no boosting
- `1.3-1.5` = subtle preference (default)
- `2.0-3.0` = strong preference
- `0` = disable genre parsing entirely

### Metadata Distribution

**Why metadata-only?**
- Lyrics are copyrighted content
- Metadata distribution: ~1MB vs ~30MB full dataset
- Users fetch lyrics with own Genius API key

**Creating a distribution:**
```bash
python create_metadata_distribution.py songs_data.json -o metadata_distribution.json.gz
```

**Validating:**
```bash
python validate_metadata.py metadata_distribution.json.gz
```

**What's included:**
- Song titles, artists, IDs, URLs
- Genres, popularity scores, release dates
- Section structure (types/counts, no text)

**What's excluded:**
- All lyric text (copyrighted)

---

## Roadmap

### Completed ✅
- Core semantic search with hybrid scoring
- Genre enrichment and boosting
- Metadata-only distribution
- CLI and Python API
- Streamlit web interface
- Dataset expansion to ~9k songs

### Planned 📋
- **Last.fm mood/vibe tags** (crowdsourced metadata)
- Audio features integration (energy, valence, tempo)
- Playlist generation from search results
- Export to Spotify/Apple Music
- Query expansion (LLM-based)

---

## Tech Stack

- **Embeddings**: sentence-transformers (`all-mpnet-base-v2`)
- **Vector DB**: ChromaDB (persistent, local storage)
- **APIs**: Spotify (metadata), Genius (lyrics)
- **Search**: Hybrid semantic + metadata ranking
- **UI**: Streamlit

## Limitations

**Genius API**: Non-commercial use only. Users must obtain their own API keys.

**Audio Features**: Not currently implemented (would require Spotify OAuth).

**Dataset Size**: ~9k songs (~1GB embeddings). Larger datasets require more RAM.

## License

Personal/non-commercial use. Genius API terms require non-commercial usage. 

**Important**: Lyrics are copyrighted material. This repository does not include or distribute copyrighted lyrics. Users fetch lyrics using their own Genius API credentials.

## Contributing

Contributions welcome! Areas of interest:
- Dataset expansion (curated playlists)
- Search quality improvements
- UI/UX enhancements
- Documentation
- Multi-language support
---

**Built with ❤️ for music discovery through semantic understanding.**
