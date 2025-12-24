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


def embed_song(song_data: Dict, songs_collection, sections_collection):
    """
    Embed and store a single song in both collections
    
    Args:
        song_data: Song dict from genius_scraper output
        songs_collection: Chroma collection for full songs
        sections_collection: Chroma collection for sections
    """
    try:
        metadata = song_data['metadata']
        song_id = str(metadata['genius_id'])
        
        # Clean metadata - ensure no None values
        clean_meta = {
            'title': str(metadata.get('title') or 'Unknown'),
            'artist': str(metadata.get('artist') or 'Unknown'),
            'url': str(metadata.get('url') or ''),
            'release_date': str(metadata.get('release_date') or 'Unknown')
        }
        
        # 1. Store full song
        songs_collection.add(
            documents=[song_data['full_lyrics']],
            metadatas=[clean_meta],
            ids=[song_id]
        )
        
        # 2. Store sections
        section_docs = []
        section_metas = []
        section_ids = []
        
        for i, section in enumerate(song_data['sections']):
            section_id = f"{song_id}_section_{i}"
            
            section_docs.append(section['text'])
            section_metas.append({
                'song_id': song_id,
                'title': str(metadata.get('title') or 'Unknown'),
                'artist': str(metadata.get('artist') or 'Unknown'),
                'section_type': str(section.get('section_type') or 'unknown'),
                'section_number': int(section.get('section_number') or 0)
            })
            section_ids.append(section_id)
        
        if section_docs:
            sections_collection.add(
                documents=section_docs,
                metadatas=section_metas,
                ids=section_ids
            )
        
        print(f"✓ Embedded: '{clean_meta['title']}' by {clean_meta['artist']} ({len(section_docs)} sections)")
        
    except Exception as e:
        title = song_data.get('metadata', {}).get('title', 'Unknown')
        print(f"⚠️  Skipping '{title}': {str(e)}")
        print(f"    Metadata: {song_data.get('metadata', {})}")

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
    
    # Embed each song
    for song_data in songs:
        embed_song(song_data, songs_collection, sections_collection)
    
    print(f"\n✓ Embedded all {len(songs)} songs!")
    print(f"  - Songs collection: {songs_collection.count()} documents")
    print(f"  - Sections collection: {sections_collection.count()} documents")


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
    # Option 1: Load and embed all songs
    load_and_embed_all()
    
    # Option 2: Reset and start fresh
    # reset_collections()
    # load_and_embed_all()