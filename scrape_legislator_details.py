#!/usr/bin/env python3
"""
Scrape Detailed Legislator Information from Profile Pages

This script takes the output from parse_legislators_cards.py and follows
each legislator's profile URL to extract additional details like:
- District map link
- Committees
- Contact information (email, phone, capitol room)
- County representation
- Full biographical information

Usage:
    # First, get the basic legislator list
    python parse_legislators_cards.py legislators_current.html -o legislators_basic

    # Then enhance with detailed info
    python scrape_legislator_details.py legislators_basic.json -o legislators_complete

    # Or scrape directly from saved HTML files
    python scrape_legislator_details.py --from-html profile_pages/*.html -o legislators_complete

Requirements:
    pip install beautifulsoup4 requests
"""

import argparse
import json
import csv
import re
import time
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import urljoin

# Try importing requests (for live scraping)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def parse_detail_page_html(html_content: str, base_url: str = "https://www.nmlegis.gov/members/") -> Dict:
    """Parse a legislator detail page and extract additional information"""

    soup = BeautifulSoup(html_content, 'html.parser')

    details = {}

    # Find all list-group-item elements (they contain structured data)
    list_items = soup.find_all('li', class_='list-group-item')

    for item in list_items:
        text = item.get_text(strip=True)

        # District (with map link)
        if 'District:' in text:
            district_link = item.find('a')
            if district_link:
                details['district'] = district_link.get_text(strip=True)
                district_map_href = district_link.get('href', '')
                if district_map_href:
                    details['district_map_url'] = urljoin(base_url, district_map_href)

        # County/Counties
        elif 'County:' in text or 'Counties:' in text:
            # Remove the label and get the value
            county_text = re.sub(r'Count(y|ies):\s*', '', text)
            details['counties'] = county_text

        # Party
        elif 'Party:' in text:
            party_text = re.sub(r'Party:\s*', '', text)
            details['party'] = party_text

        # Phone
        elif 'Phone:' in text:
            phone_text = re.sub(r'Phone:\s*', '', text)
            details['phone'] = phone_text

        # Email
        elif 'Email:' in text:
            email_link = item.find('a')
            if email_link:
                email = email_link.get('href', '').replace('mailto:', '')
                details['email'] = email

        # Capitol Room
        elif 'Room:' in text or 'Capitol Room:' in text:
            room_text = re.sub(r'(Capitol\s+)?Room:\s*', '', text)
            details['capitol_room'] = room_text

        # Leadership position
        elif 'Position:' in text or 'Leadership:' in text:
            position_text = re.sub(r'(Position|Leadership):\s*', '', text)
            details['leadership_position'] = position_text

    # Find committees
    committees = []

    # Look for committee sections (usually in a panel or specific div)
    committee_headers = soup.find_all(text=re.compile(r'Committee', re.IGNORECASE))

    for header in committee_headers:
        parent = header.find_parent(['div', 'h3', 'h4', 'b', 'strong'])
        if parent:
            # Look for lists after the header
            next_elem = parent.find_next_sibling()
            if next_elem and next_elem.name in ['ul', 'ol']:
                committee_items = next_elem.find_all('li')
                for item in committee_items:
                    committee_name = item.get_text(strip=True)
                    if committee_name and committee_name not in committees:
                        committees.append(committee_name)

    if committees:
        details['committees'] = committees

    # Look for biography/about section
    bio_keywords = ['Biography', 'About', 'Background']
    for keyword in bio_keywords:
        bio_section = soup.find(text=re.compile(keyword, re.IGNORECASE))
        if bio_section:
            parent = bio_section.find_parent(['div', 'section'])
            if parent:
                bio_text = parent.get_text(strip=True)
                # Remove the header
                bio_text = re.sub(rf'{keyword}:?\s*', '', bio_text, flags=re.IGNORECASE)
                if len(bio_text) > 50:  # Only include if substantial
                    details['biography'] = bio_text
                    break

    return details


def scrape_detail_page_live(profile_url: str, verbose: bool = True) -> Optional[Dict]:
    """Fetch and parse a legislator's detail page from the web"""

    if not HAS_REQUESTS:
        print("✗ 'requests' library not installed. Cannot fetch live pages.")
        print("  Install with: pip install requests")
        return None

    if verbose:
        print(f"  Fetching: {profile_url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        response = requests.get(profile_url, headers=headers, timeout=30)
        response.raise_for_status()

        details = parse_detail_page_html(response.text, profile_url)

        # Add small delay to be respectful
        time.sleep(0.5)

        return details

    except requests.RequestException as e:
        print(f"  ✗ Error fetching {profile_url}: {e}")
        return None


def enhance_legislators_from_json(input_file: Path, verbose: bool = True, use_web: bool = False) -> List[Dict]:
    """
    Take a legislators JSON file and enhance it with detail page information
    """

    print(f"\nLoading legislators from: {input_file}")

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    legislators = data.get('legislators', [])

    print(f"Found {len(legislators)} legislators")

    enhanced = []

    for i, legislator in enumerate(legislators, 1):
        print(f"\n[{i}/{len(legislators)}] {legislator.get('full_name', 'Unknown')}")

        # Start with existing data
        enhanced_leg = legislator.copy()

        profile_url = legislator.get('profile_url')

        if not profile_url:
            print("  ⚠ No profile URL - skipping detail scraping")
            enhanced.append(enhanced_leg)
            continue

        if use_web:
            # Fetch live from web
            details = scrape_detail_page_live(profile_url, verbose=verbose)
        else:
            print("  ⚠ Live web scraping disabled. Use --web flag to enable.")
            enhanced.append(enhanced_leg)
            continue

        if details:
            # Merge details into legislator data
            for key, value in details.items():
                # Don't overwrite existing data unless the new data is more complete
                if key not in enhanced_leg or not enhanced_leg.get(key):
                    enhanced_leg[key] = value
                elif key == 'committees' and isinstance(value, list):
                    # Merge committee lists
                    existing = enhanced_leg.get('committees', [])
                    if isinstance(existing, list):
                        merged = list(set(existing + value))
                        enhanced_leg['committees'] = merged

            print(f"  ✓ Enhanced with {len(details)} additional fields")

        enhanced.append(enhanced_leg)

    return enhanced


def enhance_legislators_from_html_files(html_files: List[Path], verbose: bool = True) -> List[Dict]:
    """
    Parse legislator detail pages from saved HTML files

    Expected filename format: HABMI.html (legislator ID as filename)
    Or: profile_HABMI.html, legislator_HABMI.html, etc.
    """

    print(f"\nParsing {len(html_files)} HTML files")

    legislators = []

    for i, html_file in enumerate(html_files, 1):
        print(f"\n[{i}/{len(html_files)}] {html_file.name}")

        # Try to extract legislator ID from filename
        leg_id_match = re.search(r'([A-Z]{3,})', html_file.stem)
        leg_id = leg_id_match.group(1) if leg_id_match else None

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        details = parse_detail_page_html(html_content)

        if details:
            legislator = {
                'legislator_id': leg_id,
                'source_file': str(html_file)
            }
            legislator.update(details)

            legislators.append(legislator)
            print(f"  ✓ Extracted {len(details)} fields")
        else:
            print(f"  ⚠ No data extracted")

    return legislators


def export_to_json(legislators: List[Dict], output_file: str):
    """Export enhanced legislators to JSON"""

    output = {
        'metadata': {
            'source': 'Enhanced legislator data with detail page scraping',
            'total_legislators': len(legislators),
            'enhancement_date': time.strftime('%Y-%m-%d'),
        },
        'legislators': legislators
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Exported to JSON: {output_file}")


def export_to_csv(legislators: List[Dict], output_file: str):
    """Export enhanced legislators to CSV"""

    if not legislators:
        print("No legislators to export")
        return

    # Get all unique fieldnames
    all_fields = set()
    for leg in legislators:
        all_fields.update(leg.keys())

    # Define preferred order
    preferred_order = [
        'full_name', 'last_name', 'first_name', 'legislator_id',
        'chamber', 'party', 'district', 'counties',
        'email', 'phone', 'capitol_room',
        'leadership_position', 'committees',
        'district_map_url', 'profile_url', 'photo_url',
        'biography', 'status', 'source', 'source_file'
    ]

    # Build fieldnames list
    fieldnames = [f for f in preferred_order if f in all_fields]
    # Add any remaining fields
    for field in sorted(all_fields):
        if field not in fieldnames:
            fieldnames.append(field)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        for leg in legislators:
            # Flatten lists for CSV
            row = leg.copy()
            if 'committees' in row and isinstance(row['committees'], list):
                row['committees'] = '; '.join(row['committees'])
            writer.writerow(row)

    print(f"✓ Exported to CSV: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Enhance legislator data with details from profile pages'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('input_json', nargs='?', help='JSON file from parse_legislators_cards.py')
    group.add_argument('--from-html', nargs='+', help='Parse from saved HTML detail pages')

    parser.add_argument('--output', '-o', default='legislators_enhanced',
                        help='Output file prefix (default: legislators_enhanced)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                        help='Output format (default: both)')
    parser.add_argument('--web', action='store_true',
                        help='Fetch detail pages from web (requires requests library)')
    parser.add_argument('--verbose', '-v', action='store_true', default=True,
                        help='Verbose output (default: True)')

    args = parser.parse_args()

    print("=" * 70)
    print("Legislator Detail Page Scraper")
    print("=" * 70)

    if args.from_html:
        # Parse from saved HTML files
        html_files = [Path(f) for f in args.from_html]
        html_files = [f for f in html_files if f.exists()]

        if not html_files:
            print("✗ No valid HTML files found")
            return

        legislators = enhance_legislators_from_html_files(html_files, verbose=args.verbose)

    else:
        # Enhance existing JSON
        input_path = Path(args.input_json)

        if not input_path.exists():
            print(f"✗ File not found: {args.input_json}")
            return

        legislators = enhance_legislators_from_json(input_path, verbose=args.verbose, use_web=args.web)

    if not legislators:
        print("\n✗ No legislators to export")
        return

    print("\n" + "=" * 70)
    print(f"✓ Total legislators: {len(legislators)}")
    print("=" * 70)

    # Export
    if args.format in ['json', 'both']:
        export_to_json(legislators, f'{args.output}.json')

    if args.format in ['csv', 'both']:
        export_to_csv(legislators, f'{args.output}.csv')

    # Show sample
    print("\nSample of enhanced data:")
    for i, leg in enumerate(legislators[:5], 1):
        name = leg.get('full_name', 'N/A')
        district = leg.get('district', 'N/A')
        party = leg.get('party', 'N/A')
        email = leg.get('email', 'N/A')
        committees = leg.get('committees', [])
        num_committees = len(committees) if isinstance(committees, list) else 0

        print(f"{i}. {name}")
        print(f"   District {district} | {party}")
        print(f"   Email: {email}")
        print(f"   Committees: {num_committees}")


if __name__ == '__main__':
    main()
