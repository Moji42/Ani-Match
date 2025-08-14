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
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


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

    # Validation
    if not title:
        return jsonify({"error": "Title parameter is required"}), 400
    if len(title.strip()) < 2:
        return jsonify({"error": "Title must be at least 2 characters"}), 400

    recommendations = get_recommendations(title, df, similarity_matrix, n)
    if recommendations is None or recommendations.empty:
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

        # Validation
        if not title or not isinstance(title, str) or len(title.strip()) < 2:
            return jsonify({"error": "Title must be a string with at least 2 characters"}), 400
        if user_id is None or user_id < 1:
            return jsonify({"error": "Valid user_id is required"}), 400

        # Get 3x more candidates to improve hybrid blending
        content_recs = get_recommendations(title, df, similarity_matrix, n*3)
        collab_recs = get_collab_recommendations(user_id, collab_model, df, ratings_df, n*3)
        
        content_list = content_recs.to_dict('records') if not content_recs.empty else []
        hybrid_list = merge_recommendations(content_list, collab_recs)
        
        return jsonify({
            'content_based': content_list[:n],  # Return original requested amount
            'collaborative': collab_recs[:n],
            'hybrid': hybrid_list[:n]
        })
    except Exception as e:
        logger.error(f"Error in hybrid recommendations: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/recommend/random', methods=['GET'])
def random_recommendations():
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
    
    # Get fresh random sample without replacement
    random_sample = df.sample(n=min(n, len(df)), replace=False)
    
    recommendations = []
    for _, row in random_sample.iterrows():
        recommendations.append({
            'Anime': row['name'],
            'Genres': row['genre'],
            'Rating': row['rating'],
            'Type': 'random',
            'Members': row['members']
        })
    
    # Add cache-control headers to prevent any caching
    response = jsonify(recommendations)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def merge_recommendations(content_recs, collab_recs):
    # Handle case where new user gets popular items without Collab_Score
    for item in collab_recs:
        if 'Collab_Score' not in item:
            item['Collab_Score'] = item.get('Predicted Rating', 0) / 10

    if not content_recs and not collab_recs:
        return []
    
    hybrid = []
    anime_scores = {}
    
    # Process content recommendations
    for item in content_recs:
        anime = item['Anime']
        anime_scores[anime] = {
            'content_score': float(item['Similarity Score']),
            'collab_score': 0,
            'genres': set(item['Genres']),
            'content_data': item,
            'collab_data': None
        }
    
    # Process collaborative recommendations
    for item in collab_recs:
        anime = item['Anime']
        if anime in anime_scores:
            # Calculate genre overlap bonus for existing items
            content_genres = anime_scores[anime]['genres']
            collab_genres = set(item['Genres'])
            genre_overlap = len(content_genres & collab_genres) / len(content_genres | collab_genres)
            genre_bonus = genre_overlap * 0.1  # 10% bonus
            
            anime_scores[anime].update({
                'collab_score': item['Collab_Score'] + genre_bonus,
                'collab_data': item
            })
        else:
            anime_scores[anime] = {
                'content_score': 0,
                'collab_score': item['Collab_Score'],
                'genres': set(item['Genres']),
                'content_data': None,
                'collab_data': item
            }
    
    # Calculate combined scores and prepare results
    for anime, scores in anime_scores.items():
        combined = (scores['content_score'] * CONFIG['content_weight'] + 
                   scores['collab_score'] * CONFIG['collab_weight'])
        
        method = 'hybrid' if (scores['content_score'] > 0 and scores['collab_score'] > 0) \
                else 'content' if scores['content_score'] > 0 \
                else 'collab'
        
        result = {
            'Anime': anime,
            'Combined_Score': f"{combined:.3f}",
            'Method': method,
            'Genres': list(scores['genres'])  # Convert set back to list
        }
        
        # Merge data from both sources
        if scores['content_data']:
            result.update({
                'Similarity_Score': scores['content_data']['Similarity Score'],
                'Content_Rating': scores['content_data']['Rating']
            })
        if scores['collab_data']:
            result.update({
                'Predicted_Rating': scores['collab_data']['Predicted Rating']
            })
        
        hybrid.append(result)
    
    # Return top N sorted by combined score
    return sorted(hybrid, key=lambda x: float(x['Combined_Score']), reverse=True)[:CONFIG['top_n_hybrid']]

@app.route('/health', methods=['GET'])
def health_check():

    return jsonify({"status": "healthy", "message": "Recommendation service is running"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)