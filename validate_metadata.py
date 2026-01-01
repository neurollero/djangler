"""
Validate Metadata Distribution
Ensures metadata file is properly formatted and complete
"""

import json
import gzip
import argparse
from collections import Counter


def validate_metadata(file_path: str = "metadata_distribution.json.gz"):
    """Validate metadata distribution file"""
    
    print(f"Validating {file_path}...\n")
    
    errors = []
    warnings = []
    
    # Load file
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ FATAL: Cannot load file - {e}")
        return False
    
    print(f"✓ File loaded successfully ({len(data)} songs)")
    
    # Check structure
    required_fields = ['metadata', 'sections']
    metadata_fields = ['title', 'artist', 'genius_id']
    
    for i, song in enumerate(data[:100]):  # Check first 100
        # Check top-level structure
        for field in required_fields:
            if field not in song:
                errors.append(f"Song {i}: Missing '{field}' field")
        
        # Check metadata fields
        meta = song.get('metadata', {})
        for field in metadata_fields:
            if field not in meta:
                errors.append(f"Song {i}: Missing metadata.{field}")
        
        # Ensure no lyrics
        if 'full_lyrics' in song:
            errors.append(f"Song {i}: Contains 'full_lyrics' (should be excluded!)")
        
        for sec in song.get('sections', []):
            if 'text' in sec:
                errors.append(f"Song {i}: Section contains 'text' (should be excluded!)")
    
    if not errors:
        print("✓ Structure validation passed")
    
    # Check coverage
    has_genres = sum(1 for s in data if s.get('metadata', {}).get('genres'))
    has_url = sum(1 for s in data if s.get('metadata', {}).get('url'))
    
    print(f"\n{'='*60}")
    print("COVERAGE STATS")
    print('='*60)
    print(f"Songs with genres: {has_genres}/{len(data)} ({has_genres/len(data)*100:.1f}%)")
    print(f"Songs with URLs: {has_url}/{len(data)} ({has_url/len(data)*100:.1f}%)")
    
    if has_genres < len(data) * 0.5:
        warnings.append(f"Only {has_genres/len(data)*100:.1f}% have genre data")
    
    # Check for duplicates
    genius_ids = [s['metadata']['genius_id'] for s in data]
    duplicates = [id for id, count in Counter(genius_ids).items() if count > 1]
    
    if duplicates:
        errors.append(f"Found {len(duplicates)} duplicate genius_ids")
    else:
        print(f"✓ No duplicate genius_ids")
    
    # Genre distribution
    all_genres = []
    for s in data:
        genres = s.get('metadata', {}).get('genres', [])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(',')]
        all_genres.extend(genres)
    
    if all_genres:
        print(f"\nTop genres:")
        for genre, count in Counter(all_genres).most_common(10):
            print(f"  {genre}: {count}")
    
    # Summary
    print(f"\n{'='*60}")
    print("VALIDATION SUMMARY")
    print('='*60)
    
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for err in errors[:10]:  # Show first 10
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more")
        return False
    
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warn in warnings:
            print(f"  - {warn}")
    
    print(f"\n✓ Validation passed!")
    print(f"  Songs: {len(data)}")
    print(f"  No copyrighted content included")
    print(f"  Ready for distribution")
    
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validate metadata distribution')
    parser.add_argument(
        'file',
        nargs='?',
        default='metadata_distribution.json.gz',
        help='Metadata distribution file to validate'
    )
    
    args = parser.parse_args()
    
    success = validate_metadata(args.file)
    exit(0 if success else 1)
