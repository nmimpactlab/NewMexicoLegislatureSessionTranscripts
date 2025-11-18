# Name Extraction - Usage Guide

## Quick Start

When you add new transcripts to the database, run this command to extract person names:

```bash
python3 extract_names_full.py --min-frequency 2
```

This will generate:
- `extracted_names_final.csv` - Spreadsheet format for manual review
- `extracted_names_final.json` - Structured data with metadata

## Command Options

```bash
# Basic extraction (recommended)
python3 extract_names_full.py --min-frequency 2

# Include single-mention names (more comprehensive, more false positives)
python3 extract_names_full.py --min-frequency 1

# Test on sample (for quick testing)
python3 extract_names_full.py --sample 50 --min-frequency 2

# Custom output prefix
python3 extract_names_full.py --output-prefix monthly_update_2025_01

# Verbose mode (see all 7 waves)
python3 extract_names_full.py --verbose --min-frequency 2
```

## Output Files

### CSV Format (`extracted_names_final.csv`)

Columns:
- **Name**: Normalized name (canonical form)
- **Frequency**: Number of mentions across all transcripts
- **Variants**: OCR variations and alternate spellings (separated by `;`)
- **Confidence_Level**: High (≥10), Medium (3-9), or Low (1-2)

**Use for**: Import into spreadsheets, manual review, tagging false positives

### JSON Format (`extracted_names_final.json`)

```json
{
  "metadata": {
    "extraction_date": "2025-...",
    "total_files_processed": 1435,
    "total_names_found": 2301,
    ...
  },
  "summary_statistics": {
    "high_confidence": 536,
    "medium_confidence": 903,
    "low_confidence": 862
  },
  "entities": [
    {
      "name": "Lopez",
      "frequency": 1074,
      "confidence_level": "high",
      "variants": ["Sil Lopez", "Sedillo Lopez", ...]
    },
    ...
  ]
}
```

**Use for**: Programmatic access, database import, integration with other tools

## Results Interpretation

### Confidence Levels

| Level | Frequency | Characteristics | Action |
|-------|-----------|-----------------|--------|
| **High** | ≥10 mentions | Very reliable, active speakers | Use directly |
| **Medium** | 3-9 mentions | Reliable, occasional speakers | Quick review recommended |
| **Low** | 1-2 mentions | Mixed (real names + false positives) | Manual review required |

### Expected False Positives

**Low-confidence entries** (frequency 1-2) may include:
- Partial phrases: "Episode Is Right", "At This Yes"
- Context words: "Focus", "Political"
- Real but rare speakers: "Keogh", "Baron", "Reece"

**Trade-off**: We prioritize finding all real names over eliminating false positives. Better to have a few false positives you can tag than to miss actual speakers.

## Manual Review Workflow

1. **Open CSV in spreadsheet software** (Excel, Google Sheets, LibreOffice)

2. **Sort by Confidence_Level** (High → Medium → Low)

3. **Review High confidence** (≥10 mentions)
   - These are almost always correct
   - Validate against known legislators/speakers
   - Flag any obvious errors

4. **Review Medium confidence** (3-9 mentions)
   - Most should be correct
   - Check for phrase fragments
   - Verify less common names

5. **Review Low confidence** (1-2 mentions)
   - Expect ~30-40% false positives
   - Tag as "NOT_PERSON" for filtering
   - Keep real but rare speakers

6. **Add tagging column**
   ```csv
   Name,Frequency,Variants,Confidence_Level,Status
   Lopez,1074,,High,VALIDATED
   Episode Is Right,2,,Low,NOT_PERSON
   Keogh,2,,Low,VALIDATED
   ```

## Integration with Existing System

### Compare with current build_index.py results

```bash
# Extract current speakers from index
python3 -c "
import json
with open('docs/index.json') as f:
    data = json.load(f)
    current_speakers = set(data['speakers'].keys())
    print(f'Current system: {len(current_speakers)} speakers')

# Compare with new extraction
import csv
with open('extracted_names_final.csv') as f:
    reader = csv.DictReader(f)
    new_names = {row['Name'] for row in reader if row['Confidence_Level'] in ['High', 'Medium']}
    print(f'New extraction: {len(new_names)} names (High+Medium confidence)')

# Find differences
only_old = current_speakers - new_names
only_new = new_names - current_speakers
print(f'Only in old: {len(only_old)}')
print(f'Only in new: {len(only_new)}')
"
```

### Replace extract_speakers() in build_index.py

You can eventually replace the current `extract_speakers()` function with this new toolkit for improved accuracy and better handling of OCR errors.

## Full Dataset Statistics (Current Run)

**Date**: 2025-01-XX
**Files processed**: 1,435 transcripts
**Total characters**: 139,089,379
**Processing time**: ~60 seconds

**Results**:
- Total entities: 2,301
- High confidence (≥10): 536 names
- Medium confidence (3-9): 903 names
- Low confidence (1-2): 862 names

**Top 20 Names**:
1. Lopez (1,074 mentions)
2. Wood (988)
3. Padilla (986)
4. Trujillo (782)
5. Martinez (775)
6. Steinborn (685)
7. Armstrong (678)
8. Hickey (669)
9. Mcqueen (668)
10. Scott (662)
11. Gonzalez (647)
12. Brandt (598)
13. Townsend (582)
14. Dixon (537)
15. Joshua Sanchez (531)
16. Stewart (527)
17. Figueroa (492)
18. Garcia (488)
19. Pope (486)
20. Garrett (474)

## Updating with New Transcripts

When new transcripts are added:

1. **Add new .cc.txt files** to appropriate committee directories

2. **Run extraction**:
   ```bash
   python3 extract_names_full.py --min-frequency 2 --output-prefix update_$(date +%Y%m%d)
   ```

3. **Review new names**:
   - Compare with previous extraction
   - Focus on names that didn't exist before
   - Validate high-frequency new names

4. **Update master list**:
   - Merge with existing validated names
   - Maintain tagging/status information
   - Archive old extractions for reference

## Troubleshooting

### "No transcript files found"
- Run from repository root directory
- Check that .cc.txt files exist in committee directories

### "Too many false positives"
- Increase `--min-frequency` threshold (try 3 or 5)
- Review low-confidence entries separately
- Consider updating blacklists in `ner_poc.py` Wave 6

### "Missing known speakers"
- Lower `--min-frequency` to 1
- Check if name has OCR variations (look in Variants column)
- Review Wave 6 validation logs (run with `--verbose`)

## Advanced Usage

### Process specific directories
```python
# Modify extract_names_full.py find_all_transcripts() to filter:
def find_all_transcripts(base_dir: Path = Path('.')):
    transcript_files = []
    # Only process Judiciary committee
    for txt_file in base_dir.glob('Judiciary/**/*.cc.txt'):
        transcript_files.append(txt_file)
    return sorted(transcript_files)
```

### Custom confidence thresholds
```python
# In export_to_csv(), modify confidence calculation:
if total_count >= 20:  # More strict
    confidence = 'High'
elif total_count >= 5:
    confidence = 'Medium'
else:
    confidence = 'Low'
```

### Export to database
```python
import json
import sqlite3

# Load extracted names
with open('extracted_names_final.json') as f:
    data = json.load(f)

# Insert into database
conn = sqlite3.connect('speakers.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS speakers
             (name TEXT, frequency INTEGER, confidence TEXT,
              variants TEXT)''')

for entity in data['entities']:
    c.execute('INSERT INTO speakers VALUES (?,?,?,?)',
              (entity['name'], entity['frequency'],
               entity['confidence_level'],
               '; '.join(entity['variants'])))

conn.commit()
```

## Next Steps

Possible enhancements:
- **Organization extraction**: Apply same wave-based approach to org names
- **Location extraction**: Extract cities, counties, regions
- **Context extraction**: Capture surrounding text for each mention
- **Speaker attribution**: Link extracted names to transcript segments
- **Confidence scoring**: ML-based scoring instead of just frequency
- **Web interface**: Interactive review and tagging interface

## Questions or Issues?

- Check `NER_TOOLKIT_DESIGN.md` for architecture details
- Check `NER_POC_README.md` for technical documentation
- Review wave-by-wave processing in `ner_poc.py`
- Test on small samples with `--sample` flag first
