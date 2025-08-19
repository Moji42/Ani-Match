# backend/filtering_config.py
"""
Configuration settings for anime recommendation filtering.
Adjust these values to fine-tune the same-series filtering behavior.
"""

# Similarity thresholds
SERIES_SIMILARITY_THRESHOLD = 0.85  # How similar titles need to be to consider same series (0.0-1.0)
PERFECT_MATCH_THRESHOLD = 0.99      # Threshold for filtering perfect similarity matches (0.0-1.0)

# Series detection patterns - add more patterns as needed
SERIES_PATTERNS = {
    # Season indicators
    'seasons': [
        r'\s*season\s*\d+.*$',
        r'\s*s\d+.*$', 
        r'\s*\d+nd\s+season.*$',
        r'\s*\d+rd\s+season.*$',
        r'\s*\d+th\s+season.*$',
        r'\s*second\s+season.*$',
        r'\s*third\s+season.*$',
        r'\s*final\s+season.*$',
        r'\s*first\s+season.*$',
    ],
    
    # Part indicators  
    'parts': [
        r'\s*part\s*\d+.*$',
        r'\s*part\s*[ivx]+.*$',
        r'\s*cour\s*\d+.*$',
        r'\s*arc\s*\d+.*$',
    ],
    
    # Special editions
    'specials': [
        r'\s*ova.*$',
        r'\s*ona.*$', 
        r'\s*special.*$',
        r'\s*movie.*$',
        r'\s*film.*$',
        r'\s*recap.*$',
        r'\s*extra.*$',
        r'\s*bonus.*$',
        r'\s*omake.*$',
    ],
    
    # Sequel indicators (specific to certain series)
    'sequels': [
        r'\s*shippuden.*$',
        r'\s*shippuuden.*$',
        r'\s*kai.*$',
        r'\s*brotherhood.*$',
        r'\s*revolution.*$',
        r'\s*evolution.*$',
        r'\s*next\s+generations.*$',
        r'\s*boruto.*$',
        r'\s*gt.*$',
        r'\s*super.*$',
        r'\s*zero.*$',
        r'\s*origin.*$',
        r'\s*prequel.*$',
    ],
    
    # General suffixes
    'general': [
        r'\s*:\s*.*$',      # Remove everything after colon
        r'\s*-\s*.*$',      # Remove everything after dash  
        r'\s*\(\d+\).*$',   # Remove year in parentheses
        r'\s*\[.*\].*$',    # Remove brackets
        r'\s*episode\s*\d+.*$',
        r'\s*ep\s*\d+.*$',
        r'\s*\d+\s*-\s*\d+.*$',
        r'\s*vol\.\s*\d+.*$',
        r'\s*volume\s*\d+.*$',
    ]
}

# Known series mappings (manual overrides)
# Use this for series that are hard to detect automatically
KNOWN_SERIES_MAPPINGS = {
    'naruto': ['naruto', 'naruto shippuden', 'naruto shippuuden', 'boruto', 'boruto naruto next generations'],
    'dragon ball': ['dragon ball', 'dragon ball z', 'dragon ball gt', 'dragon ball super', 'dragon ball kai'],
    'jojo': ['jojos bizarre adventure', 'jojo no kimyou na bouken', 'jojo'],
    'fate': ['fate stay night', 'fate zero', 'fate grand order', 'fate apocrypha', 'fate extra', 'fate kaleid'],
    'fullmetal alchemist': ['fullmetal alchemist', 'fullmetal alchemist brotherhood', 'hagane no renkinjutsushi'],
    'hunter x hunter': ['hunter x hunter', 'hunter x hunter 2011'],
    'one piece': ['one piece', 'wan pisu'],
    'attack on titan': ['attack on titan', 'shingeki no kyojin'],
    'mobile suit gundam': ['gundam', 'mobile suit gundam', 'kidou senshi gundam'],
    'code geass': ['code geass', 'code geass hangyaku no lelouch'],
    'evangelion': ['neon genesis evangelion', 'evangelion', 'shin evangelion'],
    'bleach': ['bleach', 'bleach sennen kessen hen'],
    'pokemon': ['pokemon', 'pocket monsters'],
    'sailor moon': ['sailor moon', 'bishoujo senshi sailor moon'],
    'detective conan': ['detective conan', 'meitantei conan', 'case closed'],
}

# Diversity settings
MIN_GENRE_DIVERSITY_RATIO = 0.3  # Minimum ratio of recommendations with different genres
MAX_SAME_GENRE_RECOMMENDATIONS = 3  # Maximum recommendations from same primary genre
GENRE_DIVERSITY_BOOST = True  # Prioritize genre diversity in first half of recommendations

# Recommendation quality settings
MIN_SIMILARITY_THRESHOLD = 0.1  # Minimum similarity score to consider for recommendations
QUALITY_SCORE_WEIGHT = 0.7      # Weight for similarity score in final ranking
DIVERSITY_SCORE_WEIGHT = 0.3    # Weight for diversity score in final ranking

# Filtering behavior settings
ENABLE_PERFECT_MATCH_FILTERING = True   # Filter out near-identical matches
ENABLE_SAME_SERIES_FILTERING = True     # Filter out same series recommendations
ENABLE_GENRE_DIVERSITY = True           # Enforce genre diversity
STRICT_SERIES_FILTERING = True          # Use strict series detection rules

# Search and matching settings
FUZZY_MATCH_CUTOFF = 0.7               # Minimum similarity for fuzzy title matching
MAX_FUZZY_MATCHES = 3                  # Maximum number of fuzzy matches to consider
CANDIDATE_POOL_MULTIPLIER = 6          # Multiplier for candidate pool size (n * multiplier)

# Debugging settings
ENABLE_FILTERING_LOGS = True    # Set to False to reduce log verbosity
LOG_FILTERED_TITLES = True      # Log which titles were filtered out
LOG_SERIES_DETECTION = True     # Log series detection results
LOG_DIVERSITY_CHOICES = True    # Log diversity selection reasoning

# Advanced filtering options
ENABLE_YEAR_DIVERSITY = False   # Consider release year for diversity (experimental)
ENABLE_STUDIO_DIVERSITY = False # Consider animation studio for diversity (experimental)
YEAR_DIVERSITY_THRESHOLD = 5    # Minimum year difference for year diversity

# Performance settings
MAX_PROCESSING_TIME = 30        # Maximum processing time in seconds
CACHE_SIMILARITY_MATRIX = True  # Cache similarity matrix for better performance
BATCH_SIZE = 1000              # Batch size for similarity calculations

# Quality assurance settings
MIN_RECOMMENDATIONS_THRESHOLD = 1  # Minimum recommendations to return (fallback mode)
FALLBACK_TO_POPULAR = True        # Fall back to popular anime if no recommendations found
ENABLE_QUALITY_CHECKS = True      # Enable additional quality validation

# Series family expansion rules
AUTO_EXPAND_SERIES_FAMILIES = True     # Automatically expand known series families
SIMILARITY_EXPANSION_THRESHOLD = 0.9   # Threshold for automatic series family expansion
MAX_SERIES_FAMILY_SIZE = 10           # Maximum size for automatically expanded families