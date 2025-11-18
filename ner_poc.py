#!/usr/bin/env python3
"""
Named Entity Recognition - Proof of Concept
Progressive Wave-based Extraction

This POC demonstrates how to extract person names from legislative transcripts
using progressive refinement. Each wave adds a filter or strategy, making the
process transparent and educational.
"""

import re
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Set, List, Dict, Tuple


class WaveExtractor:
    """Progressive entity extraction with visible stages"""

    def __init__(self, text: str, verbose: bool = True):
        self.text = text
        self.verbose = verbose
        self.results = {}

    def print_wave_header(self, wave_num: int, title: str):
        """Print a clear header for each wave"""
        if self.verbose:
            print("\n" + "="*70)
            print(f"WAVE {wave_num}: {title}")
            print("="*70)

    def print_wave_results(self, entities: Set[str], sample_size: int = 20):
        """Print results from a wave"""
        if self.verbose:
            print(f"\nFound {len(entities)} entities")
            if entities:
                print(f"\nSample (showing up to {sample_size}):")
                for i, entity in enumerate(sorted(entities)[:sample_size], 1):
                    print(f"  {i:3d}. {entity}")
                if len(entities) > sample_size:
                    print(f"  ... and {len(entities) - sample_size} more")

    def wave1_extract_capitalized(self) -> Set[str]:
        """
        WAVE 1: Extract all capitalized sequences

        Strategy: Find any sequence of Title Case words (Capital + lowercase)
        This is the broadest net - captures everything that might be a proper name.
        Examples: "Representative Maestas", "New Mexico", "David Archuleta"
        """
        self.print_wave_header(1, "Extract All Capitalized Sequences (Title Case)")

        # Pattern: Title Case words (Capital letter followed by lowercase)
        # Can be single word or multiple words in sequence
        # Examples: "Representative", "David Archuleta", "New Mexico"
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'

        matches = re.findall(pattern, self.text)

        # Also capture ALL CAPS sequences (acronyms and such)
        caps_pattern = r'\b[A-Z]{2,}\b(?:\s+[A-Z]{2,}\b)*'
        caps_matches = re.findall(caps_pattern, self.text)

        entities = set(matches + caps_matches)

        self.print_wave_results(entities, sample_size=30)
        self.results['wave1_capitalized'] = entities
        return entities

    def wave2_remove_common_words(self, entities: Set[str]) -> Set[str]:
        """
        WAVE 2: Remove common English words

        Strategy: Filter out common English words (case-insensitive)
        Examples: "The", "And", "For", "This", etc.
        """
        self.print_wave_header(2, "Remove Common English Words")

        # Common English words that appear in transcripts (normalized to lowercase for matching)
        common_words = {
            'the', 'and', 'or', 'but', 'for', 'with', 'from', 'to', 'of',
            'in', 'on', 'at', 'by', 'is', 'are', 'was', 'were', 'be', 'been',
            'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'shall',
            'can', 'could', 'may', 'might', 'must', 'this', 'that', 'these',
            'those', 'which', 'who', 'what', 'where', 'when', 'why', 'how',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'not', 'only', 'own', 'same', 'so', 'than',
            'too', 'very', 'just', 'now', 'then', 'here', 'there', 'out', 'up',
            'down', 'off', 'over', 'under', 'again', 'further', 'once', 'new',
            'about', 'after', 'also', 'an', 'any', 'because', 'before', 'being',
            'between', 'both', 'during', 'each', 'even', 'first', 'get', 'give',
            'into', 'it', 'its', 'make', 'many', 'me', 'my', 'our', 'out',
            'said', 'see', 'she', 'should', 'since', 'some', 'take', 'than',
            'their', 'them', 'then', 'there', 'these', 'they', 'through', 'two',
            'us', 'use', 'want', 'way', 'we', 'well', 'were', 'what', 'while',
            'who', 'will', 'work', 'would', 'year', 'you', 'your',
        }

        filtered = set()
        removed_list = []
        for entity in entities:
            # Check if single word and common
            words = entity.split()
            if len(words) == 1 and entity.lower() in common_words:
                removed_list.append(entity)
                continue  # Skip single common words
            filtered.add(entity)

        removed = entities - filtered
        if self.verbose:
            print(f"\nRemoved {len(removed)} common words")
            if removed:
                print(f"Examples: {', '.join(sorted(removed)[:20])}")

        self.print_wave_results(filtered, sample_size=30)
        self.results['wave2_no_common'] = filtered
        return filtered

    def wave3_remove_domain_words(self, entities: Set[str]) -> Set[str]:
        """
        WAVE 3: Remove legislative/domain-specific common words

        Strategy: Filter out words specific to legislative transcripts
        Examples: "Committee", "Chairman", "Representative" (standalone), etc.
        """
        self.print_wave_header(3, "Remove Domain-Specific Common Words")

        # Legislative and procedural terms (lowercase for case-insensitive matching)
        domain_words = {
            # Procedural
            'committee', 'chairman', 'chairwoman', 'chair', 'vice',
            'member', 'members', 'meeting', 'session', 'hearing',
            'testimony', 'testify', 'witness', 'amendment', 'motion',
            'vote', 'votes', 'voting', 'pass', 'passed', 'fail', 'failed',
            'approve', 'approved', 'adopt', 'adopted', 'reject', 'rejected',
            'bill', 'bills', 'resolution', 'legislation', 'statute',
            'section', 'subsection', 'paragraph', 'page', 'line',
            # Titles when standalone (we'll extract "Representative X" in Wave 4)
            'representative', 'senator', 'mister', 'doctor', 'professor',
            'reverend', 'secretary', 'governor', 'mayor', 'director',
            # Time/place
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'saturday', 'sunday', 'january', 'february', 'march', 'april',
            'may', 'june', 'july', 'august', 'september', 'october',
            'november', 'december', 'morning', 'afternoon', 'evening',
            'today', 'yesterday', 'tomorrow',
            # Common transcript artifacts
            'inaudible', 'indiscernible', 'crosstalk', 'applause',
            'laughter', 'pause', 'break', 'recess', 'adjourn', 'adjourned',
            # Misc
            'thank', 'thanks', 'please', 'sorry', 'excuse', 'question',
            'questions', 'answer', 'answers', 'comment', 'comments',
            'statement', 'statements', 'record', 'minutes',
            # Numbers spelled out
            'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
            'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
            'twenty', 'thirty', 'forty', 'fifty', 'hundred', 'thousand',
            # Common legislative phrases
            'house', 'senate', 'floor', 'chamber', 'quorum', 'present',
            # Pronouns (these get extracted as "names" but aren't)
            'he', 'she', 'him', 'her', 'his', 'hers', 'them', 'their',
            'we', 'us', 'our', 'ours', 'i', 'me', 'my', 'mine',
            # Common words that slip through
            'yes', 'no', 'yeah', 'yep', 'nope', 'okay', 'ok',
            'if', 'when', 'while', 'until', 'unless',
            'because', 'since', 'although', 'though', 'however',
            'therefore', 'thus', 'hence', 'meanwhile', 'otherwise',
            'also', 'too', 'either', 'neither', 'both',
            'new', 'old', 'next', 'last', 'first', 'second',
            'same', 'different', 'other', 'another', 'each', 'every',
            'said', 'says', 'saying', 'told', 'asked', 'asked',
            'made', 'make', 'makes', 'making',
            'ready', 'done', 'finished', 'complete',
            'speaker', 'designate', 'ranking',
        }

        filtered = set()
        for entity in entities:
            # Check if entire entity or any word is a domain word (case-insensitive)
            words = entity.split()
            if any(word.lower() in domain_words for word in words):
                continue
            filtered.add(entity)

        removed = entities - filtered
        if self.verbose:
            print(f"\nRemoved {len(removed)} domain-specific words")
            if removed:
                print(f"Examples: {', '.join(sorted(removed)[:15])}")

        self.print_wave_results(filtered, sample_size=30)
        self.results['wave3_no_domain'] = filtered
        return filtered

    def wave4_title_based_extraction(self) -> Dict[str, int]:
        """
        WAVE 4: Extract names following titles

        Strategy: Look for patterns like "Representative [Name]" or "Senator [Name]"
        This is more precise than general capitalized word extraction.

        No word count limit - captures compound names, full names, etc.
        Examples: "Representative Chatfield", "Representative Roybal Caballero",
                  "Dr. Mary Garcia-Smith"
        """
        self.print_wave_header(4, "Title-Based Name Extraction")

        # Titles that precede names (case-insensitive)
        titles = [
            'Representative', 'Rep', 'Senator', 'Sen',
            'Chairman', 'Chairwoman', 'Chair',
            'Mr', 'Ms', 'Mrs', 'Miss', 'Dr', 'Doctor',
            'Governor', 'Secretary', 'Director', 'Commissioner',
        ]

        # Build pattern: (TITLE) (NAME)
        # Name can be multiple words (1-4 for safety) but capture generously
        # Match both Title Case and lowercase (due to OCR errors)
        title_pattern = '|'.join(re.escape(title) for title in titles)

        # Match: Title + 1 to 4 words
        # Allow hyphens and apostrophes within names (O'Brien, Garcia-Smith)
        # Allow both uppercase and lowercase starts (OCR errors: "representative brown")
        # Max 4 words balances capturing full names vs. capturing too much context
        pattern = rf'\b(?:{title_pattern})\s+([A-Za-z][a-z]+(?:[\s\-\'][A-Za-z][a-z]+){{0,3}})\b'

        matches = re.findall(pattern, self.text, re.IGNORECASE)

        # Count frequencies (normalize to title case for consistency)
        # Also clean up extra whitespace
        name_counts = Counter(
            ' '.join(word.title() for word in match.split())
            for match in matches
            if match.strip()
        )

        if self.verbose:
            print(f"\nFound {len(name_counts)} unique names after titles")
            print("\nTop 30 by frequency:")
            for i, (name, count) in enumerate(name_counts.most_common(30), 1):
                print(f"  {i:3d}. {name:30s} ({count} mentions)")

        self.results['wave4_titled_names'] = name_counts
        return name_counts

    def wave5_frequency_filter(self, name_counts: Dict[str, int], min_freq: int = 3) -> Dict[str, int]:
        """
        WAVE 5: Filter by frequency

        Strategy: Only keep names that appear multiple times
        Single mentions are often OCR errors or misidentifications
        """
        self.print_wave_header(5, f"Frequency Filtering (min={min_freq} mentions)")

        filtered = {name: count for name, count in name_counts.items()
                   if count >= min_freq}

        removed = len(name_counts) - len(filtered)
        if self.verbose:
            print(f"\nRemoved {removed} names with fewer than {min_freq} mentions")
            print(f"Kept {len(filtered)} names")
            print("\nRemaining names:")
            for i, (name, count) in enumerate(sorted(filtered.items(),
                                                     key=lambda x: x[1],
                                                     reverse=True)[:20], 1):
                print(f"  {i:3d}. {name} ({count} mentions)")

        self.results['wave5_frequent'] = filtered
        return filtered

    def wave6_validation_filters(self, name_counts: Dict[str, int]) -> Dict[str, int]:
        """
        WAVE 6: Apply validation filters

        Strategy: Apply multiple validation checks to reject likely errors:
        - Must contain at least one vowel (reject OCR garbage like "XZQRT")
        - Must be reasonable length (2-50 chars)
        - Must not be all single character (reject "A B C")
        - Must not match blacklist patterns
        - Must not be common phrases ("Thank You", "Of The", etc.)
        - Must not contain common conjunctions/prepositions
        """
        self.print_wave_header(6, "Validation Filters")

        # Common phrases that aren't names
        phrase_blacklist = {
            'thank you', 'of the', 'to the', 'in the', 'on the', 'at the',
            'for the', 'and the', 'from the', 'with the', 'by the',
            'mr chair', 'madam chair', 'mr chairman', 'madam chairman',
            'chair thank you', 'chairman thank you', 'mr thank',
            'chair members', 'chairman members', 'chair members of',
            'chairman members of', 'chairman thank you very',
            'as you', 'you can', 'you have', 'you recall',
        }

        # Title words that shouldn't appear WITHIN the captured name
        # (It's ok for them to precede the name, but not be part of it)
        title_words_blacklist = {
            'chairman', 'chairwoman', 'chair', 'representative', 'senator',
            'governor', 'secretary', 'director', 'commissioner',
            'mister', 'mr', 'ms', 'mrs', 'miss', 'madam', 'dr', 'doctor',
        }

        # Words that shouldn't appear at end of a name
        end_blacklist = {
            'and', 'or', 'the', 'of', 'to', 'in', 'on', 'at', 'by', 'for',
            'with', 'from', 'thank', 'members', 'representative', 'chair',
            'chairman', 'committee',
            # Single-word context markers that appear after names
            'up', 'down', 'out', 'off', 'as', 'said', 'asked', 'did',
            'was', 'were', 'is', 'are', 'has', 'had', 'have',
        }

        # Words that shouldn't appear at start of a name (after title)
        start_blacklist = {
            'thank', 'and', 'or', 'the', 'of', 'to', 'that', 'this', 'they',
            'it', 'is', 'are', 'was', 'were', 'can', 'will', 'would',
        }

        filtered = {}
        rejected = defaultdict(list)

        for name, count in name_counts.items():
            name_lower = name.lower().strip()
            words = name.split()
            words_lower = [w.lower() for w in words]

            # Check 1: Must contain vowel
            if not re.search(r'[AEIOU]', name, re.IGNORECASE):
                rejected['no_vowel'].append(name)
                continue

            # Check 2: Length check
            if len(name) < 2 or len(name) > 50:
                rejected['bad_length'].append(name)
                continue

            # Check 3: Not all single letters
            if all(len(word) == 1 for word in words):
                rejected['single_letters'].append(name)
                continue

            # Check 4: Common phrase blacklist
            if name_lower in phrase_blacklist:
                rejected['common_phrase'].append(name)
                continue

            # Check 4b: Single-word names that are actually common words/pronouns
            # Re-check against domain words for single-word names
            if len(words) == 1:
                # Import domain words from Wave 3 logic
                domain_blocklist = {
                    'he', 'she', 'him', 'her', 'his', 'hers', 'them', 'their',
                    'we', 'us', 'our', 'ours', 'i', 'me', 'my', 'mine',
                    'yes', 'no', 'yeah', 'yep', 'nope', 'okay', 'ok', 'so',
                    'if', 'when', 'while', 'until', 'unless', 'yesterday',
                    'today', 'tomorrow', 'new', 'old', 'next', 'last',
                    'said', 'says', 'asked', 'told', 'made', 'make',
                    'ready', 'done', 'speaker', 'designate', 'ranking',
                    'but', 'there', 'here', 'hi', 'hello', 'hey',
                    'good', 'great', 'fine', 'well', 'very',
                }
                if name_lower in domain_blocklist:
                    rejected['common_word'].append(name)
                    continue

            # Check 4c: Contains title words within the name
            if any(title_word in words_lower for title_word in title_words_blacklist):
                rejected['contains_title'].append(name)
                continue

            # Check 5: Ends with blacklisted word or phrase
            if words and words[-1].lower() in end_blacklist:
                rejected['bad_ending'].append(name)
                continue

            # Check 5b: Ends with common two-word phrases like "Thank You"
            if len(words) >= 2:
                last_two = f"{words[-2]} {words[-1]}".lower()
                bad_endings_two_word = {
                    'thank you', 'so now', 'next we', 'please thank',
                    'you talked', 'you can', 'you have', 'you recall',
                    'that goes', 'will oversee', 'the establish'
                }
                if last_two in bad_endings_two_word:
                    rejected['bad_ending_phrase'].append(name)
                    continue

            # Check 5c: Ends with three-word phrases like "Are You Ready"
            if len(words) >= 3:
                last_three = f"{words[-3]} {words[-2]} {words[-1]}".lower()
                bad_endings_three_word = {
                    'are you ready', 'can you hear', 'do you want',
                    'did you want', 'would you like', 'if you will',
                    'if you could', 'thank you very', 'thank you madame',
                }
                if last_three in bad_endings_three_word:
                    rejected['bad_ending_phrase'].append(name)
                    continue

            # Check 6: Starts with blacklisted word
            if words and words[0].lower() in start_blacklist:
                rejected['bad_start'].append(name)
                continue

            # Check 7: Contains newline or other weird characters
            if '\n' in name or '\t' in name or '\r' in name:
                rejected['weird_chars'].append(name)
                continue

            # Check 8: All words are stop words (not a real name)
            stop_words = {
                'and', 'or', 'the', 'of', 'to', 'in', 'on', 'at', 'by',
                'for', 'with', 'from', 'that', 'this'
            }
            if all(word.lower() in stop_words for word in words):
                rejected['all_stop_words'].append(name)
                continue

            # Check 9: Traditional name pattern - at least one word should look like a name
            # (start with capital, have mix of vowels/consonants, length > 2)
            # Be permissive: allow multi-word names, just ensure at least ONE word looks name-like
            has_name_like_word = False
            name_like_count = 0
            for word in words:
                # Skip very short words, apostrophes, hyphens (O', -Smith)
                clean_word = word.strip("'-")
                if not clean_word or len(clean_word) < 2:
                    continue

                if (word[0].isupper() and
                    re.search(r'[aeiou]', clean_word, re.IGNORECASE) and
                    clean_word.lower() not in stop_words and
                    clean_word.lower() not in start_blacklist and
                    clean_word.lower() not in end_blacklist):
                    name_like_count += 1
                    has_name_like_word = True

            # Must have at least one name-like word (be permissive about multi-word names)
            if not has_name_like_word:
                rejected['no_name_pattern'].append(name)
                continue

            filtered[name] = count

        if self.verbose:
            total_removed = sum(len(names) for names in rejected.values())
            print(f"\nRemoved {total_removed} names that failed validation:")
            for reason, names in rejected.items():
                if names:
                    print(f"  {reason}: {len(names)} names")
                    print(f"    Examples: {', '.join(names[:5])}")

            print(f"\nKept {len(filtered)} validated names")
            if filtered:
                print("\nValidated names (sorted by frequency):")
                for i, (name, count) in enumerate(sorted(filtered.items(),
                                                         key=lambda x: x[1],
                                                         reverse=True), 1):
                    print(f"  {i:3d}. {name:30s} ({count} mentions)")

        self.results['wave6_validated'] = filtered
        return filtered

    def wave7_normalization(self, name_counts: Dict[str, int]) -> Dict[str, Tuple[int, List[str]]]:
        """
        WAVE 7: Normalize and deduplicate similar names

        Strategy: Group names that are likely the same person
        - Handle OCR variations (MAESTAS vs MAESTRAS)
        - Group similar spellings
        - Return clusters with canonical form + variants
        """
        self.print_wave_header(7, "Normalization and Deduplication")

        # Simple normalization: group by similarity
        # For POC, we'll use basic string similarity
        clusters = {}

        for name, count in name_counts.items():
            # Find if this name is similar to any existing cluster
            matched = False
            for canonical in list(clusters.keys()):
                if self._names_similar(name, canonical):
                    # Add to existing cluster
                    clusters[canonical][0] += count  # Add to total count
                    clusters[canonical][1].append(name)  # Add as variant
                    matched = True
                    break

            if not matched:
                # Create new cluster
                clusters[name] = [count, [name]]

        if self.verbose:
            print(f"\nClustered {len(name_counts)} names into {len(clusters)} unique entities")
            print("\nFinal results (Top 20):")
            sorted_clusters = sorted(clusters.items(),
                                   key=lambda x: x[1][0],
                                   reverse=True)
            for i, (canonical, (total_count, variants)) in enumerate(sorted_clusters[:20], 1):
                print(f"  {i:3d}. {canonical} ({total_count} mentions)")
                if len(variants) > 1:
                    print(f"       Variants: {', '.join(v for v in variants if v != canonical)}")

        self.results['wave7_normalized'] = clusters
        return clusters

    def _names_similar(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """
        Check if two names are similar enough to be the same person

        Uses simple Levenshtein-like similarity for POC
        """
        # Same name
        if name1 == name2:
            return True

        # One is substring of other (e.g., "MAESTAS" and "MAESTAS BERGMAN")
        if name1 in name2 or name2 in name1:
            return True

        # Calculate simple similarity ratio
        longer = max(len(name1), len(name2))
        shorter = min(len(name1), len(name2))

        # If length difference is too large, not similar
        if shorter / longer < 0.7:
            return False

        # Count matching characters in same positions
        matches = sum(c1 == c2 for c1, c2 in zip(name1, name2))
        similarity = matches / longer

        return similarity >= threshold

    def run_all_waves(self, min_frequency: int = 3) -> Dict:
        """Run all waves in sequence and return final results"""

        print("\n" + "█"*70)
        print("  NAMED ENTITY RECOGNITION - PROGRESSIVE WAVE EXTRACTION")
        print("█"*70)
        print(f"\nProcessing {len(self.text)} characters of text...\n")

        # Wave 1: Get all capitalized sequences
        wave1_entities = self.wave1_extract_capitalized()

        # Wave 2: Remove common English words
        wave2_entities = self.wave2_remove_common_words(wave1_entities)

        # Wave 3: Remove domain-specific words
        wave3_entities = self.wave3_remove_domain_words(wave2_entities)

        # Wave 4: Title-based extraction (parallel approach)
        wave4_names = self.wave4_title_based_extraction()

        # Wave 5: Frequency filtering
        wave5_names = self.wave5_frequency_filter(wave4_names, min_frequency)

        # Wave 6: Validation
        wave6_names = self.wave6_validation_filters(wave5_names)

        # Wave 7: Normalization
        wave7_clusters = self.wave7_normalization(wave6_names)

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Wave 1 - Capitalized sequences:  {len(wave1_entities):4d}")
        print(f"Wave 2 - After common words:     {len(wave2_entities):4d}")
        print(f"Wave 3 - After domain words:     {len(wave3_entities):4d}")
        print(f"Wave 4 - Title-based names:      {len(wave4_names):4d}")
        print(f"Wave 5 - Frequent names (≥{min_frequency}):     {len(wave5_names):4d}")
        print(f"Wave 6 - Validated names:        {len(wave6_names):4d}")
        print(f"Wave 7 - Final unique entities:  {len(wave7_clusters):4d}")

        return self.results


def main():
    """Run POC on sample transcript files"""

    # Find some sample transcript files
    transcript_dirs = [
        'Appropriations and Finance',
        'Education',
        'Judiciary',
    ]

    sample_files = []
    for dir_name in transcript_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            txt_files = list(dir_path.glob('*.cc.txt'))[:2]  # Take 2 from each
            sample_files.extend(txt_files)

    if not sample_files:
        print("No transcript files found. Please run from repository root.")
        return

    print(f"Found {len(sample_files)} sample files to process")
    print("Files:")
    for f in sample_files:
        print(f"  - {f}")

    # Combine text from all sample files
    combined_text = []
    for file_path in sample_files[:3]:  # Process first 3 for POC
        print(f"\nReading: {file_path}")
        text = file_path.read_text(encoding='utf-8', errors='ignore')
        combined_text.append(text)

    full_text = '\n\n'.join(combined_text)

    # Run wave extraction
    extractor = WaveExtractor(full_text, verbose=True)
    results = extractor.run_all_waves(min_frequency=2)

    # Save results
    output_file = 'ner_poc_results.json'
    with open(output_file, 'w') as f:
        # Convert sets to lists for JSON serialization
        json_results = {}
        for key, value in results.items():
            if isinstance(value, set):
                json_results[key] = sorted(list(value))
            elif isinstance(value, dict):
                if key == 'wave7_normalized':
                    # Special handling for clusters
                    json_results[key] = {
                        name: {'count': count, 'variants': variants}
                        for name, (count, variants) in value.items()
                    }
                else:
                    json_results[key] = value
            else:
                json_results[key] = value

        json.dump(json_results, f, indent=2)

    print(f"\n\nResults saved to: {output_file}")


if __name__ == '__main__':
    main()
