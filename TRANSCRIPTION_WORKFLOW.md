# Transcription Workflow

## Overview

This repository contains tools for transcribing New Mexico Legislature videos and extracting structured data from transcripts.

## Complete Transcription Pipeline

### 1. **YouTube Videos** → Audio Transcription

**Tools:**
- `update_channel_and_transcribe.py` - Main orchestration script
- `youtube_transcriber.py` - Core transcription engine
- `add_timestamps.py` - Post-processing for timestamps

**Workflow:**
```bash
# Download and transcribe YouTube channel
python update_channel_and_transcribe.py --channel-url "https://youtube.com/@channel"

# Or process individual video
python youtube_transcriber.py --video-url "https://youtube.com/watch?v=..." --output transcripts/

# Convert [Chunk X] markers to [HH:MM:SS] timestamps
python add_timestamps.py
```

**Technology Stack:**
- **yt-dlp**: Downloads audio from YouTube
- **Google Speech Recognition API**: Primary transcription (free tier)
- **Sphinx**: Offline fallback transcription
- **pydub**: Audio chunking (60-second segments)

**Output Format:**
```
[00:00:00] Speaker discusses HB 123...
[00:01:00] Representative Smith responds...
```

### 2. **Sliq.net Videos** → Audio Re-transcription

**Tool:** `download_sliq_audio.py`

**Purpose:** Re-download and re-transcribe problematic .cc.txt files with low capitalization

**Workflow:**

#### Step 1: Download Audio from Sliq.net

```bash
# Single video
python download_sliq_audio.py \
  --url "https://sg001-harmony.sliq.net/00293/Harmony/en/PowerBrowser/PowerBrowserV2/20251119/-1/77887" \
  --output audio/ \
  --filename "HouseAppropriations_2023-02-20"

# Batch download from URL list
python download_sliq_audio.py \
  --urls sliq_urls.txt \
  --output audio/

# Show files that need re-download
python download_sliq_audio.py --fix-low-cap
```

**URL List Format** (`sliq_urls.txt`):
```
https://sg001-harmony.sliq.net/.../77887  HouseAppropriations_2023-02-20
https://sg001-harmony.sliq.net/.../77888  HouseAppropriations_2023-03-01
```

#### Step 2: Transcribe Downloaded Audio

```bash
# Use YouTube transcriber on sliq.net audio
python youtube_transcriber.py \
  --audio-dir audio/ \
  --output transcripts_fixed/
```

#### Step 3: Convert to Final Format

```bash
# Add timestamps
python add_timestamps.py
```

### 3. **Extract Structured Data from Transcripts**

#### Extract Speaker Names

**Tool:** `extract_names_full.py`

```bash
# Extract names from all transcripts
python extract_names_full.py --output extracted_names_final

# Sample extraction
python extract_names_full.py --sample 100 --output names_sample
```

**Output:**
- `extracted_names_final.json` - Full name data with frequencies
- `extracted_names_final.csv` - Name list with transcript references

**Results:**
- 2,301 unique speaker names extracted
- 536 high-confidence names from 1,435 files
- Searchable directory at `docs/speakers.html`

#### Extract Bill References

**Tool:** `extract_bill_references.py`

```bash
# Extract bills from all transcripts
python extract_bill_references.py --output bills_extracted

# Sample extraction
python extract_bill_references.py --sample 100 --output bills_test
```

**Output:**
- `bills_extracted.json` - Full bill data with metadata
- `bills_extracted.csv` - Summary by bill type
- `bills_extracted_detailed.csv` - Bill-to-transcript mapping

**Results:**
- 1,432 unique bills extracted
- Searchable directory at `docs/bills.html`
- Supports filtering by year

## Low-Capitalization Issue

**Problem:** 13% of transcript files have <2% capital letters (see `LOW_CAPITALIZATION_ISSUE.md`)

**Root Cause:** Closed caption system outputs lowercase text

**Impact:** Name extraction fails on these files (relies on capitalization)

**Solution:** Re-download from sliq.net and re-transcribe with proper speech recognition

**Affected Files:**
- All from House Appropriations and Finance committee
- Years: 2021-2025
- Extension: `.cc.txt`

**Top Priority Files** (worst capitalization):
1. `House-AppropriationsandFinance_Monday_Feb20_2023_237PM-536PM - 2025-09-12.cc.txt` (0.368%)
2. `House-AppropriationsandFinance_Monday_Mar1_2021_131PM-346PM - 2025-09-12.cc.txt` (0.489%)
3. `House-AppropriationsandFinance_Friday_Feb10_2023_157PM-439PM - 2025-09-12.cc.txt` (0.723%)

## Public Analysis Website

**Location:** `docs/`

**Features:**
- **Speakers Directory** (`docs/speakers.html`) - Search 2,301 speaker names
- **Bills Directory** (`docs/bills.html`) - Browse 1,432 bills with year filtering
- Responsive design
- Client-side search and filtering

## Dependencies

```bash
# Install Python dependencies
pip install yt-dlp pydub SpeechRecognition pocketsphinx

# System dependencies (for audio processing)
sudo apt-get install ffmpeg portaudio19-dev

# For sliq.net downloads
# yt-dlp handles HLS streams automatically
```

## Data Quality Notes

### High-Quality Transcripts
- YouTube videos transcribed with Google Speech Recognition
- Proper capitalization and punctuation
- Timestamp markers for navigation
- ~8-12% capital letter ratio (expected)

### Low-Quality Transcripts (.cc.txt)
- Automated closed captions from original source
- Many files have <2% capitals
- Reduced name extraction accuracy
- Should be re-transcribed from sliq.net audio source

## File Organization

```
NewMexicoLegislatureSessionTranscripts/
├── transcripts/                  # Original .cc.txt files (3,297 files)
├── audio/                        # Downloaded audio for re-transcription
├── transcripts_fixed/            # Re-transcribed files (high quality)
├── docs/                         # Public analysis website
│   ├── speakers.html            # Speaker name directory
│   ├── bills.html               # Bills directory
│   └── extracted_names.json     # Speaker data
├── bills_extracted.json          # Bill reference data
├── LOW_CAPITALIZATION_ISSUE.md   # Detailed issue analysis
└── TRANSCRIPTION_WORKFLOW.md     # This file

# Core Tools
├── update_channel_and_transcribe.py   # YouTube pipeline orchestrator
├── youtube_transcriber.py             # Speech recognition engine
├── add_timestamps.py                  # Timestamp post-processing
├── download_sliq_audio.py             # Sliq.net audio downloader
├── extract_names_full.py              # Name extraction
└── extract_bill_references.py         # Bill reference extraction
```

## Next Steps

### Immediate Actions

1. **Map transcript filenames to sliq.net URLs**
   - Parse transcript metadata to extract date/committee
   - Search sliq.net catalog for matching videos
   - Create URL mapping file for 13 low-cap files

2. **Re-download and re-transcribe problematic files**
   ```bash
   # Download audio
   python download_sliq_audio.py --urls low_cap_urls.txt --output audio/

   # Transcribe
   python youtube_transcriber.py --audio-dir audio/ --output transcripts_fixed/

   # Add timestamps
   python add_timestamps.py
   ```

3. **Re-run name extraction on fixed transcripts**
   ```bash
   python extract_names_full.py --transcripts transcripts_fixed/ --output names_fixed
   ```

### Long-term Improvements

1. **Automate sliq.net catalog scraping**
   - Build index of all available videos
   - Create automatic mapping between .cc.txt and video URLs
   - Enable bulk re-downloading

2. **Enhance extraction accuracy**
   - Train custom NER model on legislative text
   - Build legislator name database for validation
   - Implement context-based name extraction (doesn't rely on caps)

3. **Data validation**
   - Cross-reference extracted names with official rosters
   - Validate bill numbers against legislative database
   - Build ground truth dataset for quality metrics

## License

See LICENSE file for details.

## Contact

For questions about this workflow or the data extraction tools, see the repository issues page.
