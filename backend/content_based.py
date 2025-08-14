# backend/content_based.py
import os
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches
import logging
import ast
from typing import Tuple, Union

# Constants (adjustable weights)
GENRE_WEIGHT = 0.5
RATING_WEIGHT = 0.3
POPULARITY_WEIGHT = 0.2

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_and_preprocess_data(filepath: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load and preprocess anime data for content-based recommendations.
    
    Args:
        filepath: Path to the anime dataset CSV file
        
    Returns:
        Tuple of (processed DataFrame, feature matrix)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at: {os.path.abspath(filepath)}")

    try:
        # Load and clean data
        df = (
            pd.read_csv(filepath)
            .assign(name=lambda x: x['name'].str.replace('&#039;', "'"))
            .pipe(lambda df: df[~df['genre'].isna()].copy())
        )

        # Convert genre strings to lists safely
        df['genre'] = df['genre'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )

        # Encode genres
        mlb = MultiLabelBinarizer()
        genre_features = mlb.fit_transform(df['genre'])
        genre_df = pd.DataFrame(genre_features, columns=mlb.classes_)

        # Handle missing ratings
        df['rating'] = df['rating'].fillna(df['rating'].median())

        # Normalize features
        def normalize(series: pd.Series) -> pd.Series:
            range_val = series.max() - series.min()
            return (series - series.min()) / range_val if range_val != 0 else 0.5

        df = df.assign(
            rating_normalized=normalize(df['rating']),
            members_normalized=normalize(df['members'])
        )

        # Create weighted features
        final_features = pd.concat([
            genre_df * GENRE_WEIGHT,
            df['rating_normalized'].to_frame() * RATING_WEIGHT,
            df['members_normalized'].to_frame() * POPULARITY_WEIGHT
        ], axis=1).fillna(0)

        logger.info(f"Successfully loaded and preprocessed {len(df)} anime entries")
        return df, final_features

    except Exception as e:
        logger.error(f"Data loading failed: {str(e)}", exc_info=True)
        raise

def build_similarity_matrix(features: pd.DataFrame) -> pd.DataFrame:
    """Build cosine similarity matrix from features."""
    return cosine_similarity(features)

def clean_title(title: str) -> str:
    """Normalize anime titles for matching."""
    if not isinstance(title, str):
        raise ValueError("Title must be a string")
    
    return (title.lower()
            .replace(':', '')
            .replace('-', ' ')
            .replace('!', '')
            .strip())

def get_recommendations(
    title: str,
    df: pd.DataFrame,
    similarity_matrix: pd.DataFrame,
    n: int = 5
) -> Union[pd.DataFrame, None]:
    """Get content-based anime recommendations.
    
    Args:
        title: Anime title to find similar recommendations for
        df: Processed anime DataFrame
        similarity_matrix: Precomputed similarity matrix
        n: Number of recommendations to return
        
    Returns:
        DataFrame of recommendations or None if error occurs
    """
    # Validate inputs
    if not isinstance(title, str) or len(title.strip()) < 2:
        logger.warning(f"Invalid title input: {title}")
        return None
    
    if not isinstance(n, int) or n < 1:
        n = 5
        logger.info(f"Using default n={n}")
    
    try:
        cleaned_title = clean_title(title)
        
        # Find matching anime
        exact_match = df[df['name'].apply(clean_title) == cleaned_title]
        
        if not exact_match.empty:
            idx = exact_match.index[0]
            logger.debug(f"Found exact match for '{title}'")
        else:
            # Fuzzy match with threshold
            matches = get_close_matches(
                cleaned_title, 
                df['name'].apply(clean_title).tolist(), 
                n=3, 
                cutoff=0.7
            )
            
            if not matches:
                logger.warning(f"No matches found for '{title}'")
                return None
                
            idx = df[df['name'].apply(clean_title) == matches[0]].index[0]
            logger.debug(f"Using fuzzy match for '{title}': {matches[0]}")
        
        # Get similarity scores
        sim_scores = list(enumerate(similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:(n*3)+1]
        
        # Select diverse recommendations
        selected = []
        seen_genres = set()
        
        for i, score in sim_scores:
            if len(selected) >= n:
                break
                
            current_genres = set(df.iloc[i]['genre'])
            
            # Prioritize diversity
            if len(selected) < n//2 or not current_genres.issubset(seen_genres):
                selected.append((i, score))
                seen_genres.update(current_genres)
        
        # Fallback to top matches if needed
        if len(selected) < n:
            remaining = [x for x in sim_scores if x[0] not in [s[0] for s in selected]]
            selected.extend(remaining[:n-len(selected)])
            logger.debug(f"Added {len(remaining[:n-len(selected)])} fallback recommendations")
        
        # Format results
        recommendations = pd.DataFrame({
            'Anime': df.iloc[[i[0] for i in selected]]['name'].values,
            'Similarity Score': [round(i[1], 4) for i in selected],  # Rounded to 4 decimals
            'Rating': df.iloc[[i[0] for i in selected]]['rating'].values,
            'Genres': df.iloc[[i[0] for i in selected]]['genre'].values.tolist(),
            'Content_Score': [i[1] for i in selected]
        })
        
        logger.info(f"Generated {len(recommendations)} recommendations for '{title}'")
        return recommendations
        
    except Exception as e:
        logger.error(f"Recommendation failed for '{title}': {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    # Test the module
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    data_path = os.path.join(os.path.dirname(__file__), '../data/anime_clean.csv')
    try:
        df, features = load_and_preprocess_data(data_path)
        similarity_matrix = build_similarity_matrix(features)
        
        # Test cases
        test_titles = ['Naruto', 'Narut', 'Unknown Anime', 123]
        for title in test_titles:
            print(f"\nRecommendations for '{title}':")
            recs = get_recommendations(title, df, similarity_matrix)
            print(recs if recs is not None else "No recommendations found")
            
    except Exception as e:
        logger.error(f"Module test failed: {str(e)}", exc_info=True)