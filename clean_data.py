# data_cleaning.py
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
import os

def get_data_path(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)

def clean_genres(genre_str):
    if pd.isna(genre_str):
        return []
    try:
        genres = [g.strip() for g in str(genre_str).split(',')]
        return [g for g in genres if g and g.lower() != 'unknown']
    except Exception as e:
        print(f"Error cleaning genres: {e}")
        return []

def clean_anime_data():
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(get_data_path('')), exist_ok=True)
        
        # Load and clean data
        anime_df = pd.read_csv(get_data_path('anime.csv'))
        
        anime_df = anime_df.assign(
            name=lambda x: x['name'].str.replace('&#039;', "'"),
            genre=lambda x: x['genre'].apply(clean_genres)
        ).pipe(lambda df: df[df['genre'].apply(len) > 0])  # Remove anime with no genres
        
        # Encode genres
        mlb = MultiLabelBinarizer()
        genre_encoded = pd.DataFrame(
            mlb.fit_transform(anime_df['genre']),
            columns=[f"genre_{g}" for g in mlb.classes_],
            index=anime_df.index
        )
        
        # Save cleaned data
        anime_clean = pd.concat([anime_df, genre_encoded], axis=1)
        anime_clean.to_csv(get_data_path('anime_clean.csv'), index=False)
        print(f"Saved cleaned anime data with {len(anime_clean)} entries")
        return anime_clean
        
    except Exception as e:
        print(f"Error in clean_anime_data: {str(e)}")
        return None

def clean_ratings_data():
    try:
        ratings = pd.read_csv(get_data_path('rating.csv'))
        
        ratings_clean = (
            ratings
            .query('rating > 0')  # Remove negative ratings
            .assign(
                rating=lambda x: x['rating'].clip(3, 9),  # Cap ratings
                user_id=lambda x: x.groupby('user_id').ngroup() + 1  # Normalize IDs
            )
            .drop_duplicates(['user_id', 'anime_id'])  # Remove duplicates
        )
        
        ratings_clean.to_csv(get_data_path('clean_ratings.csv'), index=False)
        print(f"Saved cleaned ratings with {len(ratings_clean)} entries")
        return ratings_clean
        
    except Exception as e:
        print(f"Error in clean_ratings_data: {str(e)}")
        return None

if __name__ == '__main__':
    print("Starting data cleaning...")
    anime_data = clean_anime_data()
    ratings_data = clean_ratings_data()
    
    if anime_data is not None and ratings_data is not None:
        print("Data cleaning completed successfully!")
    else:
        print("Data cleaning completed with errors")