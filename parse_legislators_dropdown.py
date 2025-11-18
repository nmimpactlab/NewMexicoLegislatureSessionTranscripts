#!/usr/bin/env python3
"""
Parse Legislator Data from nmlegis.gov Dropdown

The legislator list page uses a dropdown select menu with this structure:
<option value="HABMI">Michelle Paulene Abeyta</option>

Instructions:
1. Visit https://www.nmlegis.gov/members/Legislator_List?T=R
2. Right-click -> "Inspect" or press F12
3. Find the <select> element with legislator options
4. Right-click the <select> element -> Copy -> Copy element
5. Save to a file (e.g., legislators_dropdown.html)
6. Run: python parse_legislators_dropdown.py legislators_dropdown.html

Or simply copy all the <option> tags and paste into a text file.

Usage:
    python parse_legislators_dropdown.py <html_file> [--output legislators_official]
"""

import argparse
import json
import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup
import time
from typing import List, Dict


def parse_dropdown_html(html_file: Path) -> List[Dict]:
    """Parse legislators from dropdown select HTML"""

    print(f"\nParsing: {html_file}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    legislators = []

    # Find all option elements
    options = soup.find_all('option')
    print(f"Found {len(options)} option elements")

    for option in options:
        # Skip placeholder options
        if option.get('disabled') or 'select' in option.get_text().lower():
            continue

        legislator_id = option.get('value', '').strip()
        full_name = option.get_text(strip=True)

        if not full_name or not legislator_id:
            continue

        # Parse the legislator ID to extract chamber info
        # Format appears to be: H = House, S = Senate, followed by codes
        chamber = 'Unknown'
        if legislator_id.startswith('H'):
            chamber = 'House'
        elif legislator_id.startswith('S'):
            chamber = 'Senate'

        # Parse name
        name_parts = full_name.split()
        last_name = name_parts[-1] if name_parts else ''
        first_name = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else ''

        legislator = {
            'full_name': full_name,
            'first_name': first_name,
            'last_name': last_name,
            'legislator_id': legislator_id,
            'chamber': chamber,
            'party': 'Unknown',  # Not in dropdown, will need to fetch from detail page
            'district': 'Unknown',
            'status': 'current',
            'source': 'nmlegis.gov/members/Legislator_List'
        }

        legislators.append(legislator)

    print(f"✓ Extracted {len(legislators)} legislators")
    return legislators


def export_to_json(legislators: List[Dict], output_file: str):
    """Export legislators to JSON"""

    output = {
        'metadata': {
            'source': 'nmlegis.gov dropdown select parser',
            'total_legislators': len(legislators),
            'house': sum(1 for l in legislators if l.get('chamber') == 'House'),
            'senate': sum(1 for l in legislators if l.get('chamber') == 'Senate'),
            'extraction_date': time.strftime('%Y-%m-%d'),
            'note': 'Party and district info not available in dropdown - requires detail page scraping'
        },
        'legislators': legislators
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported to JSON: {output_file}")


def export_to_csv(legislators: List[Dict], output_file: str):
    """Export legislators to CSV"""

    if not legislators:
        print("No legislators to export")
        return

    fieldnames = [
        'full_name', 'last_name', 'first_name', 'legislator_id',
        'chamber', 'party', 'district', 'status', 'source'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(legislators)

    print(f"✓ Exported to CSV: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse legislator data from nmlegis.gov dropdown HTML'
    )
    parser.add_argument('html_file', help='HTML file containing dropdown options')
    parser.add_argument('--output', default='legislators_official',
                        help='Output file prefix (default: legislators_official)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                        help='Output format (default: both)')

    args = parser.parse_args()

    print("=" * 70)
    print("NM Legislator Dropdown Parser")
    print("=" * 70)

    path = Path(args.html_file)

    if not path.exists():
        print(f"✗ File not found: {args.html_file}")
        print("\nInstructions:")
        print("1. Visit https://www.nmlegis.gov/members/Legislator_List?T=R")
        print("2. Right-click -> Inspect (or press F12)")
        print("3. Find the <select> element with legislator options")
        print("4. Right-click -> Copy -> Copy element")
        print("5. Save to a file (e.g., legislators_dropdown.html)")
        return

    legislators = parse_dropdown_html(path)

    if not legislators:
        print("\n✗ No legislators extracted")
        print("\nMake sure the HTML file contains <option> elements with legislator names")
        return

    print("\n" + "=" * 70)
    print(f"✓ Total legislators extracted: {len(legislators)}")
    print("=" * 70)

    # Export
    if args.format in ['json', 'both']:
        export_to_json(legislators, f'{args.output}.json')

    if args.format in ['csv', 'both']:
        export_to_csv(legislators, f'{args.output}.csv')

    # Statistics
    by_chamber = {}
    for leg in legislators:
        chamber = leg.get('chamber', 'Unknown')
        by_chamber[chamber] = by_chamber.get(chamber, 0) + 1

    print("\nStatistics:")
    print("\nBy Chamber:")
    for chamber, count in sorted(by_chamber.items()):
        print(f"  {chamber:15s}: {count}")

    print("\nSample of extracted legislators:")
    for i, leg in enumerate(legislators[:20], 1):
        print(f"{i:2d}. {leg['legislator_id']:8s} | {leg['chamber']:8s} | {leg['full_name']}")

    if len(legislators) > 20:
        print(f"... and {len(legislators) - 20} more")


if __name__ == '__main__':
    main()
