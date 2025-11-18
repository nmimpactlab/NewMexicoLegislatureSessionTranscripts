#!/usr/bin/env python3
"""
Extract Bill References from Legislative Transcripts

This tool extracts and analyzes references to legislation (bills, resolutions,
memorials) from New Mexico Legislature session transcripts.

Bill types supported:
- HB = House Bill
- SB = Senate Bill
- HJR = House Joint Resolution
- SJR = Senate Joint Resolution
- HM = House Memorial
- SM = Senate Memorial
- HCR = House Concurrent Resolution
- SCR = Senate Concurrent Resolution
- HJRC = House Joint Resolution Constitutional Amendment
- SJRC = Senate Joint Resolution Constitutional Amendment

Usage:
    python extract_bill_references.py [--sample N] [--output bills] [--verbose]

Example:
    # Extract from all transcripts
    python extract_bill_references.py --output bills_all

    # Test on 10 transcripts
    python extract_bill_references.py --sample 10 --output bills_test
"""

import re
import json
import csv
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
import argparse


# New Mexico bill type patterns
BILL_TYPES = {
    'HB': 'House Bill',
    'SB': 'Senate Bill',
    'HJR': 'House Joint Resolution',
    'SJR': 'Senate Joint Resolution',
    'HM': 'House Memorial',
    'SM': 'Senate Memorial',
    'HCR': 'House Concurrent Resolution',
    'SCR': 'Senate Concurrent Resolution',
    'HJRC': 'House Joint Resolution Constitutional Amendment',
    'SJRC': 'Senate Joint Resolution Constitutional Amendment',
}


def extract_bill_references(text: str, verbose: bool = False) -> List[Tuple[str, str, str]]:
    """
    Extract bill references from text

    Returns: List of (bill_type, bill_number, full_match) tuples
    """

    bills = []

    # Pattern 1: Standard format "HB 123" or "HB123"
    # Matches: HB 123, SB 456, HJR 7, etc.
    pattern1 = r'\b(' + '|'.join(BILL_TYPES.keys()) + r')\s*(\d{1,4})([A-Z]{0,2})\b'

    for match in re.finditer(pattern1, text, re.IGNORECASE):
        bill_type = match.group(1).upper()
        bill_number = match.group(2)
        suffix = match.group(3).upper() if match.group(3) else ''
        full_match = match.group(0)

        # Normalize: "HB 123" or "HB 123A"
        normalized = f"{bill_type} {bill_number}{suffix}"

        bills.append((bill_type, normalized, full_match))

    # Pattern 2: Long form "House Bill 123", "Senate Bill 456"
    long_forms = {
        'House Bill': 'HB',
        'Senate Bill': 'SB',
        'House Joint Resolution': 'HJR',
        'Senate Joint Resolution': 'SJR',
        'House Memorial': 'HM',
        'Senate Memorial': 'SM',
        'House Concurrent Resolution': 'HCR',
        'Senate Concurrent Resolution': 'SCR',
    }

    pattern2 = r'\b(' + '|'.join(long_forms.keys()) + r')\s+(\d{1,4})([A-Z]{0,2})\b'

    for match in re.finditer(pattern2, text, re.IGNORECASE):
        long_form = match.group(1)
        bill_number = match.group(2)
        suffix = match.group(3).upper() if match.group(3) else ''
        full_match = match.group(0)

        # Convert to short form
        bill_type = long_forms.get(long_form.title(), long_form.upper())
        normalized = f"{bill_type} {bill_number}{suffix}"

        bills.append((bill_type, normalized, full_match))

    return bills


def process_transcripts(transcript_dir: Path, sample_size: int = None, verbose: bool = False) -> Dict:
    """
    Process all transcripts and extract bill references

    Returns: {
        'bill_id': {
            'bill_type': 'HB',
            'bill_id': 'HB 123',
            'frequency': 10,
            'transcripts': [list of files mentioning this bill],
            'variants': [list of different ways it was mentioned]
        }
    }
    """

    # Find all transcript files (including in subdirectories)
    txt_files = sorted(transcript_dir.glob('**/*.txt'))

    if sample_size:
        txt_files = txt_files[:sample_size]

    if verbose:
        print(f"\nProcessing {len(txt_files)} transcript files...")

    # Track all bills
    bill_data = defaultdict(lambda: {
        'bill_type': '',
        'bill_id': '',
        'frequency': 0,
        'transcripts': [],
        'variants': set(),
    })

    for i, txt_file in enumerate(txt_files, 1):
        if verbose and i % 100 == 0:
            print(f"  Processed {i}/{len(txt_files)} files...")

        try:
            with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()

            # Extract bills from this transcript
            bills = extract_bill_references(text, verbose=False)

            # Track unique bills in this file
            file_bills = set()

            for bill_type, normalized, full_match in bills:
                file_bills.add(normalized)
                bill_data[normalized]['bill_type'] = bill_type
                bill_data[normalized]['bill_id'] = normalized
                bill_data[normalized]['variants'].add(full_match)

            # Increment frequency for each unique bill in this file
            for bill_id in file_bills:
                bill_data[bill_id]['frequency'] += 1
                bill_data[bill_id]['transcripts'].append(txt_file.name)

        except Exception as e:
            if verbose:
                print(f"  Error processing {txt_file.name}: {e}")

    if verbose:
        print(f"\n✓ Processed {len(txt_files)} files")
        print(f"✓ Found {len(bill_data)} unique bills")

    # Convert sets to lists for JSON serialization
    for bill_id in bill_data:
        bill_data[bill_id]['variants'] = sorted(bill_data[bill_id]['variants'])

    return dict(bill_data)


def export_to_json(bill_data: Dict, output_file: str):
    """Export bill data to JSON"""

    # Sort by frequency
    sorted_bills = sorted(
        bill_data.items(),
        key=lambda x: x[1]['frequency'],
        reverse=True
    )

    output = {
        'metadata': {
            'total_unique_bills': len(bill_data),
            'total_mentions': sum(b['frequency'] for b in bill_data.values()),
            'bill_types': dict(Counter(b['bill_type'] for b in bill_data.values())),
        },
        'bills': dict(sorted_bills)
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported to JSON: {output_file}")


def export_to_csv(bill_data: Dict, output_file: str):
    """Export bill data to CSV"""

    # Sort by frequency
    sorted_bills = sorted(
        bill_data.items(),
        key=lambda x: x[1]['frequency'],
        reverse=True
    )

    fieldnames = [
        'bill_id', 'bill_type', 'full_name', 'frequency',
        'num_transcripts', 'variants'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for bill_id, data in sorted_bills:
            bill_type = data['bill_type']
            full_name = BILL_TYPES.get(bill_type, bill_type)

            writer.writerow({
                'bill_id': bill_id,
                'bill_type': bill_type,
                'full_name': full_name,
                'frequency': data['frequency'],
                'num_transcripts': len(data['transcripts']),
                'variants': '; '.join(data['variants'][:5])  # Limit variants in CSV
            })

    print(f"✓ Exported to CSV: {output_file}")


def export_detailed_csv(bill_data: Dict, output_file: str):
    """Export detailed bill-to-transcript mapping"""

    # Sort by frequency
    sorted_bills = sorted(
        bill_data.items(),
        key=lambda x: x[1]['frequency'],
        reverse=True
    )

    fieldnames = ['bill_id', 'bill_type', 'transcript_file']

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for bill_id, data in sorted_bills:
            for transcript in data['transcripts']:
                writer.writerow({
                    'bill_id': bill_id,
                    'bill_type': data['bill_type'],
                    'transcript_file': transcript
                })

    print(f"✓ Exported detailed mapping: {output_file}")


def print_statistics(bill_data: Dict):
    """Print statistics about extracted bills"""

    print("\n" + "=" * 70)
    print("Bill Extraction Statistics")
    print("=" * 70)

    total_bills = len(bill_data)
    total_mentions = sum(b['frequency'] for b in bill_data.values())

    print(f"\nTotal unique bills: {total_bills}")
    print(f"Total mentions: {total_mentions}")

    # By bill type
    by_type = Counter(b['bill_type'] for b in bill_data.values())

    print("\nBills by Type:")
    for bill_type, count in sorted(by_type.items()):
        full_name = BILL_TYPES.get(bill_type, bill_type)
        print(f"  {bill_type:6s} ({full_name:40s}): {count:4d}")

    # Top 20 most mentioned bills
    sorted_bills = sorted(
        bill_data.items(),
        key=lambda x: x[1]['frequency'],
        reverse=True
    )

    print("\nTop 20 Most Mentioned Bills:")
    for i, (bill_id, data) in enumerate(sorted_bills[:20], 1):
        bill_type = data['bill_type']
        full_name = BILL_TYPES.get(bill_type, bill_type)
        freq = data['frequency']
        num_files = len(data['transcripts'])

        print(f"{i:2d}. {bill_id:12s} | {full_name:35s} | {freq:4d} mentions in {num_files:3d} files")


def main():
    parser = argparse.ArgumentParser(
        description='Extract bill references from legislative transcripts'
    )
    parser.add_argument('--transcripts', default='.',
                        help='Directory containing transcript files (default: current directory)')
    parser.add_argument('--sample', type=int,
                        help='Process only N sample files (for testing)')
    parser.add_argument('--output', default='bills_extracted',
                        help='Output file prefix (default: bills_extracted)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    transcript_dir = Path(args.transcripts)

    if not transcript_dir.exists():
        print(f"✗ Directory not found: {transcript_dir}")
        return

    print("=" * 70)
    print("New Mexico Legislature - Bill Reference Extractor")
    print("=" * 70)

    # Extract bills
    bill_data = process_transcripts(
        transcript_dir,
        sample_size=args.sample,
        verbose=args.verbose
    )

    if not bill_data:
        print("\n✗ No bills found")
        return

    # Print statistics
    print_statistics(bill_data)

    # Export
    print("\n" + "=" * 70)
    print("Exporting Results")
    print("=" * 70 + "\n")

    export_to_json(bill_data, f'{args.output}.json')
    export_to_csv(bill_data, f'{args.output}.csv')
    export_detailed_csv(bill_data, f'{args.output}_detailed.csv')

    print("\n" + "=" * 70)
    print("✓ Extraction Complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
