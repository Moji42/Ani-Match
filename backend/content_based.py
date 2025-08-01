import os
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity

def load_and_preprocess_data(filepath):

    # Filepath verification
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset cannot be retrieved at: {os.path.abspath(filepath)}")

    # Will load and clean the data 
    df = pd.read_csv(filepath)

    df = (
        df
        
        .assign(name=lambda x: x['name'].str.replace('&#039;', "'")) # Clean anime names
       
        .pipe(lambda df: df[~df['genre'].isna()].copy())  # Remove rows with missing genres
        
        .assign(genre=lambda x: x['genre'].str.split(', ')) # Split genres into lists
    )
    
    # Starts to encode genres
    mlb = MultiLabelBinarizer()
    genre_features = mlb.fit_transform(df['genre'])
    genre_df = pd.DataFrame(genre_features, columns = mlb.classes_)

    # Handles the missing ratings to fill with a mean or median
    rating_mean = df['rating'].mean()
    df = df.assign(rating = lambda x: x['rating'].fillna(rating_mean))

    # Normalize ratings

    def safe_normalize(series):
        range_val = series.max() - series.min()
        if range_val == 0:
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - series.min()) / range_val
    
    df = df.assign(
        rating_normalized=lambda x: safe_normalize(x['rating']),
        members_normalized=lambda x: safe_normalize(x['members'])
    )
    
    # Appllying feature importance weights ( might change later )
    genre_weight = 0.7  # Genres are most important
    rating_weight = 0.2
    popularity_weight = 0.1
    
    final_features = pd.concat([
        genre_df * genre_weight,
        df['rating_normalized'].to_frame() * rating_weight,
        df['members_normalized'].to_frame() * popularity_weight
    ], axis=1)
    
    # Final validation
    if final_features.isnull().any().any():
        print("Warning: NaN values detected - filling with zeros")
        final_features = final_features.fillna(0)
    
    return df, final_features

def build_similarity_matrix(features):
    # Compute the cosine similarity 
    similarity_matrix = cosine_similarity(features)
    return similarity_matrix
    
def get_recommendations(title, df, similarity_matrix, n = 5):
   
    # Find the index of the anime
    idx = df.index[df['name'] == title].tolist()[0]

    # Get the similarity scores
    sim_scores = list(enumerate(similarity_matrix[idx]))

    # Will retrieve the top n recommendations besides itself
    sim_scores = sim_scores[1:n+1]
    anime_indices = [i[0] for i in sim_scores]

    # More flexible title matching
    matches = df['name'].str.contains(title, case =False, regex= False)
    if not matches.any():
        print(f"No anime found with '{title}' in title")
        return pd.Series([])
    
    idx = df.index[matches].tolist()[0]  # Take first match  

    recommendations = df['name'].iloc[anime_indices]
    scores = [score[1] for score in sim_scores] # Gathers the similarities scores

    return pd.DataFrame({'Anime': recommendations, 'Similarity Score': scores})

# This will be a test usage
if __name__ == "__main__":
    # Use this exact path format for Windows/WSL
    data_path = os.path.join(os.path.dirname(__file__), '../data/anime_clean.csv')
    df, features = load_and_preprocess_data(data_path)
    
    # Test with print to verify loading
    print("Data loaded successfully! First 5 entries:")
    print(df.head())
    
    similarity_matrix = build_similarity_matrix(features)
    recs = get_recommendations('Naruto', df, similarity_matrix)
    print("\nRecommendations for Naruto:")
    print(recs)