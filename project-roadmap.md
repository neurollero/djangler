# Semantic Lyric Search - Project Roadmap

## Project Overview
A RAG-based system for semantic search of song lyrics. Users can search for songs by meaning, theme, and mood rather than just keywords. Built locally with open-source tools, designed for personal use with potential for open-source distribution.

## Tech Stack
- **Data Sources**: Spotify API (playlists), Genius API (lyrics)
- **Embeddings**: `all-mpnet-base-v2` (768 dims, local via sentence-transformers)
- **Vector DB**: Chroma (persistent, local storage)
- **Architecture**: Hybrid search (full songs + lyric sections)

## Data Pipeline & Files

```
┌─────────────────────────────────────────────────────────────┐
│ 1. SPOTIFY PLAYLIST SCRAPER (spotify_scraper.py)            │
│    Input:  Spotify API credentials                          │
│    Output: song_list.json (~1-2MB)                          │
│            - title, artist, spotify_id, popularity          │
│            - 2k-4k songs                                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. LYRICS SCRAPER (genius_scraper.py / fetchlib.py)         │
│    Input:  song_list.json + Genius API token                │
│    Output: songs_data.json (~15-20MB)                       │
│            - metadata (title, artist, url, genius_id)       │
│            - sections (verse, chorus, bridge text)          │
│            - full_lyrics (cleaned text)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. EMBEDDING & STORAGE (chroma_embedder.py)                 │
│    Input:  songs_data.json                                  │
│    Output: ./lyrics_db/ (~250-300MB)                        │
│            - Chroma persistent database                     │
│            - Two collections:                               │
│              * songs (full lyrics embeddings)               │
│              * sections (verse/chorus embeddings)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. SEARCH (search.py)                                       │
│    Input:  ./lyrics_db/ + query string                      │
│    Output: Ranked search results                            │
│            - song metadata + matched sections               │
│            - combined scores from both collections          │
└─────────────────────────────────────────────────────────────┘
```

### File Dependencies
- **song_list.json**: Source of truth for song catalog
- **songs_data.json**: Lyrics + metadata, can be rebuilt from song_list.json
- **./lyrics_db/**: Vector embeddings, can be rebuilt from songs_data.json
- All downstream files regenerated if upstream changes

## Current Status

### ✅ Completed (Phase 1-3a)

**Data Collection:**
- Spotify playlist scraper with ~4k songs
- Genius lyrics fetcher with fuzzy matching
- Deduplication and quality filtering
- Metadata: title, artist, release date, Spotify popularity

**Embedding & Storage:**
- Song-level embeddings (overall mood/theme)
- Section-level embeddings (verse/chorus/bridge)
- ~300MB vector DB, ~15MB lyrics JSON

**Search Functionality:**
- Hybrid scoring: 30% song-level, 70% section-level
- Returns top matches with relevant lyric snippets
- Handles ~4k songs, <100ms search time

**Data Quality:**
- Filters out transcripts, audiobooks, non-music
- Normalizes title variations (remaster tags, apostrophes)
- 70% fuzzy match threshold for robust matching

### 🚧 Current Phase

**Re-running lyric scraper** with improved deduplication logic after bug fix.

## Roadmap

### Phase 3b-c: Search Interface
- [ ] Simple CLI with formatted results
- [ ] Optional: Basic Streamlit demo (100 songs subset)
- [ ] Search result display with matched sections

### Phase 4: Analysis & Refinement

**Dataset Analysis:**
- [ ] Analyze genre/mood coverage using Spotify metadata
- [ ] Identify underrepresented categories
- [ ] Add targeted playlists to fill gaps
- [ ] Optional: LLM-based theme tagging for deeper categorization

**Search Quality:**
- [ ] Test suite of semantic queries
- [ ] Evaluate result relevance
- [ ] Optional: Query expansion via local LLM (Phi-3-mini)
  - Expand "sex" → ["desire", "lust", "passion", "intimacy"]
  - Handle euphemistic language better
  - 10-15s per query on Intel Mac

**Metadata Enhancement:**
- [ ] Retry Spotify audio features (energy, valence, tempo)
- [ ] Use for advanced filtering ("upbeat love songs")
- [ ] Genre/mood-based search refinement

### Phase 5: Distribution

**Open Source Release:**
- [ ] Clean up code structure
- [ ] Comprehensive README with setup instructions
- [ ] Demo dataset (100 songs) for testing
- [ ] Docker container (optional)

**Deployment Options:**
- **Option A**: Code-only repo, users build their own
- **Option B**: Include compressed vector DB (~100MB)
- **Option C**: Hosted demo (Fly.io/Railway, $35-65/mo)

**Licensing Strategy:**
- Start as free/open-source (non-commercial Genius API use)
- If hits 100k+ users, negotiate commercial licensing or switch to paid lyric APIs

## Key Metrics
- **Songs**: ~4k (target: 10k-20k for comprehensive coverage)
- **Search speed**: <100ms
- **Storage**: 315MB total (15MB lyrics + 300MB vectors)
- **Embedding model**: 768 dimensions

## Open Questions
1. **Monetization**: AdSense (~$50-150/mo) vs keep free vs freemium API
2. **Hosting**: Self-hosted only vs cloud deployment
3. **Dataset size**: Stay at 4k or scale to 10k-20k?
4. **Query expansion**: Add LLM layer or keep simple?

## Next Steps (Immediate)
1. ✅ Fix deduplication bug, re-scrape lyrics
2. Re-embed with cleaned dataset
3. Build CLI interface
4. Test search quality with diverse queries
5. Analyze dataset coverage
6. Add Spotify audio features
7. Write documentation for open-source release

## Future Enhancements
- Playlist generation from search results
- Export to Spotify/Apple Music
- Multi-language support
- Collaborative filtering (similar songs)
- User preference learning
- Advanced filters (decade, genre, mood, tempo)
