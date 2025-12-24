"""
Extract subset of songs_data.json for testing
"""

import json
import argparse


def extract_subset(input_path: str, output_path: str, n: int):
    """Extract first n songs from songs_data.json"""
    with open(input_path, 'r', encoding='utf-8') as f:
        songs = json.load(f)
    
    subset = songs[:n]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(subset, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Extracted {len(subset)} songs from {input_path}")
    print(f"✓ Saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract subset of songs for testing')
    parser.add_argument('input', help='Input JSON file')
    parser.add_argument('n', type=int, help='Number of songs to extract')
    parser.add_argument('-o', '--output', help='Output file (default: test_songs.json)', 
                        default='test_songs.json')
    
    args = parser.parse_args()
    
    extract_subset(args.input, args.output, args.n)
