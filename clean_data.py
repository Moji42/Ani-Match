from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
import pandas as pd

# Load the data
anime_df = pd.read_csv('data/anime.csv')
ratings_df = pd.read_csv('data/rating.csv')

# Exlpores the data
print(anime_df.head())
print(anime_df.info())

# cleans the genres
anime_df['genre'] = anime_df['genre'].fillna('Unknown')
anime_df['genre'] = anime_df['genre'].str.split(', ')

# We can now encode the genres
mlb = MultiLabelBinarizer()
genre_encoded = pd.DataFrame(mlb.fit_transform(anime_df['genre']), 
                            columns=mlb.classes_, 
                            index=anime_df.index)

# Save cleaned data
anime_clean = pd.concat([anime_df, genre_encoded], axis=1)
anime_clean.to_csv('anime_clean.csv', index=False)


