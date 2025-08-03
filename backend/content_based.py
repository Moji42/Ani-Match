# backend/content_based.py
import os
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches  # For fuzzy matching
import logging
# Constants (adjustable weights)
GENRE_WEIGHT = 0.5
RATING_WEIGHT = 0.3
POPULARITY_WEIGHT = 0.2
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) 
def load_and_preprocess_data(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at: {os.path.abspath(filepath)}")

    df = (
        pd.read_csv(filepath)
        .assign(name=lambda x: x['name'].str.replace('&#039;', "'"))
        .pipe(lambda df: df[~df['genre'].isna()].copy())
        .assign(genre=lambda x: x['genre'].str.split(', '))
    )

    # Encode genres
    mlb = MultiLabelBinarizer()
    genre_features = mlb.fit_transform(df['genre'])
    genre_df = pd.DataFrame(genre_features, columns=mlb.classes_)

    # Handle missing ratings
    df['rating'] = df['rating'].fillna(df['rating'].median())

    # Normalize features
    def normalize(series):
        range_val = series.max() - series.min()
        return (series - series.min()) / range_val if range_val != 0 else 0.5

    df = df.assign(
        rating_normalized=normalize(df['rating']),
        members_normalized=normalize(df['members'])
    )

    # Weighted features
    final_features = pd.concat([
        genre_df * GENRE_WEIGHT,
        df['rating_normalized'].to_frame() * RATING_WEIGHT,
        df['members_normalized'].to_frame() * POPULARITY_WEIGHT
    ], axis=1).fillna(0)



    return df, final_features

def build_similarity_matrix(features):
    return cosine_similarity(features)

def clean_title(title):
    return (title.lower()
            .replace(':', '')
            .replace('-', ' ')
            .replace('!', '')
            .strip())

# Enhanced get_recommendations
def get_recommendations(title, df, similarity_matrix, n=5):
    if not isinstance(title, str) or len(title.strip()) < 2:
        logger.warning("Invalid title input")
        return pd.DataFrame()
    
    if not isinstance(n, int) or n < 1:
        n = 5
    
    
    try:
        cleaned_title = clean_title(title)
        
        # Exact match with cleaned title
        exact_match = df[df['name'].apply(clean_title) == cleaned_title]
        if not exact_match.empty:
            idx = exact_match.index[0]
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
                return pd.DataFrame()
            idx = df[df['name'].apply(clean_title) == matches[0]].index[0]
        
        # Get more candidates for diversity
        sim_scores = list(enumerate(similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:(n*3)+1]  # Get 3x candidates
        
        # Select top N most similar while ensuring some diversity
        selected = []
        seen_genres = set()
        
        for i, score in sim_scores:
            if len(selected) >= n:
                break
            current_genres = set(df.iloc[i]['genre'])
            
            # If we have space or this anime adds new genres
            if len(selected) < n//2 or not current_genres.issubset(seen_genres):
                selected.append((i, score))
                seen_genres.update(current_genres)
        
        # If we didn't get enough, fill with remaining top matches
        if len(selected) < n:
            remaining = [x for x in sim_scores if x[0] not in [s[0] for s in selected]]
            selected.extend(remaining[:n-len(selected)])
        
        return pd.DataFrame({
            'Anime': df.iloc[[i[0] for i in selected]]['name'].values,
            'Similarity Score': [f"{i[1]:.2f}" for i in selected],
            'Rating': df.iloc[[i[0] for i in selected]]['rating'].values,
            'Genres': df.iloc[[i[0] for i in selected]]['genre'].apply(lambda x: ', '.join(x)),
            'Content_Score': [i[1] for i in selected]  # Add raw score for hybrid
        })
    
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), '../data/anime_clean.csv')
    df, features = load_and_preprocess_data(data_path)
    similarity_matrix = build_similarity_matrix(features)
    
    # Test cases
    print("Test Recommendations:")
    print(get_recommendations('Naruto', df, similarity_matrix))  # Exact match
    print(get_recommendations('Narut', df, similarity_matrix))   # Fuzzy match
    print(get_recommendations('Unknown Anime', df, similarity_matrix))  # No match