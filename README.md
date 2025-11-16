# New Mexico Legislature Session Transcripts

A comprehensive, searchable database of New Mexico Legislature committee hearing transcripts.

## Live Search Tool

**[Access the searchable database here](https://nmimpactlab.github.io/NewMexicoLegislatureSessionTranscripts/)**

## Features

- **Full-Text Search**: Search across all 3,294+ legislative session transcripts
- **Advanced Filtering**: Filter by committee, year, bill number, or speaker
- **Bills Index**: Browse 1,452+ bills discussed in legislative sessions
- **Speakers Directory**: Explore 78,000+ speaker mentions across sessions
- **Committee Overview**: View all 68 legislative committees
- **Session Details**: Access date, time, speakers, bills, and transcript excerpts

## Statistics

- **Total Sessions**: 3,294 committee hearings indexed
- **Bills Tracked**: 1,452 unique bills
- **Speakers Indexed**: 380 speakers (with 3+ mentions)*
- **Committees**: 68 legislative committees
- **Date Range**: 2021-2025

\* *Note: Due to OCR quality in source transcripts, some speaker names may appear with spelling variations. See [DATA_QUALITY.md](DATA_QUALITY.md) for details.*

## Data Structure

The repository contains:
- **Transcript Files**: Raw transcripts in both `.txt` and `.json` formats
- **Index**: Pre-built searchable index (`docs/index.json`)
- **Search Interface**: Static web application for browsing and searching

## Usage

### Online Search Tool

Visit the [live search interface](https://nmimpactlab.github.io/NewMexicoLegislatureSessionTranscripts/) to:
1. Search for specific topics, bills, or speakers
2. Filter sessions by committee, year, or bill number
3. Browse all bills, speakers, and committees
4. View session transcripts and metadata

### Building the Index Locally

To rebuild the index from source transcripts:

```bash
python3 build_index.py
```

This will:
1. Parse all transcript files
2. Extract speakers, bills, dates, times, and metadata
3. Generate `docs/index.json` and `docs/index.json.gz`

### Requirements

- Python 3.6+
- No external dependencies required

## Data Sources

Transcripts are organized by committee:
- Appropriations and Finance
- Commerce & Economic Development
- Conservation
- Corporations and Transportation
- Education
- Finance
- Health and Human Services
- Health and Public Affairs
- Judiciary
- Taxation and Revenue
- And 58 more committees

## File Naming Convention

Transcript files follow this pattern:
```
{Chamber}-{Committee}_{DayOfWeek}_{Date}_{Time} - {ProcessDate}.cc.{ext}
```

Example:
```
House-TaxationandRevenue_Wednesday_Feb7_2024_839AM-1147AM - 2025-09-12.cc.txt
```

## Contributing

This is a public archive. To contribute:
1. Report issues or suggest improvements via GitHub Issues
2. Submit pull requests with corrections or enhancements

## License

The transcripts are public records of the New Mexico Legislature.

## Acknowledgments

Built for transparency and public access to legislative proceedings.

---

**Last Updated**: 2025-11-16
**Maintained by**: NM Impact Lab
