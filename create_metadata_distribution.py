"""
Create Metadata-Only Distribution
Exports song metadata without copyrighted lyrics for legal distribution
"""

import json
import gzip
import argparse
from pathlib import Path


def create_metadata_distribution(
    input_path: str = "songs_data.json",
    output_path: str = "metadata_distribution.json.gz"
):
    """
    Extract metadata without lyrics for distribution
    
    Args:
        input_path: Path to full songs_data.json
        output_path: Path for compressed metadata output
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    print(f"Loaded {len(songs)} songs from {input_path}")
    
    # Extract metadata only (no lyrics)
    metadata_only = []
    
    for song in songs:
        metadata_only.append({
            'metadata': song['metadata'],
            'sections': [
                {
                    'section_type': sec['section_type'],
                    'section_number': sec.get('section_number')
                }
                for sec in song['sections']
            ]
        })
    
    # Write compressed JSON (compact format)
    with gzip.open(output_path, 'wt', encoding='utf-8') as f:
        json.dump(metadata_only, f, separators=(',', ':'), ensure_ascii=False)
    
    # Report sizes
    original_size = Path(input_path).stat().st_size / (1024 * 1024)
    compressed_size = Path(output_path).stat().st_size / (1024 * 1024)
    
    print(f"\n✓ Created metadata distribution:")
    print(f"  Songs: {len(metadata_only)}")
    print(f"  Original size: {original_size:.2f} MB")
    print(f"  Compressed size: {compressed_size:.2f} MB")
    print(f"  Reduction: {(1 - compressed_size/original_size) * 100:.1f}%")
    print(f"  Output: {output_path}")


def inspect_metadata_distribution(file_path: str = "metadata_distribution.json.gz"):
    """Show what's included in the metadata distribution"""
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        metadata = json.load(f)
    
    print(f"\n{'='*60}")
    print("METADATA DISTRIBUTION CONTENTS")
    print('='*60)
    print(f"\nTotal songs: {len(metadata)}")
    
    # Sample entry
    print(f"\nSample entry structure:")
    print(json.dumps(metadata[0], indent=2))
    
    # Check what's included
    sample = metadata[0]['metadata']
    print(f"\nIncluded fields:")
    for key in sample.keys():
        print(f"  ✓ {key}")
    
    print(f"\nExcluded:")
    print(f"  ✗ full_lyrics (copyrighted)")
    print(f"  ✗ sections.text (copyrighted)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Create metadata-only distribution without copyrighted lyrics'
    )
    parser.add_argument(
        'input',
        nargs='?',
        default='songs_data.json',
        help='Input songs_data.json file'
    )
    parser.add_argument(
        '-o', '--output',
        default='metadata_distribution.json.gz',
        help='Output compressed file'
    )
    parser.add_argument(
        '--inspect',
        action='store_true',
        help='Inspect existing metadata distribution'
    )
    
    args = parser.parse_args()
    
    if args.inspect:
        inspect_metadata_distribution(args.output)
    else:
        create_metadata_distribution(args.input, args.output)
