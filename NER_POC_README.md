# Named Entity Recognition - Proof of Concept

## Overview

This POC demonstrates a **progressive wave-based approach** to extracting person names from legislative transcripts. Each wave applies a different filter or strategy, making the process transparent and educational.

## Running the POC

```bash
python3 ner_poc.py
```

The script will:
1. Load sample transcript files from Education, Judiciary, and Appropriations committees
2. Process them through 7 progressive waves
3. Show results after each wave
4. Save final results to `ner_poc_results.json`

## The 7 Waves

### Wave 1: Extract Capitalized Sequences
**Strategy**: Cast a wide net - capture everything that looks like it might be a proper name

- Matches Title Case words: "Representative Chatfield"
- Matches ALL CAPS: "HSD", "LESC"
- **Result**: 287 potential entities

### Wave 2: Remove Common English Words
**Strategy**: Filter out common words that happen to be capitalized

- Removes: "The", "And", "For", "With", "From", etc.
- **Result**: 249 candidates (38 removed)

### Wave 3: Remove Domain-Specific Words
**Strategy**: Filter out legislative and procedural terminology

- Removes: "Committee", "Chairman", "Session", "Bill", "Amendment"
- Removes: Days of week, months, time references
- Removes: Transcript artifacts ("Inaudible", "Applause")
- **Result**: 188 candidates (61 removed)

### Wave 4: Title-Based Name Extraction
**Strategy**: Look for names that follow titles (more precise approach)

**Pattern**: `[Title] [Name]`
- Titles: Representative, Senator, Mr, Ms, Chairman, etc.
- Names: 1-3 capitalized words
- **Handles OCR errors**: Matches both "Representative Brown" and "Representative brown"

**Result**: 218 unique name candidates

**Examples found**:
- "Representative Ezzell"
- "Representative Small"
- "Representative Trujillo"
- "Representative Brown"
- "Mr Dixon"

### Wave 5: Frequency Filtering
**Strategy**: Names should appear multiple times; one-off mentions are likely errors

- Minimum threshold: 2 mentions
- Rationale: Real people speak/are mentioned multiple times
- Single mentions are often OCR errors or context words
- **Result**: 19 candidates (199 removed)

### Wave 6: Validation Filters
**Strategy**: Apply multiple validation checks to reject non-names

**Checks**:
1. ✓ Must contain vowels (reject OCR garbage like "XZQRT")
2. ✓ Reasonable length (2-50 characters)
3. ✓ Not all single letters ("A B C")
4. ✓ Not common phrases ("Thank You", "Of The")
5. ✓ Doesn't end with stop words ("and", "or", "the", "of", "members")
6. ✓ Doesn't start with stop words ("thank", "and", "the", "that")
7. ✓ No weird characters (newlines, tabs)
8. ✓ At least one word looks like a name (proper structure, vowels, reasonable length)

**Result**: 3 validated names (16 removed)

**Removed examples**:
- "Chair Thank You" (common phrase)
- "Chairman And Members" (ends with stop words)
- "Representative This Is" (no name-like pattern)

**Validated names**:
- Ezzell (3 mentions)
- Small (2 mentions)
- Trujillo (2 mentions)

### Wave 7: Normalization and Deduplication
**Strategy**: Cluster similar names that are likely the same person

**Techniques**:
- Exact match on normalized form
- Substring matching ("Maestas" matches "Maestas Bergman")
- Simple similarity scoring (85% threshold)

**Result**: 3 unique entities (final output)

## Results from Sample Data

Processing 3 transcript files (78,959 characters):

| Wave | Entities | Description |
|------|----------|-------------|
| 1 | 287 | All capitalized sequences |
| 2 | 249 | After removing common words |
| 3 | 188 | After removing domain words |
| 4 | 218 | Title-based extraction |
| 5 | 19 | After frequency filter (≥2) |
| 6 | 3 | After validation |
| 7 | 3 | Final unique entities |

**Final Results**:
1. **Ezzell** (3 mentions) - Representative
2. **Small** (2 mentions) - Representative
3. **Trujillo** (2 mentions) - Representative

## Key Features

### 1. Zero Dependencies
- Uses only Python standard library
- No ML libraries required (spaCy, NLTK, etc.)
- Can run anywhere Python 3.6+ is installed

### 2. Transparent Progression
- See results after each wave
- Understand why entities were kept or rejected
- Educational value - shows reasoning

### 3. Handles OCR Errors
- Mixed case: "Representative brown" → "Brown"
- Spacing issues
- Common OCR substitutions

### 4. Configurable
- Adjust frequency thresholds
- Modify blacklists (common words, domain words)
- Change validation rules
- Tune similarity thresholds

### 5. Extensible Architecture
- Easy to add new waves
- Can add new title patterns
- Can add new validation checks
- Foundation for full NER toolkit

## Comparison with Current System

| Aspect | Current (build_index.py) | POC (ner_poc.py) |
|--------|-------------------------|------------------|
| Approach | Single-pass regex | 7-wave progressive |
| Visibility | Final results only | Results at each stage |
| Blacklist | 120+ hardcoded terms | Organized by category |
| Validation | Frequency + vowel check | 9 different checks |
| OCR handling | Basic | Better (mixed case) |
| Extensibility | Monolithic function | Modular waves |

## Next Steps

### Immediate Improvements
1. **Add more sample files** - Test on more diverse transcripts
2. **Tune thresholds** - Experiment with frequency minimums
3. **Expand blacklists** - Add more domain-specific terms
4. **Better normalization** - Implement phonetic matching (Soundex, Metaphone)

### Future Enhancements
1. **Organization extraction** - Apply similar wave approach to organizations
2. **Location extraction** - Extract NM cities, counties, regions
3. **ML integration** - Optional spaCy support for better accuracy
4. **Context extraction** - Capture surrounding text for each mention
5. **Confidence scoring** - Weight different validation factors

### Integration
1. **Replace extract_speakers()** - Use this approach in build_index.py
2. **A/B comparison** - Compare results with current system
3. **Performance testing** - Benchmark on full dataset
4. **Configuration files** - Move blacklists to external YAML/JSON

## Design Principles Demonstrated

### 1. Progressive Refinement
Start broad, narrow down iteratively. Each wave has a clear purpose.

### 2. Fail Loudly
Show what's being removed and why. Makes debugging easy.

### 3. Separation of Concerns
Each wave does one thing well. Easy to modify or disable waves.

### 4. Configuration Over Code
Blacklists and thresholds should be data, not code.

### 5. Observable Behavior
User can see the system thinking at each step.

## Example Output

```
██████████████████████████████████████████████████████████████████████
  NAMED ENTITY RECOGNITION - PROGRESSIVE WAVE EXTRACTION
██████████████████████████████████████████████████████████████████████

Processing 78959 characters of text...

======================================================================
WAVE 1: Extract All Capitalized Sequences (Title Case)
======================================================================
Found 287 entities
Sample: AGD, Active, Albuquerque, Amanda, American...

======================================================================
WAVE 2: Remove Common English Words
======================================================================
Removed 38 common words
Examples: After, All, And, At, Be, But, For...
Found 249 entities

[... continues through all waves ...]

======================================================================
WAVE 7: Normalization and Deduplication
======================================================================
Clustered 3 names into 3 unique entities

Final results:
  1. Ezzell (3 mentions)
  2. Small (2 mentions)
  3. Trujillo (2 mentions)

======================================================================
SUMMARY
======================================================================
Wave 1 - Capitalized sequences:   287
Wave 2 - After common words:      249
Wave 3 - After domain words:      188
Wave 4 - Title-based names:       218
Wave 5 - Frequent names (≥2):      19
Wave 6 - Validated names:           3
Wave 7 - Final unique entities:     3
```

## Usage Tips

### Adjusting Sensitivity

**Too many false positives?**
- Increase frequency threshold in `run_all_waves(min_frequency=3)`
- Add more terms to blacklists in Wave 2/3
- Make validation stricter in Wave 6

**Too many false negatives?**
- Lower frequency threshold to 1
- Reduce blacklists
- Relax validation rules
- Check Wave 4 output for missed names

### Custom Titles

Add new titles in Wave 4:
```python
titles = [
    'Representative', 'Senator',
    'Your Custom Title',  # Add here
]
```

### Custom Blacklists

Modify in Waves 2, 3, and 6:
```python
# Wave 2: Common words
common_words = {'the', 'and', 'your', 'words'}

# Wave 3: Domain words
domain_words = {'committee', 'your', 'domain', 'terms'}

# Wave 6: Phrase blacklist
phrase_blacklist = {'thank you', 'your', 'phrases'}
```

## Files

- `ner_poc.py` - Main POC script
- `ner_poc_results.json` - Output from last run
- `NER_TOOLKIT_DESIGN.md` - Full architecture design
- `NER_POC_README.md` - This file

## Questions?

This POC demonstrates the feasibility of robust name extraction without ML. The wave-based approach provides transparency and makes it easy to tune for different datasets or entity types.

Next: Apply the same principles to extract organizations, locations, and other entity types!
