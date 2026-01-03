"""
Prune low-popularity songs from songs_data.json
Note: ChromaDB must be rebuilt from scratch (rm -rf lyrics_db/) to reclaim space
"""

import json
from pathlib import Path
import argparse


def prune_songs_data(input_path: str, output_path: str, min_popularity: int):
    """Remove songs below popularity threshold from songs_data.json"""
    with open(input_path, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    original_count = len(songs)
    
    # Filter by popularity
    filtered = [
        s for s in songs 
        if s.get('metadata', {}).get('artist_popularity', 0) >= min_popularity
    ]
    
    # Save filtered dataset
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, indent=2, ensure_ascii=False)
    
    removed = original_count - len(filtered)
    print(f"\nsongs_data.json:")
    print(f"  Original: {original_count} songs")
    print(f"  Filtered: {len(filtered)} songs")
    print(f"  Removed: {removed} ({removed/original_count*100:.1f}%)")
    
    # Show popularity distribution
    pops = [s['metadata'].get('artist_popularity', 0) for s in filtered]
    print(f"\nFiltered dataset stats:")
    print(f"  Min popularity: {min(pops)}")
    print(f"  Avg popularity: {sum(pops)/len(pops):.1f}")
    print(f"  Max popularity: {max(pops)}")
    
    print(f"\n✓ Saved to {output_path}")
    print(f"\nNext steps:")
    print(f"  1. rm -rf lyrics_db/")
    print(f"  2. python src/chromalib.py {output_path}")
    
    return filtered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Prune low-popularity songs from songs_data.json'
    )
    parser.add_argument('--min-pop', type=int, default=50,
                        help='Minimum popularity threshold (default: 50)')
    parser.add_argument('--songs-input', default='songs_data.json',
                        help='Input songs_data.json')
    parser.add_argument('--songs-output', default='songs_data_pruned.json',
                        help='Output songs_data.json')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be removed without saving')
    
    args = parser.parse_args()
    
    if args.dry_run:
        with open(args.songs_input) as f:
            songs = json.load(f)
        to_remove = sum(1 for s in songs 
                       if s.get('metadata', {}).get('artist_popularity', 0) < args.min_pop)
        print(f"\nDry run: min_popularity >= {args.min_pop}")
        print(f"Would remove: {to_remove}/{len(songs)} songs ({to_remove/len(songs)*100:.1f}%)")
        print(f"Would keep: {len(songs) - to_remove} songs")
    else:
        print(f"Pruning songs with popularity < {args.min_pop}")
        prune_songs_data(args.songs_input, args.songs_output, args.min_pop)