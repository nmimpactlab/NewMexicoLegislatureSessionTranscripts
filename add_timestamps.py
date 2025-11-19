#!/usr/bin/env python3
"""
Add timestamps to existing transcript files.
Replaces [Chunk X] markers with [HH:MM:SS] timestamps.
"""

import re
from pathlib import Path


def chunk_to_timestamp(chunk_num, chunk_duration_seconds=60):
    """Convert chunk number to timestamp format HH:MM:SS"""
    # Chunk 1 starts at 0:00, Chunk 2 starts at 1:00, etc.
    start_seconds = (chunk_num - 1) * chunk_duration_seconds

    hours = start_seconds // 3600
    minutes = (start_seconds % 3600) // 60
    seconds = start_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def update_transcript_with_timestamps(transcript_file):
    """Update a transcript file to use timestamps instead of chunk markers"""
    print(f"Processing: {transcript_file}")

    try:
        # Read the file
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find and replace chunk markers with timestamps
        def replace_chunk(match):
            chunk_num = int(match.group(1))
            timestamp = chunk_to_timestamp(chunk_num)
            return f"[{timestamp}]"

        # Replace [Chunk X] with [HH:MM:SS]
        updated_content = re.sub(r'\[Chunk (\d+)\]', replace_chunk, content)

        # Check if any changes were made
        if updated_content != content:
            # Write back to file
            with open(transcript_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✓ Updated timestamps in {transcript_file}")
            return True
        else:
            print(f"- No chunk markers found in {transcript_file}")
            return False

    except Exception as e:
        print(f"✗ Error processing {transcript_file}: {str(e)}")
        return False


def main():
    transcript_dir = Path("transcripts")

    if not transcript_dir.exists():
        print(f"Error: {transcript_dir} directory not found!")
        return

    # Find all transcript files
    transcript_files = list(transcript_dir.glob("*_transcript.txt"))

    if not transcript_files:
        print("No transcript files found!")
        return

    print(f"Found {len(transcript_files)} transcript files")
    print("Converting chunk markers to timestamps...")

    updated_count = 0
    for transcript_file in transcript_files:
        if update_transcript_with_timestamps(transcript_file):
            updated_count += 1

    print(f"\nSummary: Updated {updated_count} transcript files")


if __name__ == "__main__":
    main()
