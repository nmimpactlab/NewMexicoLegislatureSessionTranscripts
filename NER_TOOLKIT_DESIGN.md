# Named Entity Recognition Toolkit - Design Document

## Overview

A modular, extensible toolkit for extracting proper names from text datasets, designed to handle OCR noise, variations, and different entity types with appropriate strategies.

## Architecture

### Core Principles

1. **Abstraction**: Base classes define interfaces, specific extractors implement strategies
2. **Composability**: Multiple strategies can be combined and weighted
3. **Configurability**: Behavior controlled through config files, not code changes
4. **Zero-dependency core**: Basic functionality works with stdlib only
5. **Optional ML**: Advanced features available when ML libraries installed

### Class Hierarchy

```
EntityExtractor (ABC)
├── PersonExtractor
│   ├── RegexPersonExtractor
│   ├── StatisticalPersonExtractor
│   └── MLPersonExtractor (optional: spaCy)
├── OrganizationExtractor
│   ├── RegexOrganizationExtractor
│   ├── PatternOrganizationExtractor
│   └── MLOrganizationExtractor (optional: spaCy)
├── LocationExtractor
├── LegislationExtractor
└── CompositeExtractor (combines multiple extractors)
```

### Entity Types & Strategies

#### 1. **Person Names**

**Challenges**:
- OCR errors (e.g., "REPRESENTATIVE MAESTAS" vs "REPRESENTATIVE MAESTRAS")
- Title variations (Rep, Representative, Senator, Sen, Mr., Ms., Dr.)
- Name formats (First Last, Last First, Middle initials)
- Incomplete names from OCR

**Strategies**:

A. **Regex Strategy** (fast, no dependencies)
```python
# Pattern matching for common formats:
- "[Title] [First] [Last]"
- "[Title] [Last]"
- "[First] [Last]" (when capitalized in context)
```

B. **Statistical Strategy** (stdlib only)
```python
# Features:
- Capitalization patterns (Title Case)
- Position after titles/honorifics
- Frequency analysis (real names appear multiple times)
- Context windows (words before/after)
- Vowel-consonant patterns (reject OCR garbage)
```

C. **ML Strategy** (optional: spaCy)
```python
# Use pre-trained NER models:
- spaCy's en_core_web_sm/lg
- Custom training on legislative transcripts
- Confidence scoring
```

#### 2. **Organization Names**

**Challenges**:
- Varied structures (acronyms, full names, descriptive)
- Government agencies vs companies vs advocacy groups
- Mixed case in OCR

**Strategies**:

A. **Pattern-based** (stdlib only)
```python
# Common patterns:
- "[Org Type] of [Location]" (Department of Health)
- Acronyms in all caps (EPA, HHS, NMPED)
- "The [Name] [Org Type]" (The Children's Cabinet)
- Possessives (New Mexico's...)
```

B. **Dictionary-based** (stdlib only)
```python
# Known entity lists:
- NM state agencies (from data/nm_agencies.txt)
- Common federal agencies
- Major organizations in transcripts
- Fuzzy matching for OCR variations
```

C. **ML Strategy** (optional: spaCy)
```python
# NER model trained for ORG entities
# Better at novel organization names
```

#### 3. **Locations**

**Strategies**:
- Dictionary of NM cities, counties
- US states and major cities
- Pattern: "[City], New Mexico"
- GeoNames database integration (optional)

#### 4. **Legislation References**

**Strategies**:
- Regex (highly reliable for "HB 123", "SB 456")
- Pattern variations: "House Bill", "Senate Bill"
- Session-specific formatting

### Entity Validation & Scoring

Each extracted entity gets a confidence score (0.0-1.0) based on:

```python
class Entity:
    text: str              # Raw extracted text
    entity_type: str       # PERSON, ORG, LOCATION, etc.
    normalized: str        # Normalized form
    confidence: float      # 0.0-1.0
    context: str          # Surrounding text
    positions: List[int]   # Character positions in document
    metadata: dict        # Strategy-specific info
```

**Scoring factors**:
- **Frequency**: More mentions → higher confidence
- **Context consistency**: Same context → higher confidence
- **Pattern match strength**: Clean pattern → higher confidence
- **Validation checks**: Passes checks → higher confidence
- **Cross-validation**: Multiple strategies agree → higher confidence

### Name Normalization

Handle OCR variations and name variations:

```python
class NameNormalizer:
    def normalize_person(name: str) -> str:
        # Remove titles
        # Standardize spacing
        # Handle common OCR errors (l→I, O→0)
        # Phonetic matching (Soundex, Metaphone)

    def normalize_organization(name: str) -> str:
        # Expand acronyms
        # Standardize punctuation
        # Handle abbreviations (Dept → Department)
```

### Deduplication

Group similar entities:

```python
class EntityDeduplicator:
    def deduplicate(entities: List[Entity]) -> List[EntityCluster]:
        # Strategies:
        # - Exact match on normalized form
        # - Fuzzy string matching (Levenshtein distance)
        # - Phonetic matching
        # - Substring matching
        #
        # Returns clusters of similar entities
```

## Configuration

### Entity Extractor Config (YAML)

```yaml
extractors:
  person:
    enabled: true
    strategies:
      - name: regex
        weight: 1.0
        config:
          min_frequency: 3
          title_required: true
          blacklist_file: data/name_blacklist.txt
      - name: statistical
        weight: 0.8
        config:
          context_window: 10
          min_confidence: 0.6
      - name: ml
        weight: 1.2
        enabled: false  # Requires spaCy
        config:
          model: en_core_web_lg

    normalization:
      remove_titles: true
      phonetic_matching: true
      common_ocr_fixes:
        - ["MAESTRAS", "MAESTAS"]
        - ["l", "I"]

    deduplication:
      similarity_threshold: 0.85
      strategy: levenshtein

    validation:
      min_length: 3
      max_length: 50
      require_vowels: true
      blacklist_patterns:
        - "^[A-Z]{5,}$"  # All caps 5+ chars (likely OCR error)
        - "^[0-9]"       # Starts with number

  organization:
    enabled: true
    strategies:
      - name: pattern
        weight: 1.0
      - name: dictionary
        weight: 1.2
        config:
          dictionary_file: data/known_organizations.txt
          fuzzy_threshold: 0.9

  legislation:
    enabled: true
    strategies:
      - name: regex
        weight: 1.0
        config:
          patterns:
            - 'HB\s*\d+'
            - 'SB\s*\d+'
            - 'House Bill\s+\d+'
            - 'Senate Bill\s+\d+'
```

## Usage Examples

### Basic Usage (Stdlib Only)

```python
from ner_toolkit import PersonExtractor, OrganizationExtractor

# Initialize extractors
person_extractor = PersonExtractor.from_config('config/extractors.yaml')
org_extractor = OrganizationExtractor.from_config('config/extractors.yaml')

# Extract from text
text = open('transcript.txt').read()
persons = person_extractor.extract(text)
orgs = org_extractor.extract(text)

# Results
for person in persons:
    print(f"{person.normalized} (confidence: {person.confidence:.2f})")
    print(f"  Mentions: {len(person.positions)}")
    print(f"  Context: {person.context[:50]}...")
```

### Advanced Usage (Multiple Strategies)

```python
from ner_toolkit import CompositeExtractor, MLPersonExtractor

# Combine multiple strategies
extractor = CompositeExtractor([
    RegexPersonExtractor(weight=1.0),
    StatisticalPersonExtractor(weight=0.8),
    MLPersonExtractor(weight=1.2)  # Requires spaCy
])

entities = extractor.extract(text)

# Filter by confidence
high_confidence = [e for e in entities if e.confidence > 0.8]

# Deduplicate
from ner_toolkit import EntityDeduplicator
deduper = EntityDeduplicator(threshold=0.85)
clusters = deduper.deduplicate(entities)

for cluster in clusters:
    canonical = cluster.get_canonical()  # Most confident variant
    variants = cluster.get_variants()
    print(f"{canonical.normalized} ({len(variants)} variants)")
```

### Integration with Existing Code

```python
# Modify build_index.py to use new toolkit
from ner_toolkit import PersonExtractor, CompositeExtractor

# Old code:
# speakers = extract_speakers(text)

# New code:
person_extractor = PersonExtractor.from_config('config/extractors.yaml')
entities = person_extractor.extract(text)

# Convert to existing format
speakers = set()
for entity in entities:
    if entity.confidence > 0.7:  # Configurable threshold
        speakers.add(entity.normalized)
```

## Implementation Plan

### Phase 1: Core Framework (Stdlib Only)
- [ ] Base `EntityExtractor` abstract class
- [ ] `Entity` and `EntityCluster` data classes
- [ ] Configuration loading (YAML/JSON)
- [ ] Basic validation utilities

### Phase 2: Person Extraction
- [ ] `RegexPersonExtractor` with configurable patterns
- [ ] `StatisticalPersonExtractor` with context analysis
- [ ] `NameNormalizer` for person names
- [ ] Person-specific validation

### Phase 3: Organization Extraction
- [ ] `PatternOrganizationExtractor`
- [ ] `DictionaryOrganizationExtractor`
- [ ] Known organization dictionaries (NM agencies, etc.)

### Phase 4: Supporting Tools
- [ ] `EntityDeduplicator` with multiple strategies
- [ ] `EntityScorer` for confidence calculation
- [ ] `ContextExtractor` for surrounding text

### Phase 5: Optional ML Support
- [ ] `MLPersonExtractor` using spaCy
- [ ] `MLOrganizationExtractor` using spaCy
- [ ] Model training utilities

### Phase 6: Integration & Testing
- [ ] Update `build_index.py` to use toolkit
- [ ] Compare results with current extraction
- [ ] Performance benchmarking
- [ ] Documentation and examples

## File Structure

```
ner_toolkit/
├── __init__.py
├── base.py              # Abstract base classes
├── entity.py            # Entity and EntityCluster classes
├── config.py            # Configuration loading
├── extractors/
│   ├── __init__.py
│   ├── person.py        # Person extractors
│   ├── organization.py  # Organization extractors
│   ├── location.py      # Location extractors
│   └── legislation.py   # Legislation extractors
├── normalization/
│   ├── __init__.py
│   ├── names.py         # Name normalization
│   └── phonetic.py      # Phonetic matching
├── validation/
│   ├── __init__.py
│   └── validators.py    # Validation utilities
├── deduplication/
│   ├── __init__.py
│   └── deduper.py       # Deduplication strategies
└── ml/                  # Optional ML components
    ├── __init__.py
    └── spacy_extractors.py

config/
├── extractors.yaml      # Main configuration
└── validation_rules.yaml

data/
├── name_blacklist.txt
├── known_organizations.txt
├── nm_agencies.txt
└── common_titles.txt
```

## Benefits

1. **Modular**: Easy to add new entity types or strategies
2. **Testable**: Each component can be tested independently
3. **Configurable**: Tune without code changes
4. **Scalable**: Works with stdlib, scales with ML libraries
5. **Reusable**: Not tied to NM Legislature transcripts
6. **Maintainable**: Clear separation of concerns
7. **Documented**: Self-documenting through config and types
