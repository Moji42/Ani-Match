# backend/content_based.py

import os
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches, SequenceMatcher
import logging
import ast
import re
from typing import Tuple, Union, Set

# ===================== CONSTANTS =======================
GENRE_WEIGHT = 0.5
RATING_WEIGHT = 0.3
POPULARITY_WEIGHT = 0.2

SERIES_SIMILARITY_THRESHOLD = 0.85
PERFECT_MATCH_THRESHOLD = 0.99

KNOWN_SERIES_FAMILIES = {
    'one piece': ['one piece', 'wan pisu'],
    'naruto': ['naruto', 'boruto', 'naruto shippuden', 'naruto shippuuden'],
    'dragon ball': ['dragon ball', 'dragonball', 'dragon ball z', 'dragon ball gt', 'dragon ball super'],
    'jojo': ['jojo', 'jojos bizarre adventure', 'jojo no kimyou na bouken'],
    'fate': ['fate', 'fate stay night', 'fate zero', 'fate grand order', 'fate apocrypha'],
    'fullmetal alchemist': ['fullmetal alchemist', 'hagane no renkinjutsushi', 'fullmetal alchemist brotherhood'],
    'attack on titan': ['attack on titan', 'shingeki no kyojin'],
    'hunter x hunter': ['hunter x hunter', 'hunter hunter'],
    'mobile suit gundam': ['gundam', 'mobile suit gundam', 'kidou senshi gundam'],
}

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ===================== HELPER FUNCTIONS =======================

def normalize(series: pd.Series) -> pd.Series:
    """Normalize a numeric column 0-1."""
    _range = series.max() - series.min()
    return (series - series.min()) / _range if _range != 0 else 0.5

def clean_title(title: str) -> str:
    if not isinstance(title, str): return ""
    return (title.lower()
           .replace(':','')
           .replace('-',' ')
           .replace('!','')
           .strip())

# Strip out seasons, parts, OVA, etc.
def extract_series_name(title: str) -> str:
    if not isinstance(title, str): return ""
    normalized = title.lower().strip()
    patterns = [
        r'\s*season\s*\d+.*$', r'\s*s\d+.*$', r'\s*\d+nd\s+season.*$', r'\s*\d+rd\s+season.*$',
        r'\s*\d+th\s+season.*$', r'\s*part\s*\d+.*$', r'\s*part\s*[ivx]+.*$', r'\s*ova.*$',
        r'\s*ona.*$', r'\s*special.*$', r'\s*movie.*$', r'\s*film.*$', r'\s*recap.*$',
        r'\s*shippuden.*$', r'\s*shippuuden.*$', r'\s*kai.*$', r'\s*brotherhood.*$',
        r'\s*boruto.*$', r'\s*:\s*.*$', r'\s*-\s*.*$', r'\s*\(\d+\).*$', r'\s*\[.*\].*$',
        r'\s*episode\s*\d+.*$', r'\s*ep\s*\d+.*$'
    ]
    for p in patterns:
        normalized = re.sub(p, '', normalized, flags=re.IGNORECASE)
    return ' '.join(normalized.split())

def get_series_family(series_name: str) -> str:
    if not series_name: return ""
    lower = series_name.lower()
    for fam, variants in KNOWN_SERIES_FAMILIES.items():
        for v in variants:
            if v in lower or lower in v:
                return fam
    return series_name

def are_same_series(title1: str, title2: str, threshold: float = SERIES_SIMILARITY_THRESHOLD) -> bool:
    """Check if two anime titles are from same series/family."""
    if not title1 or not title2:
        return False
    name1 = extract_series_name(title1)
    name2 = extract_series_name(title2)
    if not name1 or not name2:
        return False
    if get_series_family(name1) == get_series_family(name2):
        return True
    if name1 == name2:
        return True
    sim = SequenceMatcher(None, name1, name2).ratio()
    contains = (name1 in name2) or (name2 in name1)
    return sim >= threshold or contains

# Optional: allow filtering by type
def filter_by_type(df_subset, anime_type):
    """Filter anime DataFrame by type(s)"""
    if not anime_type or anime_type.lower() == 'all':
        return df_subset
    
    # Handle multiple types (comma-separated)
    if isinstance(anime_type, str):
        types = [t.strip().lower() for t in anime_type.split(',')]
    else:
        types = [str(anime_type).lower()]
    
    # Create a boolean mask for filtering
    if 'type' not in df_subset.columns:
        logger.warning("No 'type' column found in DataFrame, cannot filter by type")
        return df_subset
    
    mask = df_subset['type'].str.lower().isin(types)
    filtered_df = df_subset[mask]
    
    logger.info(f"Filtered from {len(df_subset)} to {len(filtered_df)} anime for types: {types}")
    return filtered_df


# ===================== CORE FUNCTIONS =======================

def load_and_preprocess_data(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load data, make genre multi-hot, normalize rating + members, build weighted feature matrix.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    df = (
        pd.read_csv(filepath)
        .assign(name=lambda d: d['name'].str.replace('&#039;', "'"))
        .pipe(lambda d: d[~d['genre'].isna()].copy())
    )

    # convert genre column (list stored as string) to list
    df['genre'] = df['genre'].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    mlb = MultiLabelBinarizer()
    genre_features = mlb.fit_transform(df['genre'])
    genre_df = pd.DataFrame(genre_features, columns=mlb.classes_)

    df['rating']  = df['rating'].fillna(df['rating'].median())
    df['members'] = df['members'].fillna(df['members'].median())

    df['rating_normalized']  = normalize(df['rating'])
    df['members_normalized'] = normalize(df['members'])

    final_features = pd.concat([
        genre_df * GENRE_WEIGHT,
        df['rating_normalized'] * RATING_WEIGHT,
        df['members_normalized'] * POPULARITY_WEIGHT
    ], axis=1).fillna(0)

    logger.info(f"Loaded & preprocessed {len(df)} anime.")
    return df, final_features

def build_similarity_matrix(features: pd.DataFrame):
    return cosine_similarity(features)

# backend/content_based.py
def get_recommendations(
    title: str,
    df: pd.DataFrame,
    similarity_matrix,
    n: int = 5,
    anime_type: str = None
) -> Union[pd.DataFrame, None]:
    """
    Content-based top-N recommendations with diversity and series filtering.
    """
    if not title or len(title.strip()) < 2:
        logger.warning("Invalid title input")
        return None

    cleaned = clean_title(title)
    exact_match = df[df['name'].apply(clean_title) == cleaned]

    if not exact_match.empty:
        idx = exact_match.index[0]
    else:
        matches = get_close_matches(
            cleaned, df['name'].apply(clean_title).tolist(), n=3, cutoff=0.7
        )
        if not matches:
            logger.warning(f"No matches found for '{title}'")
            return None
        idx = df[df['name'].apply(clean_title) == matches[0]].index[0]

    # Get similarity list excluding itself
    sim_scores = list(enumerate(similarity_matrix[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:(n*3)+1]

    # Filter out same series
    sim_scores_filtered = [
        (i, score) for (i, score) in sim_scores
        if not are_same_series(df.iloc[i]['name'], df.iloc[idx]['name'])
    ]

    # Diverse genres
    selected = []
    seen_genres = set()
    for (i, score) in sim_scores_filtered:
        if len(selected) >= n: break
        curr_gen = set(df.iloc[i]['genre'])
        if len(selected) < n//2 or not curr_gen.issubset(seen_genres):
            selected.append((i, score))
            seen_genres.update(curr_gen)

    # Fallback if not enough
    if len(selected) < n:
        for (i, score) in sim_scores_filtered:
            if len(selected) >= n: break
            if i not in [s[0] for s in selected]:
                selected.append((i,score))

    recommendations = pd.DataFrame({
        'Anime': df.iloc[[i for (i, s) in selected]]['name'].values,
        'Similarity Score': [round(s, 4) for (_, s) in selected],
        'Rating': df.iloc[[i for (i, s) in selected]]['rating'].values,
        'Genres': df.iloc[[i for (i, s) in selected]]['genre'].tolist(),
        'Content_Score': [s for (_, s) in selected],
        'Type': df.iloc[[i for (i, s) in selected]]['type'].values  # Add type column
    })

    # Apply type filtering after creating recommendations
    if anime_type and anime_type.lower() != 'all':
        recommendations = filter_by_type(recommendations, anime_type)
        logger.info(f"After type filtering: {len(recommendations)} recommendations")

    return recommendations

