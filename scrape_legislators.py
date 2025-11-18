#!/usr/bin/env python3
"""
Scrape New Mexico Legislator Information

This script fetches current and former legislators from nmlegis.gov
and creates a structured directory for cross-referencing with extracted names.

Usage:
    python scrape_legislators.py [--current] [--former] [--output legislators_official.json]

Requirements:
    pip install requests beautifulsoup4
"""

import requests
from bs4 import BeautifulSoup
import json
import csv
import re
from typing import List, Dict
import argparse
import time


def scrape_current_legislators(verbose=True) -> List[Dict]:
    """
    Scrape current legislators from nmlegis.gov

    URL: https://www.nmlegis.gov/members/Legislator_List?T=R
    """
    url = "https://www.nmlegis.gov/members/Legislator_List?T=R"

    if verbose:
        print(f"\nFetching current legislators from: {url}")

    try:
        # Use headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        if verbose:
            print(f"✓ Successfully fetched page ({len(response.text)} characters)")

        soup = BeautifulSoup(response.content, 'html.parser')

        legislators = []

        # Find the legislator table (inspect the HTML to determine the correct selector)
        # Common patterns: table with class, tbody > tr, etc.

        # Try multiple selectors
        tables = soup.find_all('table')

        if verbose:
            print(f"Found {len(tables)} tables on page")

        for table in tables:
            rows = table.find_all('tr')

            if verbose:
                print(f"  Table has {len(rows)} rows")

            for row in rows:
                cells = row.find_all(['td', 'th'])

                if len(cells) < 3:  # Skip header/empty rows
                    continue

                # Extract data from cells (adjust based on actual HTML structure)
                # Common pattern: Name | Chamber | Party | District | etc.

                legislator = {}

                # Try to extract name (usually first column with a link)
                name_cell = cells[0]
                name_link = name_cell.find('a')
                if name_link:
                    legislator['full_name'] = name_link.get_text(strip=True)
                else:
                    legislator['full_name'] = name_cell.get_text(strip=True)

                # Skip if this looks like a header row
                if legislator['full_name'].lower() in ['name', 'legislator', 'member']:
                    continue

                # Extract other fields (adjust indices based on actual table structure)
                if len(cells) > 1:
                    legislator['chamber'] = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    legislator['party'] = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    legislator['district'] = cells[3].get_text(strip=True) if len(cells) > 3 else ''

                # Parse name into first/last
                name_parts = legislator['full_name'].split()
                if name_parts:
                    legislator['last_name'] = name_parts[-1]
                    legislator['first_name'] = ' '.join(name_parts[:-1])

                legislator['status'] = 'current'
                legislator['source'] = url

                if legislator.get('full_name'):
                    legislators.append(legislator)

        if verbose:
            print(f"✓ Extracted {len(legislators)} current legislators")

        return legislators

    except requests.RequestException as e:
        print(f"✗ Error fetching current legislators: {e}")
        return []


def scrape_former_legislators(verbose=True) -> List[Dict]:
    """
    Scrape former legislators from nmlegis.gov

    URL: https://www.nmlegis.gov/Members/Former_Legislator_List
    """
    url = "https://www.nmlegis.gov/Members/Former_Legislator_List"

    if verbose:
        print(f"\nFetching former legislators from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        if verbose:
            print(f"✓ Successfully fetched page ({len(response.text)} characters)")

        soup = BeautifulSoup(response.content, 'html.parser')

        legislators = []

        tables = soup.find_all('table')

        if verbose:
            print(f"Found {len(tables)} tables on page")

        for table in tables:
            rows = table.find_all('tr')

            if verbose:
                print(f"  Table has {len(rows)} rows")

            for row in rows:
                cells = row.find_all(['td', 'th'])

                if len(cells) < 2:
                    continue

                legislator = {}

                name_cell = cells[0]
                name_link = name_cell.find('a')
                if name_link:
                    legislator['full_name'] = name_link.get_text(strip=True)
                else:
                    legislator['full_name'] = name_cell.get_text(strip=True)

                if legislator['full_name'].lower() in ['name', 'legislator', 'member']:
                    continue

                if len(cells) > 1:
                    legislator['chamber'] = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    legislator['party'] = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                    legislator['district'] = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                    legislator['years_served'] = cells[4].get_text(strip=True) if len(cells) > 4 else ''

                name_parts = legislator['full_name'].split()
                if name_parts:
                    legislator['last_name'] = name_parts[-1]
                    legislator['first_name'] = ' '.join(name_parts[:-1])

                legislator['status'] = 'former'
                legislator['source'] = url

                if legislator.get('full_name'):
                    legislators.append(legislator)

        if verbose:
            print(f"✓ Extracted {len(legislators)} former legislators")

        return legislators

    except requests.RequestException as e:
        print(f"✗ Error fetching former legislators: {e}")
        return []


def export_to_json(legislators: List[Dict], output_file: str):
    """Export legislators to JSON"""

    output = {
        'metadata': {
            'source': 'New Mexico Legislature website (nmlegis.gov)',
            'total_legislators': len(legislators),
            'current': sum(1 for l in legislators if l.get('status') == 'current'),
            'former': sum(1 for l in legislators if l.get('status') == 'former'),
            'extraction_date': time.strftime('%Y-%m-%d'),
        },
        'legislators': legislators
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Exported to JSON: {output_file}")


def export_to_csv(legislators: List[Dict], output_file: str):
    """Export legislators to CSV"""

    if not legislators:
        print("No legislators to export")
        return

    fieldnames = [
        'full_name', 'last_name', 'first_name', 'chamber', 'party',
        'district', 'years_served', 'status', 'source'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(legislators)

    print(f"✓ Exported to CSV: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape New Mexico legislator information from nmlegis.gov'
    )
    parser.add_argument('--current', action='store_true',
                        help='Scrape current legislators')
    parser.add_argument('--former', action='store_true',
                        help='Scrape former legislators')
    parser.add_argument('--output', default='legislators_official',
                        help='Output file prefix (default: legislators_official)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                        help='Output format (default: both)')

    args = parser.parse_args()

    # Default to both if neither specified
    if not args.current and not args.former:
        args.current = True
        args.former = True

    print("=" * 70)
    print("New Mexico Legislator Scraper")
    print("=" * 70)

    all_legislators = []

    if args.current:
        current = scrape_current_legislators(verbose=True)
        all_legislators.extend(current)

    if args.former:
        former = scrape_former_legislators(verbose=True)
        all_legislators.extend(former)

    if not all_legislators:
        print("\n✗ No legislators extracted. Check the HTML structure and update selectors.")
        print("\nTIP: Visit the pages in a browser and inspect the HTML to see the table structure.")
        return

    print("\n" + "=" * 70)
    print(f"✓ Total legislators extracted: {len(all_legislators)}")
    print("=" * 70)

    # Export
    if args.format in ['json', 'both']:
        export_to_json(all_legislators, f'{args.output}.json')

    if args.format in ['csv', 'both']:
        export_to_csv(all_legislators, f'{args.output}.csv')

    # Print sample
    print("\nSample of extracted legislators:")
    for i, leg in enumerate(all_legislators[:10], 1):
        print(f"{i:2d}. {leg['full_name']:30s} | {leg.get('chamber', 'N/A'):8s} | {leg.get('party', 'N/A'):12s} | District {leg.get('district', 'N/A')}")

    if len(all_legislators) > 10:
        print(f"... and {len(all_legislators) - 10} more")


if __name__ == '__main__':
    main()
