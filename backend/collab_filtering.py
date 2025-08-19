# backend/ collab_filtering.py
import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
import os
import pickle
from surprise import accuracy
from surprise.model_selection import cross_validate

import logging 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) 


def train_collab_model(ratings_path):
    # Load data
    ratings_df = pd.read_csv(ratings_path)
    
    # Sample data if too large
    if len(ratings_df) > 1000000:
        ratings_df = ratings_df.sample(1000000, random_state=42)
    
    # Train/test split
    reader = Reader(rating_scale=(1, 10))
    data = Dataset.load_from_df(ratings_df[['user_id', 'anime_id', 'rating']], reader)
    
    # Cross-validation
    cv_results = cross_validate(
        SVD(n_factors=50, n_epochs=20, lr_all=0.003, reg_all=0.05),
        data,
        measures=['RMSE', 'MAE'],
        cv=3,
        verbose=True
    )
    
    # Final training
    trainset = data.build_full_trainset()
    model = SVD(
        n_factors=50,
        n_epochs=20,
        lr_all=0.003,
        reg_all=0.05,
        random_state=42
    )
    model.fit(trainset)
    
    return model

def save_model(model,filename = 'collab_model.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(model,f)

def load_model(filename='collab_model.pkl'):
    try:
        with open(filename, 'rb') as f:
            model = pickle.load(f)
            if not hasattr(model, 'predict'):
                raise AttributeError("Model missing predict method")
            return model
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return None