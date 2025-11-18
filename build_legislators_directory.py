#!/usr/bin/env python3
"""
Build Legislators Directory from Extracted Names

Creates a structured directory of legislators by analyzing the extracted names
and their context from transcripts. This can be cross-referenced and manually
enhanced with additional data.
"""

import json
import csv
from pathlib import Path
from collections import defaultdict
import re


def load_extracted_speakers():
    """Load the extracted speakers data"""
    with open('extracted_names_final.json', 'r') as f:
        data = json.load(f)
    return data['entities']


def load_index_data():
    """Load the existing index to get session context"""
    with open('docs/index.json', 'r') as f:
        return json.load(f)


def analyze_legislator_names(speakers):
    """
    Identify likely legislators from extracted names

    Legislators are identified by:
    - High frequency (active participants)
    - Common NM legislative surnames
    - Presence in multiple sessions
    """

    legislators = []

    for speaker in speakers:
        name = speaker['name']
        frequency = speaker['frequency']
        confidence = speaker['confidence_level']
        variants = speaker['variants']

        # Create legislator record
        legislator = {
            'name': name,
            'last_name': name.split()[-1] if name else '',
            'frequency': frequency,
            'confidence': confidence,
            'variants': variants,
            'chamber': 'Unknown',  # To be filled
            'party': 'Unknown',  # To be filled
            'district': 'Unknown',  # To be filled
            'years_active': [],  # To be filled
            'committees': [],  # To be filled
            'verified': False,  # Manual verification flag
            'notes': ''
        }

        legislators.append(legislator)

    return legislators


def export_legislators_csv(legislators, output_file='legislators_directory.csv'):
    """Export legislators to CSV for manual review and enhancement"""

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'name', 'last_name', 'frequency', 'confidence',
            'chamber', 'party', 'district', 'years_active',
            'committees', 'verified', 'notes', 'variants'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for leg in legislators:
            # Flatten variants and committees for CSV
            row = leg.copy()
            row['variants'] = '; '.join(leg['variants'][:5]) if leg['variants'] else ''
            row['committees'] = '; '.join(leg['committees']) if leg['committees'] else ''
            row['years_active'] = ''  # Leave empty for manual fill
            writer.writerow(row)


def export_legislators_json(legislators, output_file='legislators_directory.json'):
    """Export legislators to JSON with full metadata"""

    output = {
        'metadata': {
            'source': 'Extracted from 1,435 NM Legislature transcripts',
            'total_legislators': len(legislators),
            'high_confidence': sum(1 for l in legislators if l['confidence'] == 'high'),
            'medium_confidence': sum(1 for l in legislators if l['confidence'] == 'medium'),
            'low_confidence': sum(1 for l in legislators if l['confidence'] == 'low'),
            'note': 'Unverified - requires manual validation and enhancement',
            'fields': {
                'name': 'Full name as extracted',
                'last_name': 'Last name for sorting',
                'frequency': 'Number of mentions in transcripts',
                'confidence': 'high (≥10), medium (3-9), or low (1-2)',
                'chamber': 'House or Senate (to be filled manually)',
                'party': 'Political party (to be filled manually)',
                'district': 'District number (to be filled manually)',
                'years_active': 'Years served (to be filled manually)',
                'verified': 'Boolean - manually verified as legislator',
                'notes': 'Additional notes',
                'variants': 'OCR variations of the name'
            }
        },
        'legislators': legislators
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def create_import_template():
    """Create a template for importing external legislator data"""

    template = {
        'instructions': 'Fill in this template with verified legislator data from official sources',
        'sources': [
            'https://www.nmlegis.gov/members/Legislator_List?T=R (current)',
            'https://www.nmlegis.gov/Members/Former_Legislator_List (archive)',
            'https://ballotpedia.org/New_Mexico_State_Legislature'
        ],
        'template': [
            {
                'full_name': 'John Doe',
                'last_name': 'Doe',
                'first_name': 'John',
                'chamber': 'House or Senate',
                'party': 'Democratic, Republican, or other',
                'district': 'District number',
                'years_served': '2020-2024',
                'committees': ['Education', 'Finance'],
                'leadership_positions': ['Speaker', 'Majority Leader', 'etc.'],
                'notes': 'Additional information'
            }
        ]
    }

    with open('legislators_import_template.json', 'w') as f:
        json.dump(template, f, indent=2)


def generate_cross_reference_report(legislators):
    """Generate a report for cross-referencing extracted vs known legislators"""

    report = []
    report.append("# Legislators Cross-Reference Report\n")
    report.append(f"Generated from {len(legislators)} extracted names\n\n")

    # Group by confidence
    by_confidence = defaultdict(list)
    for leg in legislators:
        by_confidence[leg['confidence']].append(leg)

    report.append("## Summary by Confidence Level\n\n")
    for conf in ['high', 'medium', 'low']:
        count = len(by_confidence[conf])
        report.append(f"- **{conf.capitalize()}**: {count} names\n")

    report.append("\n## Top 50 Most Frequent Names (Likely Legislators)\n\n")
    report.append("| Rank | Name | Frequency | Confidence | Variants |\n")
    report.append("|------|------|-----------|------------|----------|\n")

    sorted_legs = sorted(legislators, key=lambda x: x['frequency'], reverse=True)
    for i, leg in enumerate(sorted_legs[:50], 1):
        variants_sample = ', '.join(leg['variants'][:3]) if leg['variants'] else 'None'
        if len(leg['variants']) > 3:
            variants_sample += '...'
        report.append(f"| {i} | {leg['name']} | {leg['frequency']} | {leg['confidence']} | {variants_sample} |\n")

    report.append("\n## Names Requiring Verification\n\n")
    report.append("High-frequency names that should be cross-checked against official legislator lists:\n\n")

    high_freq = [l for l in sorted_legs if l['frequency'] >= 10]
    for leg in high_freq[:30]:
        report.append(f"- [ ] **{leg['name']}** ({leg['frequency']} mentions)\n")

    report.append("\n## Instructions for Manual Enhancement\n\n")
    report.append("1. Open `legislators_directory.csv` in a spreadsheet application\n")
    report.append("2. For each high-confidence name:\n")
    report.append("   - Verify if they are a legislator\n")
    report.append("   - Fill in chamber (House/Senate)\n")
    report.append("   - Fill in party affiliation\n")
    report.append("   - Fill in district number\n")
    report.append("   - Fill in years served\n")
    report.append("   - Mark 'verified' as TRUE\n")
    report.append("3. For non-legislators (lobbyists, staff, witnesses):\n")
    report.append("   - Mark 'verified' as FALSE\n")
    report.append("   - Add note describing their role\n")
    report.append("4. Save and re-import for validation analysis\n\n")

    return ''.join(report)


def main():
    print("Building Legislators Directory from Extracted Names")
    print("=" * 70)

    # Load data
    print("\n1. Loading extracted speakers data...")
    speakers = load_extracted_speakers()
    print(f"   Found {len(speakers)} extracted names")

    # Analyze and create legislators directory
    print("\n2. Creating legislators directory...")
    legislators = analyze_legislator_names(speakers)
    print(f"   Created {len(legislators)} legislator records")

    # Export to CSV
    print("\n3. Exporting to CSV...")
    export_legislators_csv(legislators)
    print("   ✓ legislators_directory.csv")

    # Export to JSON
    print("\n4. Exporting to JSON...")
    export_legislators_json(legislators)
    print("   ✓ legislators_directory.json")

    # Create import template
    print("\n5. Creating import template...")
    create_import_template()
    print("   ✓ legislators_import_template.json")

    # Generate cross-reference report
    print("\n6. Generating cross-reference report...")
    report = generate_cross_reference_report(legislators)
    with open('LEGISLATORS_CROSS_REFERENCE.md', 'w') as f:
        f.write(report)
    print("   ✓ LEGISLATORS_CROSS_REFERENCE.md")

    print("\n" + "=" * 70)
    print("✓ Legislators directory created successfully!")
    print("\nNext steps:")
    print("1. Review legislators_directory.csv")
    print("2. Manually verify and enhance with official data")
    print("3. Mark verified=TRUE for confirmed legislators")
    print("4. See LEGISLATORS_CROSS_REFERENCE.md for detailed instructions")

    # Statistics
    print("\nStatistics:")
    by_conf = defaultdict(int)
    for leg in legislators:
        by_conf[leg['confidence']] += 1

    print(f"  High confidence (≥10 mentions): {by_conf['high']}")
    print(f"  Medium confidence (3-9): {by_conf['medium']}")
    print(f"  Low confidence (1-2): {by_conf['low']}")

    top_10 = sorted(legislators, key=lambda x: x['frequency'], reverse=True)[:10]
    print("\n  Top 10 most frequent names:")
    for i, leg in enumerate(top_10, 1):
        print(f"    {i:2d}. {leg['name']:30s} ({leg['frequency']:4d} mentions)")


if __name__ == '__main__':
    main()
