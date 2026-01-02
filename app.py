"""
DJANGLER - Semantic Lyric Search
Streamlit UI for Hugging Face Spaces
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for Hugging Face Spaces
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from chromasearchlib import search_songs, load_collections

# Show loading message during initial imports
with st.spinner("Loading search engine... (first run may take 1-2 minutes)"):
    from chromasearchlib import search_songs, load_collections

@st.cache_resource
def load_db():
    with st.spinner("Loading database..."):
        return load_collections(db_path="./lyrics_db")

from chromasearchlib import search_songs, load_collections
from typing import List, Dict

# Page config
st.set_page_config(
    page_title="DJANGLER - Semantic Lyric Search",
    page_icon="🎵",
    layout="wide"
)

# Cache expensive operations
@st.cache_resource
def load_db():
    """Load ChromaDB collections (runs once)"""
    try:
        return load_collections(db_path="./lyrics_db")
    except Exception as e:
        st.error(f"Failed to load database: {e}")
        return None, None, None

@st.cache_data
def get_db_stats(_client, _songs_coll, _sections_coll):
    """Get database statistics"""
    if _songs_coll and _sections_coll:
        return {
            'songs': _songs_coll.count(),
            'sections': _sections_coll.count()
        }
    return {'songs': 0, 'sections': 0}

# Load database
client, songs_coll, sections_coll = load_db()
stats = get_db_stats(client, songs_coll, sections_coll)

# Header
st.title("🎵 DJANGLER")
st.subheader("Find songs by what they mean, not what they say")

# Sidebar - Info & Settings
with st.sidebar:
    st.header("About")
    st.write(f"**Dataset:** {stats['songs']:,} songs")
    st.write(f"**Sections:** {stats['sections']:,} lyric fragments")
    
    st.divider()
    
    st.header("Search Settings")
    n_results = st.slider("Number of results", 5, 20, 10)
    
    genre_boost = st.slider(
        "Genre boost",
        0.0, 3.0, 1.5, 0.1,
        help="Multiplier for songs matching genre keywords (e.g., 'indie rock')"
    )
    # Popularity controls
    st.divider()
    st.subheader("Popularity Ranking")
    
    min_popularity = st.slider(
        "Minimum popularity",
        0, 100, 25,
        help="Filter out songs below this popularity (25 = suppress weird/unpopular songs)"
    )
    
    max_popularity_boost = st.slider(
        "Max popularity boost",
        1.0, 2.0, 1.5, 0.1,
        help="Maximum boost for very popular songs (pop >= 90). 1.0 = no boost, 1.5 = 50% boost"
    )
    
    # Show what the settings mean
    if max_popularity_boost > 1.0:
        st.caption(f"✓ Popular songs (pop 90+) boosted {(max_popularity_boost-1)*100:.0f}%")
    else:
        st.caption("No popularity boost")
    
    if min_popularity > 0:
        st.caption(f"✓ Filtering songs with popularity < {min_popularity}")

    
    show_sections = st.checkbox("Show matched lyrics", value=True)
    show_genres = st.checkbox("Show genres", value=True)
    show_scores = st.checkbox("Show scores", value=False)
    
    st.divider()
    
    with st.expander("How it works"):
        st.write("""
        **Semantic search** finds songs by meaning:
        - "feeling lost" → songs about confusion, searching
        - "summer nights" → nostalgic warm-weather songs
        - "indie rock rebellion" → combines lyrics + genre
        
        Uses vector embeddings to understand lyrical themes.
        """)
    
    with st.expander("Example queries"):
        st.code("""
childhood memories
heartbreak and longing
indie songs about freedom
rock anthems rebellion
lonely nights driving
        """.strip())

# Main search interface
query = st.text_input(
    "Search by meaning, mood, or theme",
    placeholder="e.g., 'indie songs about loneliness' or 'fighting for what's right'",
    help="Try describing what the song is about, how it feels, or combine with genres"
)

# Search button
if query:
    with st.spinner("Searching..."):
        try:
            results = search_songs(
                query=query,
                n_results=n_results,
                genre_boost=genre_boost,
                min_popularity=min_popularity,
                max_popularity_boost=max_popularity_boost,
                use_genre_boosting=(genre_boost > 0)
            )

            
            if not results:
                st.warning("No results found. Try a different query.")
            else:
                st.success(f"Found {len(results)} songs")
                
                # Display results
                for i, r in enumerate(results, 1):
                    # Title with genre boost indicator
                    title = f"**{i}. {r['title']}** - {r['artist']}"
                    if r.get('genre_boosted'):
                        title += " 🎸"
                    
                    with st.expander(title, expanded=(i <= 3)):
                        # Genres
                        if show_genres and r.get('genres'):
                            genres_display = ', '.join(r['genres'][:5])
                            st.caption(f"🏷️ {genres_display}")
                        
                        # Popularity display
                        popularity = r.get('popularity', 0)
                        if popularity:
                            # Determine tier based on dataset
                            pop_tier = "niche"
                            tier_emoji = "📊"
                            if popularity >= 84:  # P90
                                pop_tier = "very popular"
                                tier_emoji = "🔥"
                            elif popularity >= 76:  # P75
                                pop_tier = "popular"
                                tier_emoji = "⭐"
                            elif popularity >= 64:  # P50
                                pop_tier = "established"
                                tier_emoji = "✓"
                        
                        # Show boost if applied
                        boost_factor = r.get('popularity_boost_factor', 1.0)
                        pop_text = f"{tier_emoji} Popularity: {popularity} ({pop_tier})"
                        if boost_factor > 1.0:
                            pop_text += f" • Boosted {(boost_factor-1)*100:.0f}%"
                        
                        st.caption(pop_text)

                        
                        # Scores
                        if show_scores:
                            st.caption(
                                f"Score: {r['score']:.2f} "
                                f"(song: {r['song_score']:.2f}, "
                                f"sections: {r['section_score']:.2f})"
                            )
                        
                        # Matched lyric section
                        if show_sections and r.get('top_sections'):
                            section = r['top_sections'][0]
                            st.write("**Matched lyric:**")
                            st.info(f"*[{section['type'].title()}]*\n\n{section['text'][:300]}...")
                        
                        # Genius link
                        if r.get('url'):
                            st.link_button("View on Genius", r['url'])
                
        except Exception as e:
            st.error(f"Search failed: {e}")

# Footer
st.divider()
st.caption(f"Built with 🌈ChromaDB + sentence-transformers🤗 | {stats['songs']} songs with semantic embeddings")