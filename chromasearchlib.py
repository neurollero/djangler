"""
Search Module - Query songs and sections
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Optional
from collections import defaultdict

QUERY = ["stroking breasts"]

NUMBER_OF_SUGGESTIONS = 10

EMBEDDING_MODEL = "all-mpnet-base-v2" 
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Search configuration constants
SONG_QUERY_LIMIT = 50
SECTION_QUERY_LIMIT = 100
DEFAULT_SONG_WEIGHT = 0.5
DEFAULT_SECTION_WEIGHT = 0.6

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
                song_query_limit: int = SONG_QUERY_LIMIT,
                section_query_limit: int = SECTION_QUERY_LIMIT) -> List[Dict]:
    """
    Search for songs using hybrid approach: query both collections and merge
    
    Args:
        query: Search query text
        n_results: Number of results to return
        db_path: Path to Chroma database
        song_weight: Weight for song-level matches (0-1)
        section_weight: Weight for section-level matches (0-1)
        song_query_limit: Max songs to query from collection
        section_query_limit: Max sections to query from collection
    
    Returns:
        List of dicts with song info and scores, sorted by relevance
    """
    _, songs_coll, sections_coll = load_collections(db_path)
    
    # Query song-level (overall mood/theme)
    song_results = songs_coll.query(
        query_texts=[query],
        n_results=min(song_query_limit, songs_coll.count())
    )
    
    # Query section-level (specific lyrics)
    section_results = sections_coll.query(
        query_texts=[query],
        n_results=min(section_query_limit, sections_coll.count())
    )
    
    # Score aggregation
    scores = defaultdict(lambda: {'song_score': 0, 'section_score': 0, 'metadata': None, 'sections': []})
    
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
    
    # Calculate combined scores and format results
    results = []
    for song_id, data in scores.items():
        combined_score = data['song_score'] + data['section_score']
        
        # Sort sections by score
        data['sections'].sort(key=lambda x: x['score'], reverse=True)
        
        results.append({
            'song_id': song_id,
            'title': data['metadata']['title'],
            'artist': data['metadata']['artist'],
            'url': data['metadata'].get('url'),
            'score': combined_score,
            'song_score': data['song_score'],
            'section_score': data['section_score'],
            'top_sections': data['sections'][:3]  # Top 3 matching sections
        })
    
    # Sort by combined score
    results.sort(key=lambda x: x['score'], reverse=True)

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
        print(f"{i}. {result['title']} - {result['artist']}")
        print(f"   Score: {result['score']:.2f} (song: {result['song_score']:.2f}, sections: {result['section_score']:.2f})")
        
        if show_sections and result['top_sections']:
            print(f"   Top matching section ({result['top_sections'][0]['type']}):")
            print(f"   \"{result['top_sections'][0]['text'][:100]}...\"")
        
        print()


# Example usage
if __name__ == "__main__":
    # Test queries
    queries = QUERY
    
    for query in queries:
        print(f"\n{'-'*60}")
        print(f"Query: '{query}'")
        print('_'*60)
        
        results = search_songs(query, n_results=NUMBER_OF_SUGGESTIONS)
        print_results(results)