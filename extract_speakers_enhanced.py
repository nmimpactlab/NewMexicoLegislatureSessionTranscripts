#!/usr/bin/env python3
"""
Enhanced Speaker Extraction

Extends name extraction to capture:
- Public speakers (testimony, public comment)
- Lobbyists and organizational representatives
- Subject matter experts
- Context/affiliation for each speaker

Improvements over basic extraction:
1. Multiple introduction patterns (not just titles)
2. Context detection for speaker roles
3. Affiliation capture (organizations, agencies)
4. Preserves full names for low-frequency speakers
"""

import re
import json
import csv
from pathlib import Path
from collections import Counter, defaultdict
from typing import Set, List, Dict, Tuple, Optional
import argparse
from datetime import datetime


class EnhancedSpeakerExtractor:
    """Extract speakers with context and role detection"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.speakers = {}  # name -> {count, contexts, affiliations, role}

    def extract_from_file(self, file_path: Path, text: str):
        """Extract speakers from a single file"""

        # Track which file each mention came from
        file_name = file_path.stem

        # Extract using multiple patterns
        self._extract_titled_names(text, file_name)
        self._extract_self_introductions(text, file_name)
        self._extract_testimony_speakers(text, file_name)
        self._extract_organizational_reps(text, file_name)

    def _extract_titled_names(self, text: str, file_name: str):
        """Extract names with titles (legislators, officials)"""

        titles = [
            ('Representative', 'legislator'),
            ('Rep', 'legislator'),
            ('Senator', 'legislator'),
            ('Sen', 'legislator'),
            ('Chairman', 'official'),
            ('Chairwoman', 'official'),
            ('Chair', 'official'),
            ('Secretary', 'official'),
            ('Director', 'official'),
            ('Commissioner', 'official'),
            ('Governor', 'official'),
            ('Mr', 'unknown'),
            ('Ms', 'unknown'),
            ('Mrs', 'unknown'),
            ('Dr', 'expert'),
            ('Doctor', 'expert'),
            ('Professor', 'expert'),
        ]

        for title, role in titles:
            # Pattern: Title + Name (1-3 words)
            pattern = rf'\b{re.escape(title)}\.?\s+([A-Z][a-z]+(?:[\s\-\'][A-Z][a-z]+){{0,2}})\b'

            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = self._normalize_name(match.group(1))
                if name and self._is_valid_name(name):
                    self._add_speaker(name, role, None, file_name)

    def _extract_self_introductions(self, text: str, file_name: str):
        """Extract names from self-introductions (public speakers)"""

        # Patterns for self-introduction
        intro_patterns = [
            # "My name is [NAME]"
            (r'[Mm]y name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'public'),
            # "I'm [NAME]" or "I am [NAME]"
            (r"I'?m\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", 'public'),
            (r"I am\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})", 'public'),
            # "This is [NAME]"
            (r'[Tt]his is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'public'),
            # "[NAME] here" (e.g., "John Smith here")
            (r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+here\b', 'public'),
        ]

        for pattern, role in intro_patterns:
            for match in re.finditer(pattern, text):
                name = self._normalize_name(match.group(1))
                if name and self._is_valid_name(name):
                    # Try to extract affiliation from surrounding context
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 100)
                    context = text[context_start:context_end]
                    affiliation = self._extract_affiliation(context)

                    self._add_speaker(name, role, affiliation, file_name)

    def _extract_testimony_speakers(self, text: str, file_name: str):
        """Extract speakers from testimony context"""

        # Patterns indicating testimony
        testimony_patterns = [
            # "Good morning/afternoon, I'm [NAME]"
            (r'[Gg]ood (?:morning|afternoon|evening)[,.]?\s+(?:I\'?m|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'public'),
            # "[NAME] testifying on behalf of"
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+(?:testifying|here to testify|here today)', 'public'),
            # "Thank you for the opportunity... my name is [NAME]"
            (r'[Tt]hank you.*?(?:I\'?m|my name is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})', 'public'),
        ]

        for pattern, role in testimony_patterns:
            for match in re.finditer(pattern, text):
                name = self._normalize_name(match.group(1))
                if name and self._is_valid_name(name):
                    # Extract affiliation
                    context_end = min(len(text), match.end() + 150)
                    context = text[match.start():context_end]
                    affiliation = self._extract_affiliation(context)

                    self._add_speaker(name, role, affiliation, file_name)

    def _extract_organizational_reps(self, text: str, file_name: str):
        """Extract representatives of organizations"""

        # Patterns for organizational representatives
        org_patterns = [
            # "[NAME] from [ORGANIZATION]"
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+from\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)', 'lobbyist'),
            # "[NAME] representing [ORGANIZATION]"
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+representing\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)', 'lobbyist'),
            # "[NAME] with [ORGANIZATION]"
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+with\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)', 'lobbyist'),
            # "[NAME] on behalf of [ORGANIZATION]"
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\s+on behalf of\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)', 'lobbyist'),
        ]

        for pattern, role in org_patterns:
            for match in re.finditer(pattern, text):
                name = self._normalize_name(match.group(1))
                org = match.group(2).strip() if len(match.groups()) > 1 else None

                if name and self._is_valid_name(name):
                    # Clean up organization name
                    if org:
                        org = self._clean_organization(org)

                    self._add_speaker(name, role, org, file_name)

    def _extract_affiliation(self, context: str) -> Optional[str]:
        """Extract organizational affiliation from context"""

        # Patterns to find organization
        org_patterns = [
            r'from\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)',
            r'representing\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)',
            r'with\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)',
            r'on behalf of\s+(?:the\s+)?([A-Z][A-Za-z\s&]+?)(?:\.|,|$)',
        ]

        for pattern in org_patterns:
            match = re.search(pattern, context)
            if match:
                org = match.group(1).strip()
                return self._clean_organization(org)

        return None

    def _clean_organization(self, org: str) -> str:
        """Clean up organization name"""
        # Remove trailing punctuation and common words
        org = re.sub(r'[,.\s]+$', '', org)

        # Skip if it's too short or looks like a common phrase
        if len(org) < 3:
            return None

        blacklist = {'the', 'and', 'or', 'to', 'for', 'in', 'on', 'at', 'by'}
        words = org.split()
        if len(words) == 1 and words[0].lower() in blacklist:
            return None

        return org

    def _normalize_name(self, name: str) -> str:
        """Normalize name to title case"""
        if not name:
            return None

        # Clean whitespace
        name = ' '.join(name.split())

        # Title case
        name = ' '.join(word.title() for word in name.split())

        return name

    def _is_valid_name(self, name: str) -> bool:
        """Check if name is valid"""
        if not name:
            return False

        words = name.split()

        # Length checks
        if len(name) < 2 or len(name) > 50:
            return False

        # Must have vowel
        if not re.search(r'[aeiou]', name, re.IGNORECASE):
            return False

        # Blacklist common words and filler words
        blacklist = {
            # Filler words
            'um', 'uh', 'ah', 'oh', 'er', 'eh',
            # Common words that slip through
            'thank', 'you', 'the', 'and', 'or', 'for', 'this', 'that',
            'good', 'morning', 'afternoon', 'evening', 'hello', 'hi',
            'yes', 'no', 'okay', 'well', 'now', 'here', 'there',
            'so', 'it', 'is', 'of', 'if', 'we', 'be', 'as', 'at', 'by',
            'to', 'in', 'on', 'up', 'do', 'go', 'me', 'my', 'an', 'he', 'she',
            # Procedural
            'committee', 'chair', 'chairman', 'chairwoman', 'members',
            'representative', 'senator', 'governor', 'secretary',
            # Actions
            'know', 'did', 'made', 'take', 'have', 'has', 'had', 'was', 'were',
            'can', 'will', 'would', 'could', 'should', 'may', 'might',
        }

        # Single word names shouldn't be blacklisted
        if len(words) == 1 and name.lower() in blacklist:
            return False

        # Multi-word: check all words against blacklist for common issues
        if len(words) > 1:
            # First or last word shouldn't be blacklisted
            if words[0].lower() in blacklist or words[-1].lower() in blacklist:
                return False

            # Check for patterns that indicate garbage (Name + common verb/word)
            garbage_endings = {
                'you', 'know', 'did', 'for', 'your', 'the', 'and', 'or',
                'we', 'have', 'has', 'had', 'was', 'were', 'are', 'is',
                'so', 'it', 'then', 'next', 'made', 'take', 'will',
                'can', 'could', 'would', 'should', 'may', 'might',
            }
            if words[-1].lower() in garbage_endings:
                return False

            # Patterns like "Garcia Representative Brown" - title in middle
            middle_blacklist = {'representative', 'senator', 'chair', 'chairman'}
            for word in words[1:-1]:
                if word.lower() in middle_blacklist:
                    return False

        return True

    def _add_speaker(self, name: str, role: str, affiliation: Optional[str], file_name: str):
        """Add or update speaker record"""

        if name not in self.speakers:
            self.speakers[name] = {
                'count': 0,
                'roles': Counter(),
                'affiliations': Counter(),
                'files': set(),
            }

        self.speakers[name]['count'] += 1
        self.speakers[name]['roles'][role] += 1
        self.speakers[name]['files'].add(file_name)

        if affiliation:
            self.speakers[name]['affiliations'][affiliation] += 1

    def normalize_speakers(self) -> Dict:
        """
        Normalize and deduplicate speakers

        Key improvement: Only consolidate high-frequency names
        Preserve full names for low-frequency speakers (public testimony)
        """

        # Sort by count descending
        sorted_speakers = sorted(
            self.speakers.items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )

        normalized = {}

        for name, data in sorted_speakers:
            # Check if this name should be merged with an existing one
            merged = False

            # Only merge if BOTH are high frequency (>= 5 mentions)
            # This preserves unique public speakers
            if data['count'] >= 5:
                for canonical in list(normalized.keys()):
                    if normalized[canonical]['count'] >= 5:
                        if self._should_merge(name, canonical):
                            # Merge into canonical
                            normalized[canonical]['count'] += data['count']
                            normalized[canonical]['variants'].append(name)
                            normalized[canonical]['files'].update(data['files'])

                            # Merge roles and affiliations
                            for role, cnt in data['roles'].items():
                                normalized[canonical]['roles'][role] += cnt
                            for aff, cnt in data['affiliations'].items():
                                normalized[canonical]['affiliations'][aff] += cnt

                            merged = True
                            break

            if not merged:
                # Create new entry
                normalized[name] = {
                    'count': data['count'],
                    'variants': [name],
                    'roles': data['roles'].copy(),
                    'affiliations': data['affiliations'].copy(),
                    'files': data['files'].copy(),
                }

        return normalized

    def _should_merge(self, name1: str, name2: str) -> bool:
        """Determine if two names should be merged"""

        # Don't merge if they're the same
        if name1.lower() == name2.lower():
            return False

        # Check if one is substring of other
        # But only for last names, not full names
        words1 = name1.split()
        words2 = name2.split()

        # If one is a single word (last name) and matches the last word of the other
        if len(words1) == 1 and len(words2) > 1:
            if words1[0].lower() == words2[-1].lower():
                return True
        if len(words2) == 1 and len(words1) > 1:
            if words2[0].lower() == words1[-1].lower():
                return True

        return False

    def determine_primary_role(self, roles: Counter) -> str:
        """Determine primary role from role counts"""

        if not roles:
            return 'unknown'

        # Priority order
        role_priority = ['legislator', 'official', 'expert', 'lobbyist', 'public', 'unknown']

        # Get most common role
        most_common = roles.most_common(1)[0][0]

        return most_common

    def get_confidence_level(self, count: int) -> str:
        """Determine confidence level from mention count"""
        if count >= 10:
            return 'high'
        elif count >= 3:
            return 'medium'
        else:
            return 'low'


def find_all_transcripts(base_dir: Path = Path('.')) -> List[Path]:
    """Find all transcript files"""
    transcript_files = []

    for txt_file in base_dir.glob('**/*.cc.txt'):
        if 'maybedupes' not in str(txt_file):
            transcript_files.append(txt_file)

    return sorted(transcript_files)


def export_to_json(normalized: Dict, extractor: EnhancedSpeakerExtractor,
                   output_file: str, metadata: Dict):
    """Export results to JSON"""

    output = {
        'metadata': {
            'extraction_date': metadata.get('extraction_date', datetime.now().isoformat()),
            'total_files_processed': metadata.get('total_files', 0),
            'total_characters_processed': metadata.get('total_chars', 0),
            'extraction_type': 'enhanced_with_context',
            'features': [
                'public_speaker_detection',
                'organizational_affiliation',
                'role_classification',
                'full_name_preservation'
            ]
        },
        'summary_statistics': {
            'total_speakers': len(normalized),
            'by_role': {},
            'by_confidence': {
                'high': 0,
                'medium': 0,
                'low': 0
            }
        },
        'entities': []
    }

    # Count by role
    role_counts = Counter()

    for name, data in sorted(normalized.items(), key=lambda x: x[1]['count'], reverse=True):
        primary_role = extractor.determine_primary_role(data['roles'])
        confidence = extractor.get_confidence_level(data['count'])

        role_counts[primary_role] += 1
        output['summary_statistics']['by_confidence'][confidence] += 1

        # Get top affiliation
        top_affiliation = None
        if data['affiliations']:
            top_affiliation = data['affiliations'].most_common(1)[0][0]

        entity = {
            'name': name,
            'frequency': data['count'],
            'confidence_level': confidence,
            'primary_role': primary_role,
            'affiliation': top_affiliation,
            'all_roles': dict(data['roles']),
            'all_affiliations': dict(data['affiliations']),
            'variants': [v for v in data['variants'] if v != name],
            'file_count': len(data['files'])
        }

        output['entities'].append(entity)

    output['summary_statistics']['by_role'] = dict(role_counts)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def export_to_csv(normalized: Dict, extractor: EnhancedSpeakerExtractor, output_file: str):
    """Export results to CSV"""

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        writer.writerow([
            'Name', 'Frequency', 'Confidence', 'Primary_Role',
            'Affiliation', 'Variants', 'File_Count'
        ])

        for name, data in sorted(normalized.items(), key=lambda x: x[1]['count'], reverse=True):
            primary_role = extractor.determine_primary_role(data['roles'])
            confidence = extractor.get_confidence_level(data['count'])

            top_affiliation = ''
            if data['affiliations']:
                top_affiliation = data['affiliations'].most_common(1)[0][0]

            variants = '; '.join(v for v in data['variants'] if v != name)

            writer.writerow([
                name,
                data['count'],
                confidence,
                primary_role,
                top_affiliation,
                variants,
                len(data['files'])
            ])


def main():
    parser = argparse.ArgumentParser(
        description='Enhanced speaker extraction with context detection'
    )
    parser.add_argument('--output', default='speakers_enhanced',
                        help='Output file prefix')
    parser.add_argument('--sample', type=int, default=None,
                        help='Process only N files (for testing)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    print("=" * 70)
    print("  ENHANCED SPEAKER EXTRACTION")
    print("=" * 70)
    print()

    # Find transcripts
    print("Searching for transcript files...")
    all_files = find_all_transcripts()

    if args.sample:
        all_files = all_files[:args.sample]
        print(f"Processing {args.sample} files (sample mode)")
    else:
        print(f"Found {len(all_files)} transcript files")

    print()

    # Extract speakers
    extractor = EnhancedSpeakerExtractor(verbose=args.verbose)
    total_chars = 0

    for i, file_path in enumerate(all_files, 1):
        if i % 100 == 0 or i == len(all_files):
            print(f"  Processing {i}/{len(all_files)} files...", end='\r')

        try:
            text = file_path.read_text(encoding='utf-8', errors='ignore')
            total_chars += len(text)
            extractor.extract_from_file(file_path, text)
        except Exception as e:
            print(f"\n  Warning: Could not process {file_path}: {e}")

    print(f"\n  Total: {total_chars:,} characters from {len(all_files)} files")
    print()

    # Normalize
    print("Normalizing and deduplicating...")
    normalized = extractor.normalize_speakers()

    # Metadata
    metadata = {
        'extraction_date': datetime.now().isoformat(),
        'total_files': len(all_files),
        'total_chars': total_chars
    }

    # Export
    json_file = f'{args.output}.json'
    csv_file = f'{args.output}.csv'

    print(f"Exporting to {json_file}...")
    export_to_json(normalized, extractor, json_file, metadata)

    print(f"Exporting to {csv_file}...")
    export_to_csv(normalized, extractor, csv_file)

    # Summary
    print()
    print("=" * 70)
    print("  EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Total unique speakers: {len(normalized)}")
    print()

    # Role breakdown
    role_counts = Counter()
    conf_counts = {'high': 0, 'medium': 0, 'low': 0}

    for name, data in normalized.items():
        role = extractor.determine_primary_role(data['roles'])
        conf = extractor.get_confidence_level(data['count'])
        role_counts[role] += 1
        conf_counts[conf] += 1

    print("By role:")
    for role, count in role_counts.most_common():
        print(f"  {role:15s}: {count:4d}")

    print()
    print("By confidence:")
    print(f"  High (≥10):    {conf_counts['high']:4d}")
    print(f"  Medium (3-9):  {conf_counts['medium']:4d}")
    print(f"  Low (1-2):     {conf_counts['low']:4d}")
    print()

    # Top 20
    print("Top 20 speakers:")
    sorted_speakers = sorted(normalized.items(), key=lambda x: x[1]['count'], reverse=True)
    for i, (name, data) in enumerate(sorted_speakers[:20], 1):
        role = extractor.determine_primary_role(data['roles'])
        aff = ''
        if data['affiliations']:
            aff = f" ({data['affiliations'].most_common(1)[0][0]})"
        print(f"  {i:2d}. {name:30s} {data['count']:4d} [{role}]{aff}")

    print()
    print(f"Output files:")
    print(f"  - {json_file}")
    print(f"  - {csv_file}")
    print()


if __name__ == '__main__':
    main()
