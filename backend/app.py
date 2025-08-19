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
CORS(app, resources={
    r"/recommend/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080"],
        "methods": ["GET"],
        "allow_headers": ["*"]
    }
})

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
    'max_recommendations': 20,
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
    """Normalize score to 0-1 range"""
    return min(score/max_score, 1.0) if max_score > 0 else 0

def validate_n_parameter(n):
    """Validate and normalize the n parameter"""
    if n is None:
        return CONFIG['default_recommendations']
    try:
        n = int(n)
        return max(1, min(n, CONFIG['max_recommendations']))
    except (ValueError, TypeError):
        return CONFIG['default_recommendations']

def filter_by_type(df_subset, anime_type):
    """Filter anime DataFrame by type(s)"""
    if not anime_type or anime_type.lower() == 'all':
        return df_subset
    
    # Handle multiple types (comma-separated)
    if isinstance(anime_type, str):
        types = [t.strip().lower() for t in anime_type.split(',')]
    else:
        types = [str(anime_type).lower()]
    
    # Create a boolean mask for filtering
    mask = df_subset['type'].str.lower().isin(types)
    filtered_df = df_subset[mask]
    
    logger.info(f"Filtered from {len(df_subset)} to {len(filtered_df)} anime for types: {types}")
    return filtered_df

# backend/app.py
def get_collab_recommendations(user_id, model, anime_df, ratings_df, n=5, anime_type=None):
    """Get collaborative filtering recommendations with proper n parameter handling and type filtering"""
    n = validate_n_parameter(n)
    
    # Get anime user has already rated
    rated_anime = ratings_df[ratings_df['user_id'] == user_id]['anime_id'].tolist()
    
    # Apply type filtering to the full anime DataFrame
    filtered_df = filter_by_type(anime_df, anime_type)
    
    if filtered_df.empty:
        logger.warning(f"No anime found for type filter: {anime_type}")
        return []
    
    # Get all anime not rated by user (from filtered set)
    unrated_anime = filtered_df[~filtered_df['anime_id'].isin(rated_anime)]
    
    # If no ratings exist for user, return popular anime from filtered set
    if not rated_anime:
        popular_anime = unrated_anime.sort_values('members', ascending=False).head(n)
        recommendations = []
        for _, row in popular_anime.iterrows():
            recommendations.append({
                'Anime': row['name'],
                'Predicted Rating': float(f"{row['rating']:.2f}") if pd.notna(row['rating']) else 5.0,
                'Genres': row['genre'],
                'Type': row['type'],
                'Collab_Score': normalize_score(row['rating'] if pd.notna(row['rating']) else 5.0, 10)
            })
        return recommendations
    
    user_predictions = []
    
    # Get predictions for unrated anime in filtered set
    for anime_id in unrated_anime['anime_id'].unique():
        try:
            pred = model.predict(user_id, anime_id)
            user_predictions.append((anime_id, pred.est))
        except Exception as e:
            logger.warning(f"Prediction failed for anime_id {anime_id}: {str(e)}")
            continue
    
    # Sort by predicted rating and get top-N
    user_predictions.sort(key=lambda x: x[1], reverse=True)
    top_n = user_predictions[:n]
    
    # Prepare response
    recommendations = []
    for anime_id, rating in top_n:
        try:
            anime_row = filtered_df[filtered_df['anime_id'] == anime_id]
            if anime_row.empty:
                continue
            anime = anime_row.iloc[0]
            recommendations.append({
                'Anime': anime['name'],
                'Predicted Rating': float(f"{rating:.2f}"),
                'Genres': anime['genre'],
                'Type': anime['type'],
                'Collab_Score': normalize_score(rating, 10)
            })
        except Exception as e:
            logger.warning(f"Error processing anime_id {anime_id}: {str(e)}")
            continue
    
    return recommendations

# Load or train collaborative model
try:
    collab_model = pickle.load(open('collab_model.pkl', 'rb'))
    # Verify the loaded model has the predict method
    if not hasattr(collab_model, 'predict'):
        raise AttributeError("Loaded model is missing predict method")
    logger.info("Collaborative model loaded successfully")
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
    logger.info("New collaborative model trained and saved")

# Recommendation Endpoints

@app.route('/recommend/content', methods=['GET'])
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def content_based():
    """Content-based recommendation endpoint with type filtering"""
    title = request.args.get('title', default='', type=str)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
    anime_type = request.args.get('type', default='all', type=str)
    n = validate_n_parameter(n)

    # Validation
    if not title:
        return jsonify({"error": "Title parameter is required"}), 400
    if len(title.strip()) < 2:
        return jsonify({"error": "Title must be at least 2 characters"}), 400

    try:
        recommendations = get_recommendations(title, df, similarity_matrix, n, anime_type)
        if recommendations is None or recommendations.empty:
            return jsonify({"error": "No recommendations found"}), 404
        
        # Ensure we return exactly n recommendations (or less if not enough available)
        recommendations = recommendations.head(n)
        return jsonify(recommendations.to_dict('records'))
    except Exception as e:
        logger.error(f"Content-based recommendation failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/recommend/collab', methods=['GET'])
@app.route('/recommend/collaborative', methods=['GET'])
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def collab_based():
    """Collaborative filtering recommendation endpoint with type filtering"""
    user_id = request.args.get('user_id', type=int)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
    anime_type = request.args.get('type', default='all', type=str)
    n = validate_n_parameter(n)

    if user_id is None:
        return jsonify({"error": "user_id parameter is required"}), 400
    
    if not isinstance(user_id, int) or user_id < 1:
        return jsonify({"error": "user_id must be a positive integer"}), 400

    try:
        recommendations = get_collab_recommendations(user_id, collab_model, df, ratings_df, n, anime_type)
        if not recommendations:
            return jsonify({"error": "No recommendations found"}), 404
        
        # Ensure we return exactly n recommendations (or less if not enough available)
        recommendations = recommendations[:n]
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Collaborative recommendation failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# backend/app.py
@app.route('/recommend/hybrid', methods=['GET'])
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def hybrid_based():
    """Hybrid recommendation endpoint combining content and collaborative filtering with type filtering"""
    try:
        title = request.args.get('title', default='', type=str)
        user_id = request.args.get('user_id', type=int)
        n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
        anime_type = request.args.get('type', default='all', type=str)
        n = validate_n_parameter(n)

        # Validation
        if not title or len(title.strip()) < 2:
            return jsonify({"error": "Title must be at least 2 characters"}), 400
        if not user_id or user_id < 1:
            return jsonify({"error": "Valid user_id is required"}), 400

        # Get content-based recommendations (fetch more to allow for merging)
        fetch_multiplier = max(2, n // 2)  # Fetch at least 2x the requested amount
        content_fetch_n = min(n * fetch_multiplier, CONFIG['max_recommendations'])
        content_recs_df = get_recommendations(title, df, similarity_matrix, content_fetch_n, anime_type)
        content_list = content_recs_df.to_dict('records') if not content_recs_df.empty else []

        # Get collaborative recommendations (fetch more to allow for merging)
        collab_fetch_n = min(n * fetch_multiplier, CONFIG['max_recommendations'])
        collab_list = get_collab_recommendations(user_id, collab_model, df, ratings_df, collab_fetch_n, anime_type)

        # Merge into hybrid using the duplicate-free, hybrid-first logic
        hybrid_results = merge_recommendations(content_list, collab_list, n)

        # Prepare final results with proper slicing
        hybrid_top_n = hybrid_results[:n]
        content_top_n = content_list[:n]
        collab_top_n = collab_list[:n]

        return jsonify({
            'content_based': content_top_n,
            'collaborative': collab_top_n,
            'hybrid': hybrid_top_n
        })

    except Exception as e:
        logger.error(f"Error in hybrid recommendations: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/recommend/random', methods=['GET'])
def random_recommendations():
    """Random anime recommendations endpoint with type filtering"""
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
    anime_type = request.args.get('type', default='all', type=str)
    n = validate_n_parameter(n)
    
    try:
        # Apply type filtering first
        filtered_df = filter_by_type(df, anime_type)
        
        if filtered_df.empty:
            return jsonify({"error": f"No anime found for type: {anime_type}"}), 404
        
        # Get fresh random sample without replacement
        available_anime = min(n, len(filtered_df))
        random_sample = filtered_df.sample(n=available_anime, replace=False)
        
        recommendations = []
        for _, row in random_sample.iterrows():
            recommendations.append({
                'Anime': row['name'],
                'Genres': row['genre'],
                'Rating': float(row['rating']) if pd.notna(row['rating']) else 0.0,
                'Type': row['type'],
                'Members': int(row['members']) if pd.notna(row['members']) else 0
            })
        
        # Add cache-control headers to prevent any caching
        response = jsonify(recommendations)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Random recommendations failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/types', methods=['GET'])
def get_available_types():
    """Get all available anime types for filtering"""
    try:
        if 'type' in df.columns:
            available_types = df['type'].dropna().unique().tolist()
            available_types.sort()
            return jsonify({
                'types': available_types,
                'count': len(available_types)
            })
        else:
            return jsonify({
                'types': ['TV', 'Movie', 'OVA', 'Special', 'ONA', 'Music'],
                'count': 6,
                'note': 'Default types returned - type column not found in data'
            })
    except Exception as e:
        logger.error(f"Failed to get available types: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def merge_recommendations(content_recs, collab_recs, target_n=None):
    """
    Merge content-based and collaborative recommendations into a hybrid list.
    
    Args:
        content_recs: List of content-based recommendations
        collab_recs: List of collaborative recommendations  
        target_n: Target number of final recommendations
    
    Returns:
        List of merged recommendations
    """
    if target_n is None:
        target_n = CONFIG['default_recommendations']
    
    if not content_recs and not collab_recs:
        return []

    hybrid = []
    anime_scores = {}

    # Step 1: Process content recommendations
    for item in content_recs:
        anime = item['Anime']
        content_score = float(item.get('Similarity Score', item.get('Content_Score', 0)))
        anime_scores[anime] = {
            'content_score': content_score,
            'collab_score': 0,
            'genres': set(item.get('Genres', [])),
            'content_data': item,
            'collab_data': None
        }

    # Step 2: Process collaborative recommendations
    for item in collab_recs:
        anime = item['Anime']
        collab_score = float(item.get('Collab_Score', item.get('Predicted Rating', 0)) / 10 if item.get('Predicted Rating', 0) > 1 else item.get('Collab_Score', item.get('Predicted Rating', 0)))
        
        if anime in anime_scores:
            # Anime appears in both - calculate genre bonus
            content_genres = anime_scores[anime]['genres']
            collab_genres = set(item.get('Genres', []))
            genre_bonus = len(content_genres & collab_genres) / len(content_genres | collab_genres) * 0.1 if content_genres | collab_genres else 0
            anime_scores[anime]['collab_score'] = collab_score + genre_bonus
            anime_scores[anime]['collab_data'] = item
        else:
            # Collab-only anime
            anime_scores[anime] = {
                'content_score': 0,
                'collab_score': collab_score,
                'genres': set(item.get('Genres', [])),
                'content_data': None,
                'collab_data': item
            }

    # Step 3: Percentile normalization for fair comparison
    content_values = [s['content_score'] for s in anime_scores.values() if s['content_score'] > 0]
    collab_values = [s['collab_score'] for s in anime_scores.values() if s['collab_score'] > 0]

    def percentile_rank(score, all_scores):
        if not all_scores or score <= 0:
            return 0
        sorted_scores = sorted(all_scores)
        try:
            index = sorted_scores.index(score)
            return index / (len(sorted_scores) - 1) if len(sorted_scores) > 1 else 1.0
        except ValueError:
            # Handle case where score is not exactly in the list
            for i, s in enumerate(sorted_scores):
                if s >= score:
                    return i / (len(sorted_scores) - 1) if len(sorted_scores) > 1 else 1.0
            return 1.0

    # Step 4: Compute combined scores and create result objects
    for anime, scores in anime_scores.items():
        content_pct = percentile_rank(scores['content_score'], content_values) if scores['content_score'] > 0 else 0
        collab_pct = percentile_rank(scores['collab_score'], collab_values) if scores['collab_score'] > 0 else 0

        combined = content_pct * CONFIG['content_weight'] + collab_pct * CONFIG['collab_weight']

        # Determine method
        method = 'hybrid' if content_pct > 0 and collab_pct > 0 else 'content' if content_pct > 0 else 'collab'

        result = {
            'Anime': anime,
            'Combined_Score': round(combined, 3),
            'Method': method,
            'Genres': list(scores['genres'])
        }

        # Add method-specific data including type
        if scores['content_data']:
            result.update({
                'Similarity_Score': scores['content_data'].get('Similarity Score'),
                'Content_Rating': scores['content_data'].get('Rating'),
                'Type': scores['content_data'].get('Type')
            })
        if scores['collab_data']:
            result.update({
                'Predicted_Rating': scores['collab_data'].get('Predicted Rating'),
                'Type': scores['collab_data'].get('Type')
            })

        hybrid.append(result)

    # Step 5: Sort by combined score
    hybrid_sorted = sorted(hybrid, key=lambda x: x['Combined_Score'], reverse=True)

    # Step 6: Ensure diversity and enforce constraints
    final_hybrid = []
    seen = set()
    
    # Separate by method type
    hybrid_items = [h for h in hybrid_sorted if h['Method'] == 'hybrid']
    content_items = [h for h in hybrid_sorted if h['Method'] == 'content']  
    collab_items = [h for h in hybrid_sorted if h['Method'] == 'collab']

    # Add items in priority order: hybrid first, then content, then collab
    for item_list in [hybrid_items, content_items, collab_items]:
        for item in item_list:
            if len(final_hybrid) >= target_n:
                break
            if item['Anime'] not in seen:
                final_hybrid.append(item)
                seen.add(item['Anime'])
        if len(final_hybrid) >= target_n:
            break

    # Step 7: Ensure minimum diversity - at least 2 collab items if available
    current_collab_count = len([h for h in final_hybrid if h['Method'] == 'collab'])
    min_collab = min(2, len(collab_items), target_n // 3)  # At least 2 or 1/3 of results, whichever is smaller
    
    if current_collab_count < min_collab:
        needed = min_collab - current_collab_count
        available_collab = [item for item in collab_items if item['Anime'] not in seen]
        
        # Replace lowest scoring non-collab items with collab items
        for i in range(min(needed, len(available_collab))):
            if len(final_hybrid) > min_collab:
                # Remove lowest scoring non-collab item
                for j in range(len(final_hybrid) - 1, -1, -1):
                    if final_hybrid[j]['Method'] != 'collab':
                        final_hybrid.pop(j)
                        break
            
            final_hybrid.append(available_collab[i])
            seen.add(available_collab[i]['Anime'])

    # Final sort by combined score
    final_hybrid.sort(key=lambda x: x['Combined_Score'], reverse=True)
    
    return final_hybrid[:target_n]

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "Recommendation service is running",
        "config": {
            "max_recommendations": CONFIG['max_recommendations'],
            "default_recommendations": CONFIG['default_recommendations']
        }
    })

if __name__ == '__main__':
    logger.info(f"Starting Flask app with config: {CONFIG}")
    app.run(debug=True, port=5000)