#!/usr/bin/env python3
"""
Download Audio from Sliq.net Legislative Videos

This tool downloads audio from New Mexico Legislature videos hosted on sliq.net
for re-transcription. It extracts HLS stream URLs from sliq.net pages and uses
yt-dlp to download audio in WAV format.

The sliq.net platform embeds HLS stream URLs in JavaScript variables on the page.
This tool extracts those URLs and downloads just the audio track.

Usage:
    # Download audio from a single video
    python download_sliq_audio.py --url "https://sg001-harmony.sliq.net/00293/Harmony/en/PowerBrowser/PowerBrowserV2/20251119/-1/77887" --output audio/

    # Process list of URLs from file
    python download_sliq_audio.py --urls urls.txt --output audio/

    # Re-download problematic low-capitalization transcripts
    python download_sliq_audio.py --fix-low-cap --output audio/

Example URL format:
    https://sg001-harmony.sliq.net/00293/Harmony/en/PowerBrowser/PowerBrowserV2/YYYYMMDD/-1/CONTENT_ID
"""

import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


def extract_hls_url(page_url: str, verbose: bool = False) -> Optional[str]:
    """
    Extract HLS stream URL from sliq.net page

    The page embeds stream URLs in JavaScript like:
    availableStreams.push({url: "https://...playlist.m3u8", ...});

    Returns: HLS playlist URL or None if not found
    """

    if verbose:
        print(f"\nFetching page: {page_url}")

    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = Request(page_url, headers=headers)

        with urlopen(request, timeout=30) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Look for availableStreams.push({url: "..."})
        pattern = r'availableStreams\.push\(\{[^}]*url:\s*["\']([^"\']+\.m3u8[^"\']*)["\']'

        matches = re.findall(pattern, html)

        if matches:
            # Return the first HLS URL found
            hls_url = matches[0]
            if verbose:
                print(f"✓ Found HLS URL: {hls_url}")
            return hls_url

        if verbose:
            print("✗ No HLS URL found in page")

        # Try alternative pattern
        pattern2 = r'["\']https://[^"\']*\.m3u8[^"\']*["\']'
        matches2 = re.findall(pattern2, html)

        if matches2:
            # Clean quotes
            hls_url = matches2[0].strip('"\'')
            if verbose:
                print(f"✓ Found HLS URL (alt pattern): {hls_url}")
            return hls_url

        return None

    except (HTTPError, URLError) as e:
        print(f"✗ Error fetching page: {e}")
        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def download_audio(hls_url: str, output_path: Path, filename: str = None, verbose: bool = False) -> bool:
    """
    Download audio from HLS stream using yt-dlp

    Downloads in WAV format for compatibility with speech recognition

    Returns: True if successful, False otherwise
    """

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename if not provided
    if not filename:
        # Extract from URL or use timestamp
        filename = "audio_download"

    # Remove extension if provided
    filename = Path(filename).stem

    output_file = output_path / f"{filename}.wav"

    if verbose:
        print(f"\nDownloading audio to: {output_file}")

    # yt-dlp command to download audio only
    cmd = [
        'yt-dlp',
        '--extract-audio',
        '--audio-format', 'wav',
        '--audio-quality', '0',  # Best quality
        '--output', str(output_file),
        hls_url
    ]

    try:
        if verbose:
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True)
        else:
            result = subprocess.run(cmd, check=True, capture_output=True)

        if output_file.exists():
            if verbose:
                print(f"✓ Downloaded: {output_file}")
            return True
        else:
            print(f"✗ Download failed: Output file not created")
            return False

    except subprocess.CalledProcessError as e:
        print(f"✗ yt-dlp error: {e}")
        if verbose and e.stderr:
            print(e.stderr.decode())
        return False
    except FileNotFoundError:
        print("✗ yt-dlp not found. Install with: pip install yt-dlp")
        return False


def download_from_url(page_url: str, output_path: Path, filename: str = None, verbose: bool = False) -> bool:
    """
    Download audio from sliq.net page URL

    Returns: True if successful, False otherwise
    """

    # Extract HLS URL from page
    hls_url = extract_hls_url(page_url, verbose=verbose)

    if not hls_url:
        print(f"✗ Could not extract HLS URL from: {page_url}")
        return False

    # Download audio
    return download_audio(hls_url, output_path, filename=filename, verbose=verbose)


def process_url_list(urls_file: Path, output_path: Path, verbose: bool = False):
    """
    Process list of URLs from file

    File format: One URL per line, optionally with filename:
        https://...  filename1
        https://...  filename2
    """

    if not urls_file.exists():
        print(f"✗ URLs file not found: {urls_file}")
        return

    with open(urls_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    print(f"\nProcessing {len(lines)} URLs...")

    success_count = 0
    fail_count = 0

    for i, line in enumerate(lines, 1):
        parts = line.split()
        url = parts[0]
        filename = parts[1] if len(parts) > 1 else f"audio_{i:03d}"

        print(f"\n[{i}/{len(lines)}] Processing: {url}")

        if download_from_url(url, output_path, filename=filename, verbose=verbose):
            success_count += 1
        else:
            fail_count += 1

    print(f"\n{'=' * 70}")
    print(f"Complete: {success_count} successful, {fail_count} failed")
    print(f"{'=' * 70}")


def fix_low_capitalization_files(output_path: Path, verbose: bool = False):
    """
    Re-download and transcribe the 13 low-capitalization files

    This is a placeholder that would need:
    1. Mapping of transcript filenames to sliq.net URLs
    2. Database or scraping to find the correct video URLs

    For now, this lists the problematic files.
    """

    print("\n" + "=" * 70)
    print("Low Capitalization Files - Re-download Required")
    print("=" * 70)

    # From LOW_CAPITALIZATION_ISSUE.md
    problematic_files = [
        ("0.368%", "House-AppropriationsandFinance_Monday_Feb20_2023_237PM-536PM - 2025-09-12.cc.txt"),
        ("0.489%", "House-AppropriationsandFinance_Monday_Mar1_2021_131PM-346PM - 2025-09-12.cc.txt"),
        ("0.723%", "House-AppropriationsandFinance_Friday_Feb10_2023_157PM-439PM - 2025-09-12.cc.txt"),
        ("0.842%", "House-AppropriationsandFinance_Friday_Jan27_2023_157PM-200PM - 2025-09-12.cc.txt"),
        ("1.244%", "House-AppropriationsandFinance_Saturday_Feb8_2025_1248PM-203PM - 2025-09-12.cc.txt"),
        ("1.250%", "House-AppropriationsandFinance_Saturday_Feb11_2023_1106AM-1239PM - 2025-09-12.cc.txt"),
        ("1.472%", "House-AppropriationsandFinance_Friday_Mar17_2023_719PM-801PM - 2025-09-12.cc.txt"),
        ("1.480%", "House-AppropriationsandFinance_Saturday_Feb4_2023_909AM-1114AM - 2025-09-12.cc.txt"),
        ("1.500%", "House-AppropriationsandFinance_Monday_Jan8_2024_131PM-517PM - 2025-09-12.cc.txt"),
        ("1.504%", "House-AppropriationsandFinance_Saturday_Feb13_2021_832AM-1051AM - 2025-09-12.cc.txt"),
    ]

    print("\nProblematic files (sorted by capitalization rate):\n")
    for cap_rate, filename in problematic_files:
        print(f"  {cap_rate:>6s} - {filename}")

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("\n1. Find sliq.net URLs for these transcripts")
    print("   - Parse transcript metadata to extract date/committee")
    print("   - Search sliq.net for matching videos")
    print("   - Create URL mapping file")
    print("\n2. Download audio using this tool:")
    print(f"   python download_sliq_audio.py --urls urls_to_redownload.txt --output {output_path}")
    print("\n3. Re-transcribe using YouTube transcriber:")
    print("   python youtube_transcriber.py --audio-dir audio/ --output transcripts_fixed/")
    print("\n4. Replace original low-quality .cc.txt files")
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Download audio from sliq.net legislative videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download single video
  python download_sliq_audio.py --url "https://sg001-harmony.sliq.net/00293/.../77887" --output audio/

  # Process URL list
  python download_sliq_audio.py --urls urls.txt --output audio/

  # Show low-capitalization files that need re-download
  python download_sliq_audio.py --fix-low-cap --output audio/
        """
    )

    parser.add_argument('--url',
                        help='Single sliq.net page URL to download')
    parser.add_argument('--urls',
                        help='File containing list of URLs (one per line)')
    parser.add_argument('--fix-low-cap', action='store_true',
                        help='Show low-capitalization files that need re-download')
    parser.add_argument('--output', default='audio',
                        help='Output directory for audio files (default: audio/)')
    parser.add_argument('--filename',
                        help='Output filename (without extension, only used with --url)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    output_path = Path(args.output)

    # Validate arguments
    if not any([args.url, args.urls, args.fix_low_cap]):
        parser.print_help()
        return

    print("=" * 70)
    print("Sliq.net Audio Downloader")
    print("=" * 70)

    # Process based on arguments
    if args.fix_low_cap:
        fix_low_capitalization_files(output_path, verbose=args.verbose)

    elif args.url:
        success = download_from_url(args.url, output_path, filename=args.filename, verbose=args.verbose)
        if success:
            print("\n✓ Download complete")
        else:
            print("\n✗ Download failed")
            sys.exit(1)

    elif args.urls:
        process_url_list(Path(args.urls), output_path, verbose=args.verbose)


if __name__ == '__main__':
    main()
