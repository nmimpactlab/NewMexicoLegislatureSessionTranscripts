# Data Quality Notes

## Speaker Extraction Limitations

### OCR Quality Issues

The transcript files in this repository were generated using automated speech recognition (ASR) and optical character recognition (OCR). While the content is generally accurate, there are known issues affecting speaker name extraction:

#### Duplicate Names Due to OCR Variations

Some legislators appear under multiple name variations due to OCR errors. Examples:

- **"Ivey-Soto"** appears as: "Ivey Soto" (281 mentions), "Ivy Soto" (157 mentions)
- **"Sedillo Lopez"** appears as: "Sedillo Lopez" (258), "Cedillo Lopez" (53), "Sadia Lopez" (30), "Sidia Lopez" (29), "Sio Lopez" (25), "Serio Lopez" (24), "Sidil Lopez" (24), "Cedil Lopez" (21)
- **"Roybal Caballero"** appears as: "Roybal Caballero" (202), "Royal Caballero" (58)
- **"Peter Wirth"** appears as: "Peter Wirth" (61), "Peter Worth" (28)

#### What We Did to Mitigate

1. **Strict Pattern Matching**: Only extract names following specific patterns (e.g., "Representative FirstName LastName")
2. **Comprehensive Blacklisting**: Filter out common words misidentified as names (e.g., "New Mexico", "Chairman", "Committee")
3. **Minimum Mention Threshold**: Only include speakers mentioned 3+ times across all transcripts (filtered out 2,777 low-frequency OCR errors)
4. **Vowel Validation**: Reject names without vowels (often OCR garbage)
5. **Geographic Name Filtering**: Remove city/state names that appeared due to OCR errors

#### Results

- **Before filtering**: 78,199 "speakers" (mostly false positives)
- **After strict patterns**: 3,253 speakers
- **After frequency filtering**: 380 speakers with 3+ mentions

#### Why Not Further Consolidation?

Automatically merging OCR variants (e.g., "Ivey" → "Ivy") is risky because:
- Some similar names are actually different people
- Edit distance algorithms could incorrectly merge legitimate different legislators
- Without an authoritative legislator roster, manual verification would be required

#### Using the Data

When searching or analyzing speakers:
- **Be aware** that some legislators may appear under slight name variations
- **Search broadly** - try variations of names if needed
- **Focus on high-count speakers** for most reliable data
- **Bill and committee data** is much more reliable (less affected by OCR)

## Bill Extraction

Bill extraction is highly reliable as bill numbers follow strict patterns (HB 123, SB 456) that are less susceptible to OCR errors.

**Stats**: 1,452 unique bills indexed across 3,294 sessions

## Committee Extraction

Committee names are extracted from standardized filenames and are highly accurate.

**Stats**: 68 committees indexed

## Recommendations for Users

1. **Primary Use Cases**:
   - Searching for bill discussions ✅ (highly reliable)
   - Finding committee sessions ✅ (highly reliable)
   - Browsing by date/time ✅ (highly reliable)

2. **Secondary Use Cases**:
   - Speaker-based searches ⚠️ (be aware of name variations)
   - Speaker frequency analysis ⚠️ (some duplicate counts due to OCR)

3. **Future Improvements**:
   - Manual curation of speaker name mappings
   - Cross-referencing with official NM Legislature rosters
   - Potential re-OCR of source documents with better tools

## Data Source

All transcripts are official New Mexico Legislature committee session recordings, processed through automated transcription services. The underlying session content is accurate; only automated name extraction is affected by OCR quality.

---

Last Updated: 2025-11-16
