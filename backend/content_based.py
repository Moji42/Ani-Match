import os
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches  # For fuzzy matching

# Constants (adjustable weights)
GENRE_WEIGHT = 0.7
RATING_WEIGHT = 0.2
POPULARITY_WEIGHT = 0.1

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

def get_recommendations(title, df, similarity_matrix, n=5):
    try:
        # Exact match
        exact_match = df[df['name'].str.lower() == title.lower()]
        if not exact_match.empty:
            idx = exact_match.index[0]
        else:
            # Fuzzy match (top 1 closest name)
            matches = get_close_matches(title, df['name'].tolist(), n=1, cutoff=0.6)
            if not matches:
                print(f"No matches found for '{title}'")
                return pd.DataFrame()
            idx = df[df['name'] == matches[0]].index[0]

        # Get top-N similar items
        sim_scores = list(enumerate(similarity_matrix[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:n+1]
        
        return pd.DataFrame({
            'Anime': df.iloc[[i[0] for i in sim_scores]]['name'].values,
            'Similarity Score': [f"{i[1]:.2f}" for i in sim_scores],
            'Rating': df.iloc[[i[0] for i in sim_scores]]['rating'].values,
            'Genres': df.iloc[[i[0] for i in sim_scores]]['genre'].apply(lambda x: ', '.join(x))
        })

    except KeyError as e:
        print(f"Column missing in dataframe: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {e}")
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