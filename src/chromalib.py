"""
Chroma Embedding & Storage - Modular Pipeline
Embeds and stores song lyrics in vector database
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict

EMBEDDING_MODEL = "all-mpnet-base-v2" 
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def setup_chroma(db_path: str = "./lyrics_db") -> chromadb.PersistentClient:
    """
    Initialize Chroma persistent client
    
    Args:
        db_path: Path to store Chroma database
    
    Returns:
        Chroma client instance
    """
    client = chromadb.PersistentClient(path=db_path)
    print(f"Initialized Chroma database at {db_path}")
    return client


def create_collections(client: chromadb.PersistentClient, 
                      model_name: str = EMBEDDING_MODEL) -> tuple:
    """
    Create or get two collections: full songs and sections
    
    Args:
        client: Chroma client
        model_name: Sentence transformer model name
    
    Returns:
        Tuple of (songs_collection, sections_collection)
    """
    # Embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )
    
    # Create/get collections
    songs_collection = client.get_or_create_collection(
        name="songs",
        embedding_function=embedding_fn,
        metadata={"description": "Full song lyrics embeddings"}
    )
    
    sections_collection = client.get_or_create_collection(
        name="sections",
        embedding_function=embedding_fn,
        metadata={"description": "Song section embeddings (verse, chorus, etc.)"}
    )
    
    print(f"Collections ready: songs ({songs_collection.count()} docs), sections ({sections_collection.count()} docs)")
    
    return songs_collection, sections_collection


def embed_song(song, songs_collection, sections_collection):
    """
    Embed a single song and its sections
    
    Returns:
        'skipped' if already exists, 'embedded' if successful
    """
    # Handle nested metadata structure
    metadata = song.get('metadata', song)
    song_id = str(metadata.get('genius_id', metadata.get('id')))
    
    # Check if song already exists
    existing = songs_collection.get(ids=[song_id])
    if existing['ids']:
        return 'skipped'
    
    # Extract metadata
    title = metadata['title']
    artist = metadata['artist']
    
    # Embed full song
    full_text = song.get('full_lyrics', '')
    if full_text:
        songs_collection.add(
            documents=[full_text],
            metadatas=[{
                'title': title,
                'artist': artist,
                'genius_id': song_id,
                'genres': ', '.join(metadata.get('genres', [])),
                'artist_popularity': metadata.get('artist_popularity', 0)
            }],
            ids=[song_id]
        )
    
    # Embed individual sections
    sections = song.get('sections', [])
    documents = []
    metadatas = []
    ids = []
    
    for i, section in enumerate(sections):
        section_text = section.get('text', '')
        if section_text.strip():
            documents.append(section_text)
            metadatas.append({
                'title': title,
                'artist': artist,
                'section_type': section.get('section_type', 'unknown'),
                'section_number': i + 1,
                'song_id': song_id
            })
            ids.append(f"{song_id}_section_{i}")
    
    if documents:
        sections_collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    return 'embedded'

def load_and_embed_all(json_path: str = "songs_data.json", 
                       db_path: str = "./lyrics_db",
                       model_name: str = EMBEDDING_MODEL):
    """
    Complete pipeline: load JSON and embed all songs
    
    Args:
        json_path: Path to songs JSON file
        db_path: Path to Chroma database
        model_name: Sentence transformer model
    """
    # Load songs
    with open(json_path, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    print(f"Loaded {len(songs)} songs from {json_path}")
    
    # Setup Chroma
    client = setup_chroma(db_path)
    songs_collection, sections_collection = create_collections(client, model_name)
    
    # Track stats
    stats = {'embedded': 0, 'skipped': 0, 'failed': 0}
    
    # Embed each song with progress bar
    total = len(songs)
    for i, song_data in enumerate(songs, 1):
        try:
            result = embed_song(song_data, songs_collection, sections_collection)
            if result == 'skipped':
                stats['skipped'] += 1
            else:
                stats['embedded'] += 1
        except Exception as e:
            stats['failed'] += 1
            metadata = song_data.get('metadata', {})
            print(f"\n✗ Failed: '{metadata.get('title', 'Unknown')}' - {e}")
        
        # Progress bar
        if i % 100 == 0 or i == total:
            pct = i / total * 100
            bar_len = 40
            filled = int(bar_len * i / total)
            bar = '█' * filled + '░' * (bar_len - filled)
            print(f'\r{bar} {i}/{total} ({pct:.1f}%)', end='', flush=True)
    
    print(f"\n\n✓ Complete!")
    print(f"  Embedded: {stats['embedded']}")
    print(f"  Skipped:  {stats['skipped']} (already in DB)")
    print(f"  Failed:   {stats['failed']}")
    print(f"  Total DB: {songs_collection.count()} songs, {sections_collection.count()} sections")


def reset_collections(db_path: str = "./lyrics_db"):
    """
    Delete and recreate collections (useful for testing)
    
    Args:
        db_path: Path to Chroma database
    """
    client = chromadb.PersistentClient(path=db_path)
    
    try:
        client.delete_collection("songs")
        client.delete_collection("sections")
        print("✓ Collections deleted")
    except:
        print("Collections already empty")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Embed songs into ChromaDB')
    parser.add_argument('input', nargs='?', default='songs_data.json',
                       help='Input JSON file (default: songs_data.json)')
    parser.add_argument('--db-path', default='./lyrics_db',
                       help='ChromaDB path (default: ./lyrics_db)')
    parser.add_argument('--reset', action='store_true',
                       help='Reset collections before embedding')
    parser.add_argument('--model', default=EMBEDDING_MODEL,
                       help=f'Embedding model (default: {EMBEDDING_MODEL})')
    
    args = parser.parse_args()
    
    if args.reset:
        print("Resetting collections...")
        reset_collections(args.db_path)
    
    load_and_embed_all(
        json_path=args.input,
        db_path=args.db_path,
        model_name=args.model
    )
