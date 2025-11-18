#!/usr/bin/env python3
"""
Parse Legislator Data from Saved HTML

If the scraper script fails due to access restrictions, you can:
1. Visit https://www.nmlegis.gov/members/Legislator_List?T=R in your browser
2. Right-click -> "Save Page As" -> legislators_current.html
3. Run this script to parse the saved HTML

Usage:
    python parse_legislators_html.py legislators_current.html [--output legislators_official]
"""

import argparse
import json
import csv
from pathlib import Path
from bs4 import BeautifulSoup
import time
from typing import List, Dict


def parse_html_file(html_file: Path, status='current') -> List[Dict]:
    """Parse legislators from a saved HTML file"""

    print(f"\nParsing: {html_file}")

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    legislators = []

    # Find all tables
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables in HTML")

    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        print(f"\nTable {table_idx + 1}: {len(rows)} rows")

        headers = []
        header_row = table.find('tr')
        if header_row:
            header_cells = header_row.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True).lower() for cell in header_cells]
            print(f"  Headers: {headers}")

        for row_idx, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])

            if len(cells) < 2:
                continue

            cell_values = [cell.get_text(strip=True) for cell in cells]

            # Skip header rows
            if cell_values[0].lower() in ['name', 'legislator', 'member', 'full name']:
                continue

            # Skip empty rows
            if not any(cell_values):
                continue

            legislator = {
                'status': status,
                'source': str(html_file)
            }

            # Try to intelligently map columns
            # Common patterns from nmlegis.gov:
            # - Name | Chamber | Party | County | District | Email | Phone

            # Column 0: Name (usually has a link)
            name_cell = cells[0]
            name_link = name_cell.find('a')
            if name_link:
                legislator['full_name'] = name_link.get_text(strip=True)
                # Extract profile URL if available
                href = name_link.get('href')
                if href:
                    legislator['profile_url'] = href
            else:
                legislator['full_name'] = cell_values[0]

            if not legislator['full_name'] or len(legislator['full_name']) < 3:
                continue

            # Parse name into first/last
            name_parts = legislator['full_name'].split()
            if name_parts:
                legislator['last_name'] = name_parts[-1]
                legislator['first_name'] = ' '.join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]

            # Column 1: Chamber (House/Senate)
            if len(cell_values) > 1:
                chamber = cell_values[1]
                if 'house' in chamber.lower() or chamber.upper() == 'H':
                    legislator['chamber'] = 'House'
                elif 'senate' in chamber.lower() or chamber.upper() == 'S':
                    legislator['chamber'] = 'Senate'
                else:
                    legislator['chamber'] = chamber

            # Column 2: Party (D/R/I etc.)
            if len(cell_values) > 2:
                party = cell_values[2]
                if party.upper() == 'D' or 'democrat' in party.lower():
                    legislator['party'] = 'Democratic'
                elif party.upper() == 'R' or 'republican' in party.lower():
                    legislator['party'] = 'Republican'
                elif party.upper() == 'I' or 'independent' in party.lower():
                    legislator['party'] = 'Independent'
                else:
                    legislator['party'] = party

            # Column 3: County or District
            if len(cell_values) > 3:
                legislator['county'] = cell_values[3]

            # Column 4: District
            if len(cell_values) > 4:
                district = cell_values[4]
                legislator['district'] = district

            # Column 5: Email
            if len(cells) > 5:
                email_cell = cells[5]
                email_link = email_cell.find('a')
                if email_link:
                    email = email_link.get('href', '').replace('mailto:', '')
                    legislator['email'] = email
                else:
                    legislator['email'] = cell_values[5]

            # Column 6: Phone
            if len(cell_values) > 6:
                legislator['phone'] = cell_values[6]

            legislators.append(legislator)

            # Debug: print first few rows
            if row_idx < 5:
                print(f"  Row {row_idx}: {legislator.get('full_name', 'N/A'):30s} | {legislator.get('chamber', 'N/A'):8s} | {legislator.get('party', 'N/A')}")

    print(f"\n✓ Extracted {len(legislators)} legislators from {html_file}")
    return legislators


def export_to_json(legislators: List[Dict], output_file: str):
    """Export legislators to JSON"""

    output = {
        'metadata': {
            'source': 'Parsed from locally saved HTML files',
            'total_legislators': len(legislators),
            'current': sum(1 for l in legislators if l.get('status') == 'current'),
            'former': sum(1 for l in legislators if l.get('status') == 'former'),
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

    # Get all unique fieldnames
    all_fields = set()
    for leg in legislators:
        all_fields.update(leg.keys())

    fieldnames = [
        'full_name', 'last_name', 'first_name', 'chamber', 'party',
        'district', 'county', 'email', 'phone', 'status', 'profile_url', 'source'
    ]

    # Add any extra fields
    for field in all_fields:
        if field not in fieldnames:
            fieldnames.append(field)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(legislators)

    print(f"✓ Exported to CSV: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse legislator data from locally saved HTML files'
    )
    parser.add_argument('html_files', nargs='+', help='HTML files to parse')
    parser.add_argument('--output', default='legislators_official',
                        help='Output file prefix (default: legislators_official)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                        help='Output format (default: both)')

    args = parser.parse_args()

    print("=" * 70)
    print("NM Legislator HTML Parser")
    print("=" * 70)

    all_legislators = []

    for html_file in args.html_files:
        path = Path(html_file)

        if not path.exists():
            print(f"✗ File not found: {html_file}")
            continue

        # Determine status from filename
        status = 'current'
        if 'former' in path.name.lower():
            status = 'former'

        legislators = parse_html_file(path, status=status)
        all_legislators.extend(legislators)

    if not all_legislators:
        print("\n✗ No legislators extracted")
        print("\nTroubleshooting:")
        print("1. Make sure the HTML file contains a table with legislator data")
        print("2. Check that the file is saved as UTF-8 encoding")
        print("3. Inspect the HTML structure and adjust the parsing logic if needed")
        return

    print("\n" + "=" * 70)
    print(f"✓ Total legislators extracted: {len(all_legislators)}")
    print("=" * 70)

    # Export
    if args.format in ['json', 'both']:
        export_to_json(all_legislators, f'{args.output}.json')

    if args.format in ['csv', 'both']:
        export_to_csv(all_legislators, f'{args.output}.csv')

    # Statistics
    by_chamber = {}
    by_party = {}
    for leg in all_legislators:
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
    for i, leg in enumerate(all_legislators[:15], 1):
        chamber = leg.get('chamber', 'N/A')
        party = leg.get('party', 'N/A')
        district = leg.get('district', 'N/A')
        print(f"{i:2d}. {leg['full_name']:35s} | {chamber:8s} | {party:12s} | Dist. {district}")

    if len(all_legislators) > 15:
        print(f"... and {len(all_legislators) - 15} more")


if __name__ == '__main__':
    main()
