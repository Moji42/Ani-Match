# backend/app.py
from flask import Flask, request, jsonify
from content_based import load_and_preprocess_data, build_similarity_matrix, get_recommendations
import pandas as pd
from surprise import Dataset, Reader, SVD
import pickle
import os
import logging
from functools import lru_cache
from flask_caching import Cache

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure caching
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

# Configuration for model
CONFIG = {
    'content_weight': 0.6,  # Slightly higher weight for content
    'collab_weight': 0.4,
    'top_n_hybrid': 10,
    'default_recommendations': 5,
    'cache_timeout': 300
}

# Get absolute paths to data files
backend_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(backend_dir)
data_path = os.path.join(project_root, 'data', 'anime_clean.csv')
ratings_path = os.path.join(project_root, 'data', 'clean_ratings.csv')

# Verify files exist
if not os.path.exists(data_path):
    raise FileNotFoundError(f"Anime data not found at: {data_path}")
if not os.path.exists(ratings_path):
    raise FileNotFoundError(f"Ratings data not found at: {ratings_path}")

# Load data
ratings_df = pd.read_csv(ratings_path)
df, features = load_and_preprocess_data(data_path)
similarity_matrix = build_similarity_matrix(features)

def normalize_score(score, max_score):
    return min(score/max_score, 1.0)

def get_collab_recommendations(user_id, model, anime_df, ratings_df, n=5):
    # Get anime user has already rated
    rated_anime = ratings_df[ratings_df['user_id'] == user_id]['anime_id'].tolist()
    
    # Get all anime not rated by user
    unrated_anime = anime_df[~anime_df['anime_id'].isin(rated_anime)]
    
    # If no ratings exist for user, return popular anime
    if not rated_anime:
        return unrated_anime.sort_values('members', ascending=False).head(n)[[
            'name', 'genre', 'rating'
        ]].rename(columns={
            'name': 'Anime',
            'genre': 'Genres',
            'rating': 'Predicted Rating'
        }).to_dict('records')
    
    user_predictions = []
    
    for anime_id in unrated_anime['anime_id'].unique():
        pred = model.predict(user_id, anime_id)
        user_predictions.append((anime_id, pred.est))
    
    # Sort by predicted rating and get top-N
    user_predictions.sort(key=lambda x: x[1], reverse=True)
    top_n = user_predictions[:n]
    
    # Prepare response
    recommendations = []
    for anime_id, rating in top_n:
        anime = anime_df[anime_df['anime_id'] == anime_id].iloc[0]
        recommendations.append({
            'Anime': anime['name'],
            'Predicted Rating': float(f"{rating:.2f}"),
            'Genres': anime['genre'],  # Already a list from preprocessing
            'Collab_Score': normalize_score(rating, 10)
        })
    
    return recommendations

# Load or train collaborative model
try:
    collab_model = pickle.load(open('collab_model.pkl', 'rb'))
    # Verify the loaded model has the predict method
    if not hasattr(collab_model, 'predict'):
        raise AttributeError("Loaded model is missing predict method")
except (FileNotFoundError, EOFError, AttributeError) as e:
    logger.error(f"Model loading failed: {str(e)}")
    logger.info("Training new collaborative model...")
    reader = Reader(rating_scale=(1, 10))
    data = Dataset.load_from_df(ratings_df[['user_id', 'anime_id', 'rating']], reader)
    trainset = data.build_full_trainset()
    
    collab_model = SVD(
        n_factors=50,
        n_epochs=20,
        lr_all=0.003,
        reg_all=0.05,
        random_state=42
    )
    collab_model.fit(trainset)
    pickle.dump(collab_model, open('collab_model.pkl', 'wb'))

# Recommendation Endpoints
@app.route('/recommend/content', methods=['GET'])
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def content_based():
    title = request.args.get('title', default='', type=str)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)

    if not title:
        return jsonify({"error": "Title parameter is required"}), 400

    if not isinstance(title, str) or len(title.strip()) < 2:
        return jsonify({"error": "Title must be a string with at least 2 characters"}), 400

    recommendations = get_recommendations(title, df, similarity_matrix, n)
    if recommendations.empty:
        return jsonify({"error": "No recommendations found"}), 404
    return jsonify(recommendations.to_dict('records'))

@app.route('/recommend/collab', methods=['GET'])
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def collab_based():
    user_id = request.args.get('user_id', type=int)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)

    if user_id is None:
        return jsonify({"error": "user_id parameter is required"}), 400
    
    if not isinstance(user_id, int) or user_id < 1:
        return jsonify({"error": "user_id must be a positive integer"}), 400

    recommendations = get_collab_recommendations(user_id, collab_model, df, ratings_df, n)
    if not recommendations:
        return jsonify({"error": "No recommendations found"}), 404
    return jsonify(recommendations)

@app.route('/recommend/hybrid', methods=['GET'])
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def hybrid_based():
    try:
        title = request.args.get('title', default='', type=str)
        user_id = request.args.get('user_id', type=int)
        n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)

        if not title or user_id is None:
            return jsonify({"error": "Both title and user_id are required"}), 400
        
        if user_id == 0:
            return jsonify({"error": "Invalid user_id"}), 400

        # Get recommendations from both methods
        content_recs = get_recommendations(title, df, similarity_matrix, n)
        collab_recs = get_collab_recommendations(user_id, collab_model, df, ratings_df, n)
        
        # Convert content_recs to dict list
        content_list = content_recs.to_dict('records') if not content_recs.empty else []
        
        # Get hybrid recommendations
        hybrid_list = merge_recommendations(content_list, collab_recs)
        
        return jsonify({
            'content_based': content_list,
            'collaborative': collab_recs,
            'hybrid': hybrid_list[:n]  # Ensure only n recommendations are returned
        })
    except Exception as e:
        logger.error(f"Error in hybrid recommendations: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


def merge_recommendations(content_recs, collab_recs):
    if not content_recs and not collab_recs:
        return []
    
    hybrid = []
    anime_scores = {}
    
    # Process content recommendations
    content_recs = content_recs or []
    for item in content_recs:
        anime = item['Anime']
        anime_scores[anime] = {
            'content_score': float(item['Similarity Score']),
            'collab_score': 0,
            'data': item
        }
    
    # Process collaborative recommendations
    collab_recs = collab_recs or []
    for item in collab_recs:
        anime = item['Anime']
        if anime in anime_scores:
            anime_scores[anime]['collab_score'] = item['Collab_Score']
        else:
            anime_scores[anime] = {
                'content_score': 0,
                'collab_score': item['Collab_Score'],
                'data': item
            }
    
    # Calculate combined scores with weights
    for anime, scores in anime_scores.items():
        combined = (scores['content_score'] * CONFIG['content_weight'] + 
                   scores['collab_score'] * CONFIG['collab_weight'])
        
        # Prepare unified response format
        result = {
            'Anime': anime,
            'Combined_Score': f"{combined:.3f}",
            'Method': 'hybrid' if scores['content_score'] and scores['collab_score'] else 
                     'content' if scores['content_score'] else 'collab'
        }
        
        # Add all available fields
        if 'Similarity Score' in scores['data']:
            result.update({
                'Similarity Score': scores['data']['Similarity Score'],
                'Rating': scores['data']['Rating'],
                'Genres': scores['data']['Genres']
            })
        if 'Predicted Rating' in scores['data']:
            result.update({
                'Predicted Rating': scores['data']['Predicted Rating'],
                'Genres': scores['data']['Genres']
            })
        
        hybrid.append(result)
    
    # Return top N hybrid recommendations
    return sorted(hybrid, key=lambda x: float(x['Combined_Score']), reverse=True)[:CONFIG['top_n_hybrid']]

@app.route('/health', methods=['GET'])
def health_check():

    return jsonify({"status": "healthy", "message": "Recommendation service is running"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)