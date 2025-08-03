import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import os
import pickle

def train_collab_model(ratings_path):

    # Loads the ratings data (Expected format is : user_id, anime_id, rating)
    ratings_df = pd.read_csv(ratings_path)

    # Loads data for the suprise library
    reader = Reader(rating_scale=(1,10))
    data = Dataset.load_from_df(ratings_df[['user_id', 'anime_id', 'rating']], reader)

    # Train/test splits
    trainset  = data.build_full_trainset()

    # Training of the SVD Model ( matrix factorization)
    model = SVD(n_factors = 100, n_epochs = 20, lr_all=0.005, reg_all = 0.02)
    model.fit(trainset)

    return model

def save_model(model,filename = 'collab_model.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(model,f)

def load_model(model,filename = 'collab_model.pkl'):
    with open(filename, 'rb') as f:
        return pickle.load(f)