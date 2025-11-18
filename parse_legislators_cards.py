#!/usr/bin/env python3
"""
Parse Legislator Data from nmlegis.gov Card/Thumbnail Layout

The legislator list page displays cards with this structure:
<a class="thumbnail" href="Legislator?SponCode=HABMI">
    <img src="../Images/Legislators/House/HABMI.jpg" alt="Abeyta">
    <div class="caption">
        <span>Michelle Paulene Abeyta - (D)</span>
        <span>District: 69</span>
    </div>
</a>

Instructions:
1. Visit https://www.nmlegis.gov/members/Legislator_List?T=R
2. Right-click -> "Inspect" or press F12
3. Right-click on the page -> "Save Page As" -> legislators_current.html
4. Run: python parse_legislators_cards.py legislators_current.html

Usage:
    python parse_legislators_cards.py <html_file> [--output legislators_official]
"""

import argparse
import json
import csv
import re
from pathlib import Path
from bs4 import BeautifulSoup
import time
from typing import List, Dict


def parse_legislator_cards(html_file: Path, status='current') -> List[Dict]:
    """Parse legislators from card/thumbnail layout"""

    print(f"\nParsing: {html_file}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    legislators = []

    # Find all legislator cards/thumbnails
    # Look for <a> tags with class "thumbnail" that link to Legislator?SponCode=
    cards = soup.find_all('a', class_='thumbnail', href=re.compile(r'Legislator\?SponCode='))

    print(f"Found {len(cards)} legislator cards")

    for card in cards:
        legislator = {'status': status}

        # Extract legislator ID from href
        href = card.get('href', '')
        sponcode_match = re.search(r'SponCode=([A-Z]+)', href)
        if sponcode_match:
            legislator['legislator_id'] = sponcode_match.group(1)
            legislator['profile_url'] = f"https://www.nmlegis.gov/members/{href}"

        # Extract chamber from image path
        img = card.find('img')
        if img:
            img_src = img.get('src', '')
            if '/House/' in img_src:
                legislator['chamber'] = 'House'
            elif '/Senate/' in img_src:
                legislator['chamber'] = 'Senate'
            legislator['photo_url'] = f"https://www.nmlegis.gov/members/{img_src.lstrip('../')}"

        # Extract name and party from caption
        caption = card.find('div', class_='caption')
        if caption:
            spans = caption.find_all('span')

            # First span: Name - (Party)
            if len(spans) > 0:
                name_party_text = spans[0].get_text(strip=True)

                # Parse: "Michelle Paulene Abeyta - (D)"
                name_party_match = re.match(r'(.+?)\s*-\s*\(([A-Z])\)', name_party_text)
                if name_party_match:
                    full_name = name_party_match.group(1).strip()
                    party_code = name_party_match.group(2).strip()

                    legislator['full_name'] = full_name

                    # Parse name into first/last
                    name_parts = full_name.split()
                    if name_parts:
                        legislator['last_name'] = name_parts[-1]
                        legislator['first_name'] = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else ''

                    # Map party code to full name
                    party_map = {
                        'D': 'Democratic',
                        'R': 'Republican',
                        'I': 'Independent',
                        'L': 'Libertarian',
                        'G': 'Green'
                    }
                    legislator['party'] = party_map.get(party_code, party_code)

            # Second span: District
            if len(spans) > 1:
                district_text = spans[1].get_text(strip=True)

                # Parse: "District: 69"
                district_match = re.search(r'District:\s*(\d+)', district_text)
                if district_match:
                    legislator['district'] = district_match.group(1)

        # Only add if we have at least a name
        if legislator.get('full_name'):
            legislator['source'] = 'nmlegis.gov/members/Legislator_List'
            legislators.append(legislator)

    print(f"✓ Extracted {len(legislators)} legislators")
    return legislators


def export_to_json(legislators: List[Dict], output_file: str):
    """Export legislators to JSON"""

    output = {
        'metadata': {
            'source': 'nmlegis.gov legislator card parser',
            'total_legislators': len(legislators),
            'house': sum(1 for l in legislators if l.get('chamber') == 'House'),
            'senate': sum(1 for l in legislators if l.get('chamber') == 'Senate'),
            'democratic': sum(1 for l in legislators if l.get('party') == 'Democratic'),
            'republican': sum(1 for l in legislators if l.get('party') == 'Republican'),
            'extraction_date': time.strftime('%Y-%m-%d'),
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
        'chamber', 'party', 'district', 'status',
        'profile_url', 'photo_url', 'source'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(legislators)

    print(f"✓ Exported to CSV: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse legislator data from nmlegis.gov card/thumbnail layout'
    )
    parser.add_argument('html_file', help='HTML file saved from legislator list page')
    parser.add_argument('--output', default='legislators_official',
                        help='Output file prefix (default: legislators_official)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                        help='Output format (default: both)')
    parser.add_argument('--status', default='current',
                        help='Legislator status: current or former (default: current)')

    args = parser.parse_args()

    print("=" * 70)
    print("NM Legislator Card Parser")
    print("=" * 70)

    path = Path(args.html_file)

    if not path.exists():
        print(f"✗ File not found: {args.html_file}")
        print("\nInstructions:")
        print("1. Visit https://www.nmlegis.gov/members/Legislator_List?T=R")
        print("2. Right-click -> 'Save Page As' -> save as legislators_current.html")
        print("3. Run: python parse_legislators_cards.py legislators_current.html")
        return

    legislators = parse_legislator_cards(path, status=args.status)

    if not legislators:
        print("\n✗ No legislators extracted")
        print("\nMake sure the HTML file contains legislator card elements")
        print("Look for <a class=\"thumbnail\"> elements with legislator data")
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
    by_party = {}
    for leg in legislators:
        chamber = leg.get('chamber', 'Unknown')
        party = leg.get('party', 'Unknown')
        by_chamber[chamber] = by_chamber.get(chamber, 0) + 1
        by_party[party] = by_party.get(party, 0) + 1

    print("\nStatistics:")
    print("\nBy Chamber:")
    for chamber, count in sorted(by_chamber.items()):
        print(f"  {chamber:15s}: {count}")

    print("\nBy Party:")
    for party, count in sorted(by_party.items()):
        print(f"  {party:15s}: {count}")

    print("\nSample of extracted legislators:")
    for i, leg in enumerate(legislators[:15], 1):
        chamber = leg.get('chamber', 'N/A')
        party = leg.get('party', 'N/A')
        district = leg.get('district', 'N/A')
        leg_id = leg.get('legislator_id', 'N/A')
        print(f"{i:2d}. {leg_id:8s} | {chamber:8s} | {party:12s} | Dist. {district:3s} | {leg['full_name']}")

    if len(legislators) > 15:
        print(f"... and {len(legislators) - 15} more")


if __name__ == '__main__':
    main()
