# Low Capitalization Transcript Analysis

## Issue Summary

During analysis of the transcript files, we identified transcripts with abnormally low capitalization rates that would cause name extraction failures. The name extraction tool (`ner_poc.py` and `extract_names_full.py`) relies on capital letters to identify proper names, so files with <2% capitalization will miss most speaker names.

## Analysis Results

**Sample Size**: 100 files examined
**Files with <2% capitals**: 13 files (13% of sample)

### Top 10 Problematic Files (Lowest Capitalization)

1. **0.368%** - House-AppropriationsandFinance_Monday_Feb20_2023_237PM-536PM - 2025-09-12.cc.txt
2. **0.489%** - House-AppropriationsandFinance_Monday_Mar1_2021_131PM-346PM - 2025-09-12.cc.txt
3. **0.723%** - House-AppropriationsandFinance_Friday_Feb10_2023_157PM-439PM - 2025-09-12.cc.txt
4. **0.842%** - House-AppropriationsandFinance_Friday_Jan27_2023_157PM-200PM - 2025-09-12.cc.txt
5. **1.244%** - House-AppropriationsandFinance_Saturday_Feb8_2025_1248PM-203PM - 2025-09-12.cc.txt
6. **1.250%** - House-AppropriationsandFinance_Saturday_Feb11_2023_1106AM-1239PM - 2025-09-12.cc.txt
7. **1.472%** - House-AppropriationsandFinance_Friday_Mar17_2023_719PM-801PM - 2025-09-12.cc.txt
8. **1.480%** - House-AppropriationsandFinance_Saturday_Feb4_2023_909AM-1114AM - 2025-09-12.cc.txt
9. **1.500%** - House-AppropriationsandFinance_Monday_Jan8_2024_131PM-517PM - 2025-09-12.cc.txt
10. **1.504%** - House-AppropriationsandFinance_Saturday_Feb13_2021_832AM-1051AM - 2025-09-12.cc.txt

## Pattern Analysis

### Common Characteristics

- **Committee**: All problematic files are from House Appropriations and Finance committee
- **Years**: Issues span 2021-2025
- **File Extension**: All are `.cc.txt` files (closed caption transcripts)
- **Severity**: Some files have <1% capitals (extremely low)

### Expected vs. Actual Capitalization

**Expected**: ~8-12% capital letters in normal English text
- Proper nouns (names, places)
- First letter of sentences
- Titles and headings
- Acronyms

**Actual in problematic files**: 0.3% - 1.5%
- Suggests OCR errors or automatic transcription issues
- May be entirely lowercase output from captioning system

## Impact on Name Extraction

### Extraction Methodology

Our name extraction tools use these strategies:
1. **Wave 1-3**: Look for capitalization patterns
2. **Wave 4**: Match title patterns like "Representative [Name]"
3. **Wave 5-7**: Additional validation and cleanup

**Critical Dependency**: All waves rely on proper capitalization to distinguish proper names from common words.

### Estimated Impact

If 13% of all 3,297 transcripts have this issue:
- **~428 files** may have severely reduced name extraction
- **~536 high-confidence names** extracted from 1,435 files
- **Potential loss**: Could be missing 20-30% of names from these files

## Root Cause Analysis

### Possible Causes

1. **Automatic Captioning System**
   - Some closed captioning systems output all lowercase
   - May be a setting or configuration issue

2. **OCR Preprocessing**
   - Text may have been converted to lowercase during processing
   - Original PDFs or video captions may have proper capitalization

3. **Data Source Issue**
   - Specific committee or time period may have different transcription vendor
   - House Appropriations may use different system than other committees

## Recommended Solutions

### Short-term Solutions

1. **Alternative Extraction Methods**
   ```python
   # Use context-based NER instead of capitalization
   # Look for patterns like:
   # - "representative smith said"
   # - "senator jones asked"
   # - "mr. williams responded"
   ```

2. **Title-based Extraction**
   ```python
   # Focus on title patterns that work without caps:
   pattern = r'\b(representative|senator|mr\.|ms\.|mrs\.|dr\.)\s+([a-z]+)\b'
   # Even in lowercase, titles indicate names
   ```

3. **Smart Capitalization Repair**
   ```python
   # Use dictionary/ML to identify likely proper nouns
   # Capitalize first letter after titles
   # Capitalize after sentence-ending punctuation
   ```

### Long-term Solutions

1. **Source Data Investigation**
   - Contact NM Legislature IT/Records department
   - Request original transcripts with proper capitalization
   - Check if newer versions available

2. **Automated Capitalization Restoration**
   ```python
   # Use NER model trained on legislative text
   # Apply capitalization based on:
   # - Known legislator names database
   # - Common title patterns
   # - Sentence structure
   ```

3. **Manual Review Process**
   - Flag low-capitalization files for review
   - Cross-reference with official attendance records
   - Build ground truth dataset for training

## Action Items

### Immediate (Low Effort)

- [x] Document the issue with examples
- [ ] Create script to identify all affected files
- [ ] Generate full list of low-cap files (not just sample)
- [ ] Add warning in extraction documentation

### Medium-term (Moderate Effort)

- [ ] Implement context-based name extraction
- [ ] Create title-pattern-only extraction mode
- [ ] Test alternative extraction on low-cap files
- [ ] Compare results with original extraction

### Long-term (High Effort)

- [ ] Contact NM Legislature for source data
- [ ] Develop ML-based capitalization restoration
- [ ] Build legislator database for validation
- [ ] Re-run extraction on restored files

## Code to Identify All Affected Files

```python
#!/usr/bin/env python3
"""
Identify all transcript files with low capitalization rates
"""

from pathlib import Path

def check_capitalization(file_path, sample_size=2000):
    """Check capitalization rate in first N characters"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sample = f.read(sample_size)

        if len(sample) < 100:
            return None

        letters = [c for c in sample if c.isalpha()]
        if not letters:
            return None

        cap_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        return cap_ratio
    except:
        return None

# Find all low-cap files
low_cap_files = []
for txt_file in Path('.').glob('**/*.txt'):
    ratio = check_capitalization(txt_file)
    if ratio and ratio < 0.02:  # Less than 2%
        low_cap_files.append((txt_file, ratio))

# Report
print(f"Found {len(low_cap_files)} files with <2% capitalization")
for file_path, ratio in sorted(low_cap_files, key=lambda x: x[1]):
    print(f"{ratio:.3%} - {file_path}")
```

## References

- Name extraction tool: `extract_names_full.py`
- POC tool: `ner_poc.py`
- Results: `extracted_names_final.csv` (2,301 unique names)
- Speakers directory: `docs/speakers.html`

## Notes

This issue affects data quality for the Speakers Directory on the public analysis website. Users searching for names from these affected transcripts may not find results, even though the speakers are mentioned in the source material.

**Priority**: Medium
**Estimated Effort**: 2-4 hours for complete analysis, 8-16 hours for restoration solution
