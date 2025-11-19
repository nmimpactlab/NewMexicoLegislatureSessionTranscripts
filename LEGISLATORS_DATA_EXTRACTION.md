# Legislator Data Extraction Guide

This guide explains how to extract official legislator data from nmlegis.gov and cross-reference it with the names extracted from transcripts.

## Overview

We have created five tools to handle different scenarios for getting legislator data:

1. **`parse_legislators_cards.py`** - Parse card/thumbnail layout (RECOMMENDED for basic data)
2. **`scrape_legislator_details.py`** - Enhance with detail page data (committees, contact info)
3. **`parse_legislators_dropdown.py`** - Parse dropdown select HTML (name and chamber only)
4. **`parse_legislators_html.py`** - Parse table-based HTML layouts
5. **`scrape_legislators.py`** - Direct web scraping (may be blocked by site)

## Quick Start: Recommended Method

The nmlegis.gov website displays legislators in a card/thumbnail layout with complete information. Here's the easiest way to extract the data:

### Step 1: Save the Page

1. Visit https://www.nmlegis.gov/members/Legislator_List?T=R (current legislators)
2. Right-click on the page → "Save Page As..."
3. Save as `legislators_current.html` (save complete page)

### Step 2: Parse the HTML

```bash
# Install dependencies (if needed)
pip install beautifulsoup4

# Parse the saved page
python parse_legislators_cards.py legislators_current.html --output legislators_official

# This creates:
# - legislators_official.json (with full details)
# - legislators_official.csv (spreadsheet format)
```

**What data is extracted:**
- Full name, first name, last name
- Legislator ID (e.g., "HABMI")
- Chamber (House or Senate)
- Party (Democratic, Republican, etc.)
- District number
- Profile URL
- Photo URL

### Step 3: (Optional) Enhance with Detail Page Data

To get additional information like committees, contact info, and district maps:

```bash
# Option A: Scrape detail pages from web (slow, may be blocked)
python scrape_legislator_details.py legislators_official.json --web -o legislators_complete

# Option B: Save detail pages manually and parse (recommended)
# 1. Visit a few legislator profile pages
# 2. Save each as HTML (e.g., HABMI.html, SPADR.html)
# 3. Parse all at once:
python scrape_legislator_details.py --from-html *.html -o legislators_complete
```

**Additional data extracted from detail pages:**
- Committees (list)
- Email address
- Phone number
- Capitol room number
- Counties represented
- District map PDF link
- Leadership positions
- Biography (if available)

### Step 4: (Optional) Get Former Legislators

Repeat the same process for former legislators:

1. Visit https://www.nmlegis.gov/Members/Former_Legislator_List
2. Inspect and copy the dropdown HTML
3. Save as `legislators_former.html`
4. Parse: `python parse_legislators_dropdown.py legislators_former.html --output legislators_former`

## Alternative Methods

### Method 1: Direct Web Scraping

If the website allows it (may return 403 errors):

```bash
pip install requests beautifulsoup4

# Scrape current and former legislators
python scrape_legislators.py --current --former --output legislators_official
```

### Method 2: Save Full HTML Page

If you prefer to save the entire page:

1. Visit the legislator list page
2. Right-click → "Save Page As" → save as `legislators_page.html`
3. Run: `python parse_legislators_html.py legislators_page.html --output legislators_official`

## Cross-Referencing with Extracted Names

Once you have the official legislator data, you can cross-reference it with the names extracted from transcripts:

### Option A: Manual Cross-Reference

1. Open `legislators_directory.csv` (2,301 extracted names)
2. Open `legislators_official.csv` (official list)
3. Use spreadsheet VLOOKUP or similar to match by last name
4. Fill in chamber, party, district for matched entries
5. Mark `verified` as TRUE for confirmed matches

### Option B: Automated Cross-Reference (TODO)

Create a script to automatically match:

```python
# TODO: Create cross_reference_legislators.py
# - Load both datasets
# - Match by last name (fuzzy matching for OCR errors)
# - Flag high-confidence matches
# - Export merged dataset
```

## Files Generated

### From Transcript Extraction

- `legislators_directory.json` - 2,301 extracted names with metadata
- `legislators_directory.csv` - Same data in spreadsheet format
- `LEGISLATORS_CROSS_REFERENCE.md` - Verification report

### From Official Sources

- `legislators_official.json` - Official legislator data
- `legislators_official.csv` - Official data in spreadsheet format

### Merged/Cross-Referenced (After manual or automated matching)

- `legislators_verified.json` - Merged dataset with verified info
- `legislators_verified.csv` - Spreadsheet format

## Data Fields

### Extracted from Transcripts

```json
{
  "name": "Lopez",
  "last_name": "Lopez",
  "frequency": 1074,
  "confidence": "high",
  "variants": ["Sil Lopez", "Cedilla Lopez", "Sidia Lopez"],
  "chamber": "Unknown",  // To be filled from official data
  "party": "Unknown",
  "district": "Unknown",
  "years_active": [],
  "committees": [],
  "verified": false
}
```

### From Official Sources

```json
{
  "full_name": "Michelle Paulene Abeyta",
  "first_name": "Michelle Paulene",
  "last_name": "Abeyta",
  "legislator_id": "HABMI",
  "chamber": "House",
  "party": "Democratic",  // May need detail page scraping
  "district": "12",
  "status": "current"
}
```

## Detailed Instructions

### Getting Party and District Data

The dropdown only provides names and chamber. To get party/district info:

**Option 1: Manual Lookup**
- Click each legislator in the dropdown to visit their detail page
- Copy party and district info
- Paste into the CSV

**Option 2: Automated Detail Page Scraping**
- Modify `scrape_legislators.py` to follow links and scrape detail pages
- Extract party, district, committees, contact info

### Handling OCR Errors

The extracted names contain OCR variations. When cross-referencing:

1. **Fuzzy String Matching**: Use libraries like `fuzzywuzzy` or `rapidfuzz`
   ```python
   from rapidfuzz import fuzz
   similarity = fuzz.ratio("Sedillo Lopez", "Sil Lopez")
   # Returns similarity score
   ```

2. **Last Name Matching**: Start by matching just last names
   - "Lopez" matches "Sedillo Lopez", "Sil Lopez", etc.

3. **Manual Review**: High-frequency names (>100 mentions) should be manually verified

## Next Steps

1. **Extract official data** using one of the methods above
2. **Cross-reference** extracted vs official names
3. **Verify high-confidence names** (≥10 mentions) first
4. **Fill in metadata** (chamber, party, district) for verified legislators
5. **Export verified dataset** for use in analysis tools

## Integration with Public Analysis Tool

Once you have verified legislator data:

1. Update `docs/speakers_extracted.json` with verified info
2. Add chamber/party/district filters to `docs/speakers.html`
3. Link to legislator detail pages
4. Show legislator photos if available

## Troubleshooting

### "403 Forbidden" or "SSL Error"
- Use the manual HTML download method
- The site may block automated requests

### "No legislators extracted"
- Check the HTML structure in your browser's Inspector
- Adjust the parsing logic in the scripts
- Look for `<table>`, `<select>`, or `<div>` containers

### Missing data (party, district, etc.)
- The dropdown may not include all fields
- You'll need to scrape individual legislator detail pages
- Or manually enter data from the website

## References

- **Current Legislators**: https://www.nmlegis.gov/members/Legislator_List?T=R
- **Former Legislators**: https://www.nmlegis.gov/Members/Former_Legislator_List
- **Ballotpedia**: https://ballotpedia.org/New_Mexico_State_Legislature
- **Wikipedia**: https://en.wikipedia.org/wiki/New_Mexico_Legislature

## Support Files

- `legislators_import_template.json` - Template for manual data entry
- `build_legislators_directory.py` - Builds directory from extracted names
- `LEGISLATORS_CROSS_REFERENCE.md` - Top 50 most frequent names for verification
