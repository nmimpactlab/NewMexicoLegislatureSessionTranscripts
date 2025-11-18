#!/usr/bin/env python3
"""
Named Entity Recognition - Full Dataset Processor

Processes all legislative transcripts and exports results to CSV and JSON formats.
"""

import re
import json
import csv
from pathlib import Path
from collections import Counter, defaultdict
from typing import Set, List, Dict, Tuple
import argparse
from datetime import datetime

# Import the WaveExtractor from ner_poc
from ner_poc import WaveExtractor


def find_all_transcripts(base_dir: Path = Path('.')) -> List[Path]:
    """Find all transcript files in the repository"""
    transcript_files = []

    # Search in committee directories
    for txt_file in base_dir.glob('**/*.cc.txt'):
        # Skip the maybedupes directory
        if 'maybedupes' not in str(txt_file):
            transcript_files.append(txt_file)

    return sorted(transcript_files)


def export_to_csv(results: Dict, output_file: str):
    """Export validated names to CSV format"""
    validated = results.get('wave6_validated', {})
    normalized = results.get('wave7_normalized', {})

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Name',
            'Frequency',
            'Variants',
            'Confidence_Level'
        ])

        # Sort by frequency (descending)
        sorted_names = sorted(normalized.items(),
                            key=lambda x: x[1][0],
                            reverse=True)

        for canonical_name, (total_count, variants) in sorted_names:
            # Determine confidence level based on frequency
            if total_count >= 10:
                confidence = 'High'
            elif total_count >= 3:
                confidence = 'Medium'
            else:
                confidence = 'Low'

            # Format variants (excluding the canonical name itself)
            variant_list = [v for v in variants if v != canonical_name]
            variants_str = '; '.join(variant_list) if variant_list else ''

            writer.writerow([
                canonical_name,
                total_count,
                variants_str,
                confidence
            ])


def export_to_json(results: Dict, output_file: str, metadata: Dict):
    """Export complete results to structured JSON format"""
    validated = results.get('wave6_validated', {})
    normalized = results.get('wave7_normalized', {})

    # Build structured output
    output = {
        'metadata': {
            'extraction_date': metadata.get('extraction_date', datetime.now().isoformat()),
            'total_files_processed': metadata.get('total_files', 0),
            'total_characters_processed': metadata.get('total_chars', 0),
            'min_frequency_threshold': metadata.get('min_frequency', 1),
            'total_names_found': len(normalized),
            'extraction_settings': {
                'wave_count': 7,
                'handles_multi_word_names': True,
                'handles_ocr_errors': True,
                'max_words_per_name': 4
            }
        },
        'summary_statistics': {
            'high_confidence': sum(1 for _, (count, _) in normalized.items() if count >= 10),
            'medium_confidence': sum(1 for _, (count, _) in normalized.items() if 3 <= count < 10),
            'low_confidence': sum(1 for _, (count, _) in normalized.items() if count < 3),
        },
        'entities': []
    }

    # Add each entity with full details
    for canonical_name, (total_count, variants) in sorted(normalized.items(),
                                                          key=lambda x: x[1][0],
                                                          reverse=True):
        entity = {
            'name': canonical_name,
            'frequency': total_count,
            'confidence_level': (
                'high' if total_count >= 10 else
                'medium' if total_count >= 3 else
                'low'
            ),
            'variants': [v for v in variants if v != canonical_name]
        }
        output['entities'].append(entity)

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description='Extract person names from legislative transcripts'
    )
    parser.add_argument(
        '--min-frequency',
        type=int,
        default=1,
        help='Minimum number of mentions required (default: 1)'
    )
    parser.add_argument(
        '--output-prefix',
        type=str,
        default='extracted_names',
        help='Prefix for output files (default: extracted_names)'
    )
    parser.add_argument(
        '--sample',
        type=int,
        default=None,
        help='Process only N files (for testing)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress for each wave'
    )

    args = parser.parse_args()

    print("="*70)
    print("  LEGISLATIVE TRANSCRIPT NAME EXTRACTION")
    print("="*70)
    print()

    # Find all transcript files
    print("Searching for transcript files...")
    all_files = find_all_transcripts()

    if args.sample:
        all_files = all_files[:args.sample]
        print(f"Processing {args.sample} files (sample mode)")
    else:
        print(f"Found {len(all_files)} transcript files")

    print()

    # Load and combine all transcripts
    print("Loading transcripts...")
    combined_text = []
    total_chars = 0

    for i, file_path in enumerate(all_files, 1):
        if i % 100 == 0 or i == len(all_files):
            print(f"  Loaded {i}/{len(all_files)} files...", end='\r')

        try:
            text = file_path.read_text(encoding='utf-8', errors='ignore')
            combined_text.append(text)
            total_chars += len(text)
        except Exception as e:
            print(f"\n  Warning: Could not read {file_path}: {e}")

    print(f"\n  Total: {total_chars:,} characters from {len(all_files)} files")
    print()

    # Run extraction
    full_text = '\n\n'.join(combined_text)
    extractor = WaveExtractor(full_text, verbose=args.verbose)

    print("Running 7-wave extraction process...")
    print(f"  Minimum frequency threshold: {args.min_frequency}")
    print()

    results = extractor.run_all_waves(min_frequency=args.min_frequency)

    # Prepare metadata
    metadata = {
        'extraction_date': datetime.now().isoformat(),
        'total_files': len(all_files),
        'total_chars': total_chars,
        'min_frequency': args.min_frequency
    }

    # Export to CSV
    csv_file = f'{args.output_prefix}.csv'
    print(f"\nExporting to {csv_file}...")
    export_to_csv(results, csv_file)

    # Export to JSON
    json_file = f'{args.output_prefix}.json'
    print(f"Exporting to {json_file}...")
    export_to_json(results, json_file, metadata)

    # Print summary
    normalized = results.get('wave7_normalized', {})
    validated = results.get('wave6_validated', {})

    print()
    print("="*70)
    print("  EXTRACTION COMPLETE")
    print("="*70)
    print(f"Total validated names: {len(validated)}")
    print(f"Total unique entities (after deduplication): {len(normalized)}")
    print()

    # Show confidence breakdown
    high_conf = sum(1 for _, (count, _) in normalized.items() if count >= 10)
    med_conf = sum(1 for _, (count, _) in normalized.items() if 3 <= count < 10)
    low_conf = sum(1 for _, (count, _) in normalized.items() if count < 3)

    print("Confidence breakdown:")
    print(f"  High confidence (≥10 mentions):  {high_conf:4d}")
    print(f"  Medium confidence (3-9):         {med_conf:4d}")
    print(f"  Low confidence (1-2):            {low_conf:4d}")
    print()

    # Show top 20
    print("Top 20 names by frequency:")
    sorted_names = sorted(normalized.items(), key=lambda x: x[1][0], reverse=True)
    for i, (name, (count, variants)) in enumerate(sorted_names[:20], 1):
        variant_info = f" ({len(variants)} variants)" if len(variants) > 1 else ""
        print(f"  {i:2d}. {name:30s} {count:4d} mentions{variant_info}")

    print()
    print(f"Output files:")
    print(f"  - {csv_file} (CSV for spreadsheets)")
    print(f"  - {json_file} (JSON with full metadata)")
    print()


if __name__ == '__main__':
    main()
