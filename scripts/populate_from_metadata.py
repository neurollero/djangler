"""
Populate Lyrics from Metadata Distribution
Fetches lyrics for metadata-only dataset using Genius API
"""

import json
import gzip
import time
import argparse
from pathlib import Path
from fetchlib import fetch_lyrics, parse_sections, clean_lyrics
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def populate_from_metadata(
    metadata_path: str = "metadata_distribution.json.gz",
    output_path: str = "songs_data.json",
    genius_token: str = None,
    checkpoint_frequency: int = 100
):
    """
    Repopulate lyrics from metadata distribution
    
    Args:
        metadata_path: Path to compressed metadata file
        output_path: Path for complete songs_data.json
        genius_token: Genius API access token
        checkpoint_frequency: Save progress every N songs
    """
    if not genius_token:
        raise ValueError("Genius API token required. Set GENIUS_ACCESS_TOKEN env var or pass --token")
    
    # Load metadata
    print(f"Loading metadata from {metadata_path}...")
    with gzip.open(metadata_path, 'rt', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"Loaded {len(metadata)} songs")
    
    # Check if output exists (resume capability)
    if Path(output_path).exists():
        print(f"\nFound existing {output_path}, resuming...")
        with open(output_path, 'r', encoding='utf-8') as f:
            populated = json.load(f)
        
        # Track already processed songs
        processed_ids = {s['metadata']['genius_id'] for s in populated}
        print(f"Already processed: {len(processed_ids)} songs")
    else:
        populated = []
        processed_ids = set()
    
    # Process songs
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, song_meta in enumerate(metadata):
        meta = song_meta['metadata']
        genius_id = meta.get('genius_id')
        
        # Skip if already processed
        if genius_id in processed_ids:
            skip_count += 1
            continue
        
        # Progress tracking
        if (i + 1) % 50 == 0:
            print(f"\nProgress: {i + 1}/{len(metadata)}")
            print(f"  Success: {success_count}, Skipped: {skip_count}, Failed: {fail_count}")
        
        print(f"Fetching: '{meta['title']}' by {meta['artist']}")
        
        # Fetch lyrics from Genius
        try:
            result = fetch_lyrics(
                song_title=meta['title'],
                artist=meta['artist'],
                access_token=genius_token,
                timeout=15
            )
            
            if result:
                # Parse sections
                sections = parse_sections(result['lyrics'])
                
                # Clean sections
                for section in sections:
                    section['text'] = clean_lyrics(section['text'])
                
                # Combine with original metadata
                populated.append({
                    'metadata': meta,  # Keep original metadata
                    'sections': sections,
                    'full_lyrics': clean_lyrics(result['lyrics'])
                })
                
                success_count += 1
                processed_ids.add(genius_id)
            else:
                fail_count += 1
                print(f"  ⚠️  Failed to fetch lyrics")
            
            # Rate limiting
            time.sleep(0.1)
            
        except Exception as e:
            fail_count += 1
            print(f"  ⚠️  Error: {str(e)}")
            time.sleep(0.5)  # Longer pause on error
        
        # Checkpoint saves
        if (i + 1) % checkpoint_frequency == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(populated, f, indent=2, ensure_ascii=False)
            print(f"  💾 Saved checkpoint ({len(populated)} songs)")
    
    # Final save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(populated, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("POPULATION COMPLETE")
    print('='*60)
    print(f"Total processed: {len(populated)}/{len(metadata)}")
    print(f"Success: {success_count}")
    print(f"Skipped: {skip_count}")
    print(f"Failed: {fail_count}")
    print(f"\nOutput: {output_path}")
    
    # File size
    size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    print(f"Size: {size_mb:.2f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Populate lyrics from metadata distribution using Genius API'
    )
    parser.add_argument(
        'metadata',
        nargs='?',
        default='metadata_distribution.json.gz',
        help='Compressed metadata file'
    )
    parser.add_argument(
        '-o', '--output',
        default='songs_data.json',
        help='Output file for complete dataset'
    )
    parser.add_argument(
        '--token',
        help='Genius API access token (or set GENIUS_ACCESS_TOKEN env var)'
    )
    parser.add_argument(
        '--checkpoint-freq',
        type=int,
        default=100,
        help='Save checkpoint every N songs'
    )
    
    args = parser.parse_args()
    
    # Get token from args or environment
    import os
    token = args.token or os.getenv('GENIUS_ACCESS_TOKEN')
    
    if not token:
        print("Error: Genius API token required!")
        print("\nOptions:")
        print("  1. Set environment variable: export GENIUS_ACCESS_TOKEN='your_token'")
        print("  2. Pass via command line: --token YOUR_TOKEN")
        print("\nGet a token at: https://genius.com/api-clients")
        exit(1)
    
    populate_from_metadata(
        metadata_path=args.metadata,
        output_path=args.output,
        genius_token=token,
        checkpoint_frequency=args.checkpoint_freq
    )
