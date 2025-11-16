#!/usr/bin/env python3
"""
Build searchable index of New Mexico Legislature Session Transcripts
Extracts: speakers, bills, sessions, dates, times, and committees
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import hashlib

def parse_filename(filename):
    """
    Parse transcript filename to extract metadata
    Example: House-TaxationandRevenue_Wednesday_Feb7_2024_839AM-1147AM - 2025-09-12.cc.txt
    """
    # Remove extension and timestamp suffix
    name = filename.replace('.cc.txt', '').replace('.cc.raw.json', '')
    name = re.sub(r' - \d{4}-\d{2}-\d{2}$', '', name)

    # Split into parts
    parts = name.split('_')

    if len(parts) < 5:
        return None

    # Extract chamber and committee
    chamber_committee = parts[0].split('-')
    chamber = chamber_committee[0] if len(chamber_committee) > 0 else 'Unknown'
    committee = chamber_committee[1] if len(chamber_committee) > 1 else 'Unknown'

    # Parse committee name (convert CamelCase to spaces)
    committee = re.sub(r'([a-z])([A-Z])', r'\1 \2', committee)

    day_of_week = parts[1]

    # Parse date
    month = parts[2][:3]
    day = parts[2][3:]
    year = parts[3]

    # Parse time
    time_range = parts[4] if len(parts) > 4 else ''

    # Convert month abbreviation to number
    month_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
    }

    month_num = month_map.get(month, '01')
    date_str = f"{year}-{month_num}-{day.zfill(2)}"

    # Parse time range
    time_parts = time_range.split('-')
    start_time = time_parts[0] if len(time_parts) > 0 else ''
    end_time = time_parts[1] if len(time_parts) > 1 else ''

    # Format times (e.g., "839AM" -> "8:39 AM")
    def format_time(t):
        if not t:
            return ''
        match = re.match(r'(\d{1,2})(\d{2})(AM|PM)', t)
        if match:
            hour, minute, period = match.groups()
            return f"{hour}:{minute} {period}"
        return t

    start_time = format_time(start_time)
    end_time = format_time(end_time)

    return {
        'chamber': chamber,
        'committee': committee,
        'day_of_week': day_of_week,
        'date': date_str,
        'start_time': start_time,
        'end_time': end_time
    }

def extract_speakers(content):
    """
    Extract speaker names from transcript content
    Looks for patterns like "Representative Smith", "Senator Jones", etc.
    Uses strict patterns and filtering to avoid false positives from OCR errors.

    Note: Due to OCR quality in transcripts, some speaker names may have
    spelling variations or be missed entirely.
    """
    speakers = set()

    # Comprehensive blacklist for filtering false positives
    blacklist = {
        # Common words
        'customer', 'chamber', 'chambers', 'committee', 'member', 'members',
        'speaker', 'chair', 'chairman', 'chairwoman', 'chairperson',
        'representative', 'senator', 'delegate', 'mister', 'madam',
        'dunking', 'surrounding', 'term', 'patrol', 'session',
        'thank', 'thanks', 'welcome', 'morning', 'afternoon', 'evening',
        'question', 'questions', 'comment', 'comments', 'motion',
        'bill', 'bills', 'vote', 'votes', 'floor', 'gallery',
        'public', 'audience', 'room', 'meeting', 'day', 'time',
        'point', 'order', 'minute', 'minutes', 'second', 'seconds',
        'good', 'great', 'next', 'first', 'last', 'end', 'start',
        'please', 'present', 'absent', 'here', 'there', 'all',
        'issue', 'matter', 'subject', 'topic', 'item', 'agenda',

        # Geographic names that appear due to OCR errors
        'new', 'mexico', 'mexicans', 'york', 'albuquerque', 'santa',
        'hobbs', 'cruces', 'roswell', 'farmington', 'espanola',
        'hospital', 'university', 'state', 'city', 'county',

        # Common OCR errors
        'small', 'elizabeth', 'liz', 'southern', 'newman',
        'google', 'hospital', 'department', 'district'
    }

    # More strict patterns - require proper title and name structure
    patterns = [
        # Representative/Senator + First + Last name (both capitalized)
        r'(?:Representative|Rep\.)\s+([A-Z][a-z]{2,})\s+([A-Z][a-z]{2,})',
        r'(?:Senator|Sen\.)\s+([A-Z][a-z]{2,})\s+([A-Z][a-z]{2,})',
        # Chairman/Chairwoman + Last name
        r'(?:Chairman|Chairwoman)\s+([A-Z][a-z]{3,})',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            if len(match.groups()) == 2:
                # First and last name
                first, last = match.groups()

                # Check blacklist
                if first.lower() in blacklist or last.lower() in blacklist:
                    continue

                # Reject if contains "New Mexico" pattern
                if 'new' in first.lower() and 'mexico' in last.lower():
                    continue
                if 'mexico' in first.lower() or 'new' in last.lower():
                    continue

                # Reject names with too many consonants (OCR errors)
                def has_vowel_pattern(word):
                    vowels = set('aeiouAEIOU')
                    return any(c in vowels for c in word)

                if not has_vowel_pattern(first) or not has_vowel_pattern(last):
                    continue

                # Reject if looks like an OCR error (e.g., "Cedila", "Cedilo" variants)
                # These often have unusual character patterns
                full_name = f"{first} {last}"

                # Additional validation
                if len(first) >= 3 and len(last) >= 3:
                    speakers.add(full_name)
            else:
                # Single name (like Chairman Smith)
                name = match.group(1).strip()
                if (name.lower() not in blacklist and
                    len(name) >= 4 and
                    any(c in 'aeiouAEIOU' for c in name)):
                    speakers.add(name)

    return list(speakers)

def extract_bills(content):
    """
    Extract bill references from transcript content
    Looks for patterns like "House Bill 123", "HB 123", "Senate Bill 456", "SB 456"
    """
    bills = set()

    # Patterns for bill identification
    patterns = [
        r'House\s+Bill\s+(\d+)',
        r'HB\s*(\d+)',
        r'Senate\s+Bill\s+(\d+)',
        r'SB\s*(\d+)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            bill_num = match.group(1)

            # Determine bill type
            if 'house' in pattern.lower() or 'hb' in pattern.lower():
                bill_id = f"HB {bill_num}"
            else:
                bill_id = f"SB {bill_num}"

            bills.add(bill_id)

    return list(bills)

def process_transcript_file(file_path):
    """
    Process a single transcript file and extract all metadata
    """
    filename = os.path.basename(file_path)

    # Parse filename metadata
    metadata = parse_filename(filename)
    if not metadata:
        return None

    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

    # Extract speakers and bills
    speakers = extract_speakers(content)
    bills = extract_bills(content)

    # Generate unique session ID
    session_id = hashlib.md5(f"{filename}".encode()).hexdigest()[:16]

    # Create excerpt (first 500 characters)
    # Remove line numbers from .txt files
    excerpt_text = re.sub(r'^\s*\d+→', '', content[:2000], flags=re.MULTILINE)
    excerpt = excerpt_text[:500].strip()

    return {
        'id': session_id,
        'filename': filename,
        'file_path': file_path.replace('/home/user/NewMexicoLegislatureSessionTranscripts/', ''),
        'chamber': metadata['chamber'],
        'committee': metadata['committee'],
        'day_of_week': metadata['day_of_week'],
        'date': metadata['date'],
        'start_time': metadata['start_time'],
        'end_time': metadata['end_time'],
        'speakers': sorted(speakers),
        'bills': sorted(bills),
        'excerpt': excerpt
    }

def build_index():
    """
    Build complete index of all transcripts
    """
    print("Building index...")

    sessions = []
    speaker_index = defaultdict(lambda: {'count': 0, 'sessions': []})
    bill_index = defaultdict(lambda: {'count': 0, 'sessions': []})
    committee_index = defaultdict(lambda: {'count': 0, 'sessions': []})

    # Find all .txt transcript files
    base_path = Path('/home/user/NewMexicoLegislatureSessionTranscripts')
    txt_files = list(base_path.glob('**/*.cc.txt'))

    print(f"Found {len(txt_files)} transcript files")

    # Process each file
    for i, file_path in enumerate(txt_files):
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(txt_files)} files...")

        session_data = process_transcript_file(str(file_path))

        if session_data:
            sessions.append(session_data)

            # Update speaker index
            for speaker in session_data['speakers']:
                speaker_index[speaker]['count'] += 1
                speaker_index[speaker]['sessions'].append(session_data['id'])

            # Update bill index
            for bill in session_data['bills']:
                bill_index[bill]['count'] += 1
                bill_index[bill]['sessions'].append(session_data['id'])

            # Update committee index
            committee = session_data['committee']
            committee_index[committee]['count'] += 1
            committee_index[committee]['sessions'].append(session_data['id'])

    # Sort sessions by date (most recent first)
    sessions.sort(key=lambda x: x['date'], reverse=True)

    # Filter speakers with minimum threshold to reduce OCR noise
    # Real legislators appear many times; OCR errors are usually one-offs
    MIN_SPEAKER_MENTIONS = 3
    filtered_speakers = {
        k: v for k, v in speaker_index.items()
        if v['count'] >= MIN_SPEAKER_MENTIONS
    }

    print(f"\nFiltered {len(speaker_index) - len(filtered_speakers)} low-frequency speakers (< {MIN_SPEAKER_MENTIONS} mentions)")
    print(f"Retained {len(filtered_speakers)} speakers with {MIN_SPEAKER_MENTIONS}+ mentions")

    # Create final index structure
    index = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_sessions': len(sessions),
            'total_speakers': len(filtered_speakers),
            'total_bills': len(bill_index),
            'total_committees': len(committee_index),
            'min_speaker_mentions': MIN_SPEAKER_MENTIONS,
            'note': 'Speaker extraction is limited by OCR quality in source transcripts. Some names may have spelling variations.'
        },
        'sessions': sessions,
        'speakers': {k: dict(v) for k, v in sorted(filtered_speakers.items())},
        'bills': {k: dict(v) for k, v in sorted(bill_index.items())},
        'committees': {k: dict(v) for k, v in sorted(committee_index.items())}
    }

    print(f"\nIndex built successfully!")
    print(f"Total sessions: {len(sessions)}")
    print(f"Unique speakers: {len(speaker_index)}")
    print(f"Unique bills: {len(bill_index)}")
    print(f"Committees: {len(committee_index)}")

    return index

def save_index(index, output_path='docs/index.json'):
    """
    Save index to JSON file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\nIndex saved to {output_path}")

    # Also save a compressed version
    import gzip
    compressed_path = output_path + '.gz'
    with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)

    print(f"Compressed index saved to {compressed_path}")

if __name__ == '__main__':
    index = build_index()
    save_index(index)
    print("\nDone!")
