"""
Search Module - Query songs and sections with genre boosting
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import sys

QUERY = ["memories of childhood summers"]

NUMBER_OF_SUGGESTIONS = 10

EMBEDDING_MODEL = "all-mpnet-base-v2" 
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Search configuration constants
SONG_QUERY_LIMIT = 50
SECTION_QUERY_LIMIT = 100
DEFAULT_SONG_WEIGHT = 0.5
DEFAULT_SECTION_WEIGHT = 0.6
DEFAULT_GENRE_BOOST = 1.5

# Genre keyword mappings for query parsing
GENRE_KEYWORDS = {
    'rock': ['rock', 'indie rock', 'alternative rock', 'classic rock', 'punk rock', 
             'hard rock', 'progressive rock', 'psychedelic rock', 'garage rock'],
    'indie': ['indie', 'indie pop', 'indie rock', 'indie folk', 'bedroom pop'],
    'pop': ['pop', 'dance pop', 'electropop', 'synth pop', 'k-pop', 'art pop'],
    'hip hop': ['hip hop', 'rap', 'trap', 'drill', 'boom bap', 'conscious rap'],
    'country': ['country', 'alt country', 'americana', 'bluegrass', 'outlaw country'],
    'r&b': ['r&b', 'rnb', 'soul', 'neo soul', 'alternative r&b'],
    'electronic': ['edm', 'house', 'techno', 'dubstep', 'trance', 'drum and bass', 
                   'ambient', 'downtempo', 'electronic'],
    'folk': ['folk', 'folk rock', 'singer-songwriter', 'acoustic', 'alt-folk'],
    'jazz': ['jazz', 'bebop', 'smooth jazz', 'fusion', 'blues'],
    'metal': ['metal', 'heavy metal', 'death metal', 'black metal', 'metalcore', 'thrash'],
    'punk': ['punk', 'pop punk', 'hardcore', 'post-punk', 'emo'],
    'latin': ['reggaeton', 'bachata', 'salsa', 'latin', 'cumbia', 'merengue'],
    'alternative': ['alternative', 'alt rock', 'shoegaze', 'dream pop', 'post-rock'],
    'dance': ['disco', 'funk', 'dance', 'nu-disco'],
    'experimental': ['experimental', 'avant-garde', 'noise', 'industrial'],
    'grunge': ['grunge', 'post-grunge']
}


def parse_query_for_genres(query: str) -> Tuple[str, List[str]]:
    """
    Extract genre keywords from query
    
    Args:
        query: Search query text
    
    Returns:
        Tuple of (cleaned_query, list_of_genre_keywords)
    """
    query_lower = query.lower()
    
    # Find matching genres
    matched_genres = set()
    genre_words = set()
    
    for genre_category, keywords in GENRE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                # Add all keywords from this genre category
                matched_genres.update(keywords)
                # Track words to remove from query
                genre_words.update(keyword.split())
    
    # Remove genre words from query
    words = query.split()
    cleaned_words = [w for w in words if w.lower() not in genre_words]
    cleaned_query = ' '.join(cleaned_words)
    
    return cleaned_query, list(matched_genres)


def load_collections(db_path: str = "./lyrics_db", 
                    model_name: str = EMBEDDING_MODEL):
    """
    Load existing Chroma collections
    
    Args:
        db_path: Path to Chroma database
        model_name: Sentence transformer model
    
    Returns:
        Tuple of (client, songs_collection, sections_collection)
    """
    client = chromadb.PersistentClient(path=db_path)
    
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )
    
    songs = client.get_collection("songs", embedding_function=embedding_fn)
    sections = client.get_collection("sections", embedding_function=embedding_fn)
    
    return client, songs, sections


def search_songs(query: str,
                n_results: int = NUMBER_OF_SUGGESTIONS,
                db_path: str = "./lyrics_db",
                song_weight: float = DEFAULT_SONG_WEIGHT,
                section_weight: float = DEFAULT_SECTION_WEIGHT,
                genre_boost: float = DEFAULT_GENRE_BOOST,
                song_query_limit: int = SONG_QUERY_LIMIT,
                section_query_limit: int = SECTION_QUERY_LIMIT,
                use_genre_boosting: bool = True) -> List[Dict]:
    """
    Search for songs using hybrid approach with optional genre boosting
    
    Args:
        query: Search query text
        n_results: Number of results to return
        db_path: Path to Chroma database
        song_weight: Weight for song-level matches (0-1)
        section_weight: Weight for section-level matches (0-1)
        genre_boost: Multiplier for genre matches (e.g., 1.5 = 50% boost)
        song_query_limit: Max songs to query from collection
        section_query_limit: Max sections to query from collection
        use_genre_boosting: Whether to parse and boost by genres
    
    Returns:
        List of dicts with song info and scores, sorted by relevance
    """
    # Parse query for genres if boosting enabled
    search_query = query
    genre_filters = []
    if use_genre_boosting:
        search_query, genre_filters = parse_query_for_genres(query)
        if genre_filters:
            print(f"Detected genres: {genre_filters[:5]}...")  # Show first 5
            print(f"Cleaned query: '{search_query}'")
    
    # Use original query if cleaning removed everything
    if not search_query.strip():
        search_query = query
    
    _, songs_coll, sections_coll = load_collections(db_path)
    
    # Query song-level (overall mood/theme)
    song_results = songs_coll.query(
        query_texts=[search_query],
        n_results=min(song_query_limit, songs_coll.count())
    )
    
    # Query section-level (specific lyrics)
    section_results = sections_coll.query(
        query_texts=[search_query],
        n_results=min(section_query_limit, sections_coll.count())
    )
    
    # Score aggregation
    scores = defaultdict(lambda: {
        'song_score': 0, 
        'section_score': 0, 
        'metadata': None, 
        'sections': [],
        'genre_boosted': False
    })
    
    # Song-level scores (normalize by rank)
    for rank, (song_id, meta, dist) in enumerate(zip(
        song_results['ids'][0],
        song_results['metadatas'][0],
        song_results['distances'][0]
    )):
        scores[song_id]['song_score'] = (song_query_limit - rank) * song_weight
        scores[song_id]['metadata'] = meta
    
    # Section-level scores (best match per song + track matching sections)
    for rank, (section_id, meta, dist, doc) in enumerate(zip(
        section_results['ids'][0],
        section_results['metadatas'][0],
        section_results['distances'][0],
        section_results['documents'][0]
    )):
        song_id = meta['song_id']
        section_score = (section_query_limit - rank) * section_weight
        
        # Keep best section score
        if section_score > scores[song_id]['section_score']:
            scores[song_id]['section_score'] = section_score
        
        # Track matching sections
        scores[song_id]['sections'].append({
            'type': meta['section_type'],
            'number': meta.get('section_number'),
            'text': doc,
            'distance': dist,
            'score': section_score
        })
        
        # Add metadata if not already present
        if not scores[song_id]['metadata']:
            scores[song_id]['metadata'] = {
                'title': meta['title'],
                'artist': meta['artist']
            }
    
    # Calculate combined scores and apply genre boosting
    results = []
    for song_id, data in scores.items():
        combined_score = data['song_score'] + data['section_score']
        
        # Apply genre boost if genres match
        if use_genre_boosting and genre_filters and data['metadata']:
            genres_str = data['metadata'].get('genres', '')  # ✅ NEW - get as string
            if genres_str:
                # Split comma-separated string into list
                song_genres_lower = [g.strip().lower() for g in genres_str.split(',')]
                # Check if any song genre matches any filter genre
                if any(gf.lower() in sg for gf in genre_filters for sg in song_genres_lower):
                    combined_score *= genre_boost
                    data['genre_boosted'] = True
        
        # Sort sections by score
        data['sections'].sort(key=lambda x: x['score'], reverse=True)

        genres_str = data['metadata'].get('genres', '')
        genres_list = [g.strip() for g in genres_str.split(',')] if genres_str else []
        
        results.append({
            'song_id': song_id,
            'title': data['metadata']['title'],
            'artist': data['metadata']['artist'],
            'url': data['metadata'].get('url'),
            'genres': genres_list,
            'score': combined_score,
            'song_score': data['song_score'],
            'section_score': data['section_score'],
            'genre_boosted': data['genre_boosted'],
            'top_sections': data['sections'][:3]
        })
    
    # Sort by combined score
    results.sort(key=lambda x: x['score'], reverse=True)

    # Deduplicate
    seen_ids = set()
    unique_results = []
    for r in results:
        if r['song_id'] not in seen_ids:
            seen_ids.add(r['song_id'])
            unique_results.append(r)
    
    return unique_results[:n_results]


def search_sections_only(query: str,
                        n_results: int = 10,
                        db_path: str = "./lyrics_db") -> List[Dict]:
    """
    Search sections only (no song-level aggregation)
    
    Args:
        query: Search query text
        n_results: Number of section results
        db_path: Path to Chroma database
    
    Returns:
        List of matching sections with metadata
    """
    _, _, sections_coll = load_collections(db_path)
    
    results = sections_coll.query(
        query_texts=[query],
        n_results=n_results
    )
    
    sections = []
    for meta, dist, doc in zip(
        results['metadatas'][0],
        results['distances'][0],
        results['documents'][0]
    ):
        sections.append({
            'song_id': meta['song_id'],
            'title': meta['title'],
            'artist': meta['artist'],
            'section_type': meta['section_type'],
            'section_number': meta.get('section_number'),
            'text': doc,
            'distance': dist
        })
    
    return sections


def print_results(results: List[Dict], show_sections: bool = True):
    """
    Pretty print search results
    
    Args:
        results: Results from search_songs()
        show_sections: Whether to show matching section snippets
    """
    print(f"\nFound {len(results)} songs:\n")
    
    for i, result in enumerate(results, 1):
        boost_indicator = " 🎵" if result.get('genre_boosted') else ""
        print(f"{i}. {result['title']} - {result['artist']}{boost_indicator}")
        
        # Show genres if available
        if result.get('genres'):
            print(f"   Genres: {', '.join(result['genres'][:3])}")
        
        print(f"   Score: {result['score']:.2f} (song: {result['song_score']:.2f}, sections: {result['section_score']:.2f})")
        
        if show_sections and result['top_sections']:
            print(f"   Top matching section ({result['top_sections'][0]['type']}):")
            print(f"   \"{result['top_sections'][0]['text'][:100]}...\"")
        
        print()


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Search songs semantically')
    parser.add_argument('query', nargs='*', help='Search query')  # Changed to nargs='*'
    parser.add_argument('--genre-boost', type=float, default=1.5, 
                        help='Genre boost multiplier (default: 1.5, use 0 to disable)')
    parser.add_argument('-n', '--num-results', type=int, default=10,
                        help='Number of results (default: 10)')
    parser.add_argument('--stats', action='store_true',
                        help='Show database statistics')  # NEW
    
    args = parser.parse_args()
    
    # Show stats if requested
    if args.stats:
        _, songs_coll, sections_coll = load_collections()
        print(f"\nDatabase Statistics:")
        print(f"  Songs: {songs_coll.count()}")
        print(f"  Sections: {sections_coll.count()}")
        exit(0)
    
    # Require query if not showing stats
    if not args.query:
        parser.error("Query required (or use --stats)")
    
    query = " ".join(args.query)

    print(f"\n{'-'*60}")
    print(f"Query: '{query}'")
    print('_'*60)
    
    results = search_songs(
        query,
        n_results=args.num_results,
        genre_boost=args.genre_boost,
        use_genre_boosting=(args.genre_boost > 0)
    )
    print_results(results)