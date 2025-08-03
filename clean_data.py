import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

def clean_anime_data():
    # Load anime data
    anime_df = pd.read_csv('data/anime.csv')
    
    print("\nAnime Data Overview:")
    print(anime_df.head())
    print(anime_df.info())
    
    # Clean genres
    anime_df['genre'] = anime_df['genre'].fillna('Unknown')
    anime_df['genre'] = anime_df['genre'].str.split(', ')
    
    # Encode genres
    mlb = MultiLabelBinarizer()
    genre_encoded = pd.DataFrame(
        mlb.fit_transform(anime_df['genre']),
        columns=mlb.classes_,
        index=anime_df.index
    )
    
    # Merge with original data
    anime_clean = pd.concat([anime_df, genre_encoded], axis=1)
    
    # Save cleaned data
    anime_clean.to_csv('data/anime_clean.csv', index=False)
    print("\nSaved cleaned anime data to data/anime_clean.csv")
    return anime_clean

def clean_ratings_data():
    # Load ratings data
    ratings = pd.read_csv('data/rating.csv')
    
    print("\nOriginal Ratings Data Overview:")
    print(f"Total ratings: {len(ratings)}")
    print(f"Unique users: {ratings['user_id'].nunique()}")
    print(f"Unique anime: {ratings['anime_id'].nunique()}")
    
    # Clean ratings
    # Remove negative ratings and -1 values (typically indicate "not watched")
    ratings = ratings[ratings['rating'] > 0]
    
    # Cap maximum rating at 9 to prevent perfect scores from dominating
    ratings['rating'] = ratings['rating'].clip(upper=9)
    
    # Normalize user IDs to be sequential
    ratings['user_id'] = ratings.groupby('user_id').ngroup() + 1
    
    # Save cleaned data
    ratings.to_csv('data/clean_ratings.csv', index=False)
    print("\nSaved cleaned ratings data to data/clean_ratings.csv")
    
    # Print stats about cleaned data
    print("\nCleaned Ratings Stats:")
    print(f"Remaining ratings: {len(ratings)}")
    print(f"Rating distribution:\n{ratings['rating'].value_counts().sort_index()}")
    return ratings

if __name__ == '__main__':
    print("Starting data cleaning process...")
    anime_clean = clean_anime_data()
    ratings_clean = clean_ratings_data()
    print("\nData cleaning complete!")