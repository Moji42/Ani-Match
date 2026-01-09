#backend/app.py
from flask import Flask, request, jsonify, redirect, url_for, session
from content_based import load_and_preprocess_data, build_similarity_matrix, get_recommendations
from supabase import create_client, Client
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import pandas as pd
from surprise import Dataset, Reader, SVD
import pickle
import os
import logging
from functools import lru_cache
from flask_caching import Cache
from flask_cors import CORS
from dotenv import load_dotenv
import datetime
import secrets
import requests
from urllib.parse import urlencode, urljoin
from auth import (
    auth_required, auth_optional, github_auth, github_oauth_callback, 
    debug_github_config, add_user_preference, get_user_preferences, get_user_stats
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
BASE_URL = "http://127.0.0.1:5000"

# Configure JWT
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(hours=24)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
jwt = JWTManager(app)

# Configure Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
if not supabase_url or not supabase_key:
    raise ValueError("Supabase URL and Key must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure caching
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
cache.init_app(app)

# Configuration for model
CONFIG = {
    'content_weight': 0.6,
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
    
    if isinstance(anime_type, str):
        types = [t.strip().lower() for t in anime_type.split(',')]
    else:
        types = [str(anime_type).lower()]
    
    mask = df_subset['type'].str.lower().isin(types)
    filtered_df = df_subset[mask]
    
    logger.info(f"Filtered from {len(df_subset)} to {len(filtered_df)} anime for types: {types}")
    return filtered_df

def get_collab_recommendations(user_id, model, anime_df, ratings_df, n=5, anime_type=None):
    """Get collaborative filtering recommendations"""
    n = validate_n_parameter(n)
    
    # Get anime user has already rated
    rated_anime = ratings_df[ratings_df['user_id'] == user_id]['anime_id'].tolist()
    
    # Apply type filtering
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

@app.before_request
def check_supabase():
    try:
        supabase.auth.get_session()
    except Exception as e:
        logger.error(f"Supabase connection error: {str(e)}")

# Authentication endpoints
@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Create user in Supabase
        result = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        logger.info(f"Registration attempt for email: {email}, Supabase result: {result}")

        # Check if registration succeeded
        user = getattr(result, 'user', None)
        if user:
            # Generate JWT token
            access_token = create_access_token(identity=user.id)

            return jsonify({
                "message": "User registered successfully",
                "user_id": user.id,
                "email": user.email,
                "access_token": access_token
            }), 201

        # Handle registration errors from Supabase
        error = getattr(result, 'error', None)
        if error:
            return jsonify({"error": getattr(error, "message", "Registration failed")}), 400

        return jsonify({"error": "Failed to create user"}), 400

    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)

        error_message = str(e)
        if "already registered" in error_message.lower():
            return jsonify({"error": "Email is already registered"}), 409
        elif "Failed to fetch" in error_message:
            return jsonify({"error": "Cannot connect to authentication server"}), 503
        else:
            return jsonify({"error": "Internal server error"}), 500

@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Authenticate user with Supabase
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        logger.info(f"Login attempt for email: {email}, Supabase result: {result}")

        # Check if authentication succeeded
        user = getattr(result, 'user', None)  # Works even if result is dict or object
        if not user:
            # Could also check for result.error
            return jsonify({"error": "Invalid credentials"}), 401

        # Generate JWT token
        access_token = create_access_token(identity=user.id)

        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "email": user.email,
            "access_token": access_token
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)

        # Specific error handling for Supabase auth errors
        error_message = str(e)
        if "Invalid login credentials" in error_message:
            return jsonify({"error": "Invalid credentials"}), 401
        elif "Failed to fetch" in error_message:
            return jsonify({"error": "Cannot connect to authentication server"}), 503
        else:
            return jsonify({"error": "Internal server error"}), 500

# OAuth Routes
@app.route('/auth/google', methods=['GET'])
def google_auth():
    """Initialize Google OAuth flow"""
    try:
        redirect_url = request.args.get('redirect_to', 'http://localhost:8080')
        
        # Use Supabase's OAuth directly
        result = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": url_for('oauth_callback', provider='google', _external=True)
            }
        })
        
        if hasattr(result, 'url'):
            return redirect(result.url)
        else:
            # Fallback: redirect to Supabase OAuth URL directly
            supabase_oauth_url = f"{supabase_url}/auth/v1/authorize"
            params = {
                'provider': 'google',
                'redirect_to': url_for('oauth_callback', provider='google', _external=True)
            }
            return redirect(f"{supabase_oauth_url}?{urlencode(params)}")
            
    except Exception as e:
        logger.error(f"Google OAuth initiation error: {str(e)}")
        return jsonify({"error": "OAuth initialization failed"}), 500

@app.route('/auth/github', methods=['GET'])
def github_auth_route():
    """Delegate GitHub OAuth initiation to backend/auth.py implementation."""
    try:
        # call the github_auth implementation imported from auth.py
        return github_auth()
    except Exception as e:
        logger.error(f"GitHub OAuth initiation delegation error: {str(e)}")
        return jsonify({"error": "OAuth initialization failed"}), 500

@app.route('/auth/callback/<provider>')
def oauth_callback(provider):
    """Handle OAuth callback from Google/GitHub"""
    try:
        # Delegate to auth module for provider-specific handling when available
        if provider == 'github':
            return github_oauth_callback()

        # Get the authorization code from the callback
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logger.error(f"OAuth error from {provider}: {error}")
            return jsonify({"error": f"OAuth failed: {error}"}), 400
        
        if not code:
            return jsonify({"error": "Authorization code not received"}), 400
        
        # Exchange code for session with Supabase
        result = supabase.auth.exchange_code_for_session({
            "auth_code": code
        })
        
        user = getattr(result, 'user', None)
        session_data = getattr(result, 'session', None)
        
        if user and session_data:
            # Generate JWT token for our application
            access_token = create_access_token(identity=user.id)
            
            # Create HTML response that sends auth data to parent window
            response_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Successful</title>
                <script>
                    // Send auth data to parent window
                    const authData = {{
                        access_token: '{access_token}',
                        user_id: '{user.id}',
                        email: '{user.email}',
                        provider: '{provider}'
                    }};
                    
                    window.opener.postMessage({{
                        type: 'OAUTH_SUCCESS',
                        data: authData
                    }}, '*');
                    
                    // Close the popup after a short delay
                    setTimeout(() => window.close(), 1000);
                </script>
            </head>
            <body>
                <div style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h2>Authentication Successful!</h2>
                    <p>Welcome, {user.email}</p>
                    <p>You can close this window now.</p>
                </div>
            </body>
            </html>
            """
            return response_html
        else:
            return jsonify({"error": "Failed to authenticate with OAuth provider"}), 401
            
    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {str(e)}")
        return jsonify({"error": f"OAuth callback failed: {str(e)}"}), 500

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        # Get user ID from JWT token
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({"error": "Invalid or missing token"}), 401

        # Fetch user details from Supabase by ID
        response = supabase.auth.admin.get_user(user_id)
        user = getattr(response, "user", None)

        if user:
            return jsonify({
                "user_id": user.id,
                "email": user.email,
                "created_at": user.created_at,
                "provider": getattr(user, 'app_metadata', {}).get('provider', 'email')
            }), 200
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        logger.error(f"Profile fetch error: {str(e)}", exc_info=True)
        error_message = str(e)
        if "not found" in error_message.lower():
            return jsonify({"error": "User not found"}), 404
        elif "Failed to fetch" in error_message:
            return jsonify({"error": "Cannot connect to authentication server"}), 503
        else:
            return jsonify({"error": "Internal server error"}), 500

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        # Optionally invalidate Supabase session
        try:
            supabase.auth.sign_out()
        except:
            pass  # Continue even if Supabase logout fails
        
        return jsonify({"message": "Logout successful"}), 200
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


# User favorites / watchlist endpoints
@app.route('/user/favorites', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def user_favorites():
    user_id = get_jwt_identity()
    try:
        if request.method == 'GET':
            resp = supabase.table('favorites').select('*').eq('user_id', user_id).execute()
            data = getattr(resp, 'data', None) or resp.get('data') if isinstance(resp, dict) else None
            return jsonify(data or [])

        body = request.get_json() or {}
        anime_name = body.get('anime') or request.args.get('anime')
        if not anime_name:
            return jsonify({'error': 'anime name is required'}), 400

        if request.method == 'POST':
            payload = {
                'user_id': user_id,
                'anime': anime_name,
                'added_at': datetime.datetime.utcnow().isoformat()
            }
            resp = supabase.table('favorites').insert(payload).execute()
            err = getattr(resp, 'error', None) or (resp.get('error') if isinstance(resp, dict) else None)
            if err:
                err_msg = str(err) if err else 'Unknown error'
                logger.error(f"Supabase insert error: {err_msg}")
                return jsonify({'error': f'Failed to add favorite: {err_msg}'}), 500
            return jsonify({'message': 'Added to favorites'}), 201

        if request.method == 'DELETE':
            resp = supabase.table('favorites').delete().eq('user_id', user_id).eq('anime', anime_name).execute()
            err = getattr(resp, 'error', None) or (resp.get('error') if isinstance(resp, dict) else None)
            if err:
                err_msg = str(err) if err else 'Unknown error'
                logger.error(f"Supabase delete error: {err_msg}")
                return jsonify({'error': f'Failed to remove favorite: {err_msg}'}), 500
            return jsonify({'message': 'Removed from favorites'}), 200

    except Exception as e:
        logger.error(f"Favorites endpoint error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/user/watchlist', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def user_watchlist():
    user_id = get_jwt_identity()
    try:
        if request.method == 'GET':
            resp = supabase.table('watchlist').select('*').eq('user_id', user_id).execute()
            data = getattr(resp, 'data', None) or resp.get('data') if isinstance(resp, dict) else None
            return jsonify(data or [])

        body = request.get_json() or {}
        anime_name = body.get('anime') or request.args.get('anime')
        if not anime_name:
            return jsonify({'error': 'anime name is required'}), 400

        if request.method == 'POST':
            payload = {
                'user_id': user_id,
                'anime': anime_name,
                'added_at': datetime.datetime.utcnow().isoformat()
            }
            resp = supabase.table('watchlist').insert(payload).execute()
            err = getattr(resp, 'error', None) or (resp.get('error') if isinstance(resp, dict) else None)
            if err:
                err_msg = str(err) if err else 'Unknown error'
                logger.error(f"Supabase insert error: {err_msg}")
                return jsonify({'error': f'Failed to add to watchlist: {err_msg}'}), 500
            return jsonify({'message': 'Added to watchlist'}), 201

        if request.method == 'DELETE':
            resp = supabase.table('watchlist').delete().eq('user_id', user_id).eq('anime', anime_name).execute()
            err = getattr(resp, 'error', None) or (resp.get('error') if isinstance(resp, dict) else None)
            if err:
                err_msg = str(err) if err else 'Unknown error'
                logger.error(f"Supabase delete error: {err_msg}")
                return jsonify({'error': f'Failed to remove from watchlist: {err_msg}'}), 500
            return jsonify({'message': 'Removed from watchlist'}), 200

    except Exception as e:
        logger.error(f"Watchlist endpoint error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/user/preferences', methods=['GET', 'POST', 'DELETE'])
@jwt_required()
def user_preferences():
    """Manage simple user preferences (like/dislike) stored in Supabase 'preferences' table."""
    user_id = get_jwt_identity()
    try:
        if request.method == 'GET':
            action = request.args.get('action')
            query = supabase.table('preferences').select('*').eq('user_id', user_id)
            if action:
                query = query.eq('action', action)
            resp = query.execute()
            data = getattr(resp, 'data', None) or (resp.get('data') if isinstance(resp, dict) else None)
            return jsonify(data or [])

        body = request.get_json() or {}
        anime_name = body.get('anime') or request.args.get('anime')
        action = body.get('action') or request.args.get('action')
        value = body.get('value')

        if not anime_name or not action:
            return jsonify({'error': 'anime and action are required'}), 400

        if request.method == 'POST':
            payload = {
                'user_id': user_id,
                'anime': anime_name,
                'action': action,
                'value': value,
                'added_at': datetime.datetime.utcnow().isoformat()
            }
            resp = supabase.table('preferences').insert(payload).execute()
            err = getattr(resp, 'error', None) or (resp.get('error') if isinstance(resp, dict) else None)
            if err:
                err_msg = str(err) if err else 'Unknown error'
                logger.error(f"Supabase insert error (preferences): {err_msg}")
                return jsonify({'error': f'Failed to add preference: {err_msg}'}), 500
            return jsonify({'message': 'Preference added'}), 201

        if request.method == 'DELETE':
            # allow deletion by anime+action
            resp = supabase.table('preferences').delete().eq('user_id', user_id).eq('anime', anime_name).eq('action', action).execute()
            err = getattr(resp, 'error', None) or (resp.get('error') if isinstance(resp, dict) else None)
            if err:
                err_msg = str(err) if err else 'Unknown error'
                logger.error(f"Supabase delete error (preferences): {err_msg}")
                return jsonify({'error': f'Failed to remove preference: {err_msg}'}), 500
            return jsonify({'message': 'Preference removed'}), 200

    except Exception as e:
        logger.error(f"Preferences endpoint error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# Recommendation Endpoints (keeping all existing ones)
@app.route('/recommend/content', methods=['GET'])
@jwt_required()
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def content_based():
    """Content-based recommendation endpoint"""
    title = request.args.get('title', default='', type=str)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
    anime_type = request.args.get('type', default='all', type=str)
    n = validate_n_parameter(n)

    if not title:
        return jsonify({"error": "Title parameter is required"}), 400
    if len(title.strip()) < 2:
        return jsonify({"error": "Title must be at least 2 characters"}), 400

    try:
        recommendations = get_recommendations(title, df, similarity_matrix, n, anime_type)
        if recommendations is None or recommendations.empty:
            return jsonify({"error": "No recommendations found"}), 404
        
        recommendations = recommendations.head(n)
        return jsonify(recommendations.to_dict('records'))
    except Exception as e:
        logger.error(f"Content-based recommendation failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/recommend/collab', methods=['GET'])
@app.route('/recommend/collaborative', methods=['GET'])
@jwt_required()
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def collab_based():
    """Collaborative filtering recommendation endpoint"""
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
        
        recommendations = recommendations[:n]
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Collaborative recommendation failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/recommend/hybrid', methods=['GET'])
@jwt_required()
@cache.cached(timeout=CONFIG['cache_timeout'], query_string=True)
def hybrid_based():
    """Hybrid recommendation endpoint"""
    try:
        title = request.args.get('title', default='', type=str)
        user_id = request.args.get('user_id', type=int)
        n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
        anime_type = request.args.get('type', default='all', type=str)
        n = validate_n_parameter(n)

        if not title or len(title.strip()) < 2:
            return jsonify({"error": "Title must be at least 2 characters"}), 400
        if not user_id or user_id < 1:
            return jsonify({"error": "Valid user_id is required"}), 400

        # Get content-based recommendations
        content_fetch_n = min(n * 2, CONFIG['max_recommendations'])
        content_recs_df = get_recommendations(title, df, similarity_matrix, content_fetch_n, anime_type)
        content_list = content_recs_df.to_dict('records') if not content_recs_df.empty else []

        # Get collaborative recommendations
        collab_fetch_n = min(n * 2, CONFIG['max_recommendations'])
        collab_list = get_collab_recommendations(user_id, collab_model, df, ratings_df, collab_fetch_n, anime_type)

        # Simple merge logic (you can enhance this)
        hybrid_results = []
        seen_anime = set()
        
        # Add collaborative recommendations first
        for item in collab_list:
            if item['Anime'] not in seen_anime:
                hybrid_results.append({**item, 'Method': 'collab'})
                seen_anime.add(item['Anime'])
        
        # Add content-based recommendations
        for item in content_list:
            if item['Anime'] not in seen_anime:
                hybrid_results.append({**item, 'Method': 'content'})
                seen_anime.add(item['Anime'])
        
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
@jwt_required()
def random_recommendations():
    """Random anime recommendations endpoint"""
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)
    anime_type = request.args.get('type', default='all', type=str)
    n = validate_n_parameter(n)
    
    try:
        filtered_df = filter_by_type(df, anime_type)
        
        if filtered_df.empty:
            return jsonify({"error": f"No anime found for type: {anime_type}"}), 404
        
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
        
        response = jsonify(recommendations)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        logger.error(f"Random recommendations failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/api/types', methods=['GET'])
@jwt_required()
def get_available_types():
    """Get all available anime types"""
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

@app.route('/recommend/replacement', methods=['GET'])
@jwt_required()
def get_replacement_recommendation():
    """Get a single replacement recommendation"""
    try:
        title = request.args.get('title', default='', type=str)
        user_id = request.args.get('user_id', type=int)
        method = request.args.get('method', default='content', type=str)
        anime_type = request.args.get('type', default='all', type=str)
        excluded_titles = request.args.getlist('excluded')  # List of titles to exclude
        
        if not title and method != 'collab':
            return jsonify({"error": "Title parameter is required for content-based methods"}), 400
        
        # Get a single recommendation
        if method == 'content':
            recommendations = get_recommendations(title, df, similarity_matrix, 10, anime_type)
            if recommendations is None or recommendations.empty:
                return jsonify({"error": "No recommendations found"}), 404
            
            # Filter out excluded titles
            filtered_recs = recommendations[~recommendations['Anime'].isin(excluded_titles)]
            if filtered_recs.empty:
                # If all recommendations are excluded, return a random one
                filtered_recs = filter_by_type(df, anime_type).sample(n=1)
                replacement = {
                    'Anime': filtered_recs.iloc[0]['name'],
                    'Rating': float(filtered_recs.iloc[0]['rating']) if pd.notna(filtered_recs.iloc[0]['rating']) else 0.0,
                    'Genres': filtered_recs.iloc[0]['genre'],
                    'Type': filtered_recs.iloc[0]['type'],
                    'Method': 'random'
                }
            else:
                replacement = filtered_recs.iloc[0].to_dict()
                replacement['Method'] = 'content'
                
        elif method == 'collab':
            if not user_id:
                return jsonify({"error": "user_id is required for collaborative filtering"}), 400
                
            recommendations = get_collab_recommendations(user_id, collab_model, df, ratings_df, 10, anime_type)
            if not recommendations:
                return jsonify({"error": "No recommendations found"}), 404
            
            # Filter out excluded titles
            filtered_recs = [rec for rec in recommendations if rec['Anime'] not in excluded_titles]
            if not filtered_recs:
                # If all recommendations are excluded, return a random one
                filtered_df = filter_by_type(df, anime_type)
                if filtered_df.empty:
                    return jsonify({"error": "No anime found for the specified type"}), 404
                random_anime = filtered_df.sample(n=1).iloc[0]
                replacement = {
                    'Anime': random_anime['name'],
                    'Rating': float(random_anime['rating']) if pd.notna(random_anime['rating']) else 0.0,
                    'Genres': random_anime['genre'],
                    'Type': random_anime['type'],
                    'Method': 'random'
                }
            else:
                replacement = filtered_recs[0]
                replacement['Method'] = 'collab'
                
        else:  # hybrid or other methods - default to content-based
            recommendations = get_recommendations(title, df, similarity_matrix, 10, anime_type)
            if recommendations is None or recommendations.empty:
                return jsonify({"error": "No recommendations found"}), 404
            
            # Filter out excluded titles
            filtered_recs = recommendations[~recommendations['Anime'].isin(excluded_titles)]
            if filtered_recs.empty:
                # If all recommendations are excluded, return a random one
                filtered_df = filter_by_type(df, anime_type)
                if filtered_df.empty:
                    return jsonify({"error": "No anime found for the specified type"}), 404
                random_anime = filtered_df.sample(n=1).iloc[0]
                replacement = {
                    'Anime': random_anime['name'],
                    'Rating': float(random_anime['rating']) if pd.notna(random_anime['rating']) else 0.0,
                    'Genres': random_anime['genre'],
                    'Type': random_anime['type'],
                    'Method': 'random'
                }
            else:
                replacement = filtered_recs.iloc[0].to_dict()
                replacement['Method'] = 'content'
        
        return jsonify(replacement)
        
    except Exception as e:
        logger.error(f"Replacement recommendation failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route('/health', methods=['GET'])
@jwt_required()
def health_check():
    """Health check endpoint"""
    user_id = get_jwt_identity()
    return jsonify({
        "status": "healthy", 
        "message": "Recommendation service is running",
        "user_id": user_id,
        "config": {
            "max_recommendations": CONFIG['max_recommendations'],
            "default_recommendations": CONFIG['default_recommendations']
        }
    })

@app.route('/public/health', methods=['GET'])
def public_health_check():
    """Public health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "message": "Recommendation service is running"
    })

if __name__ == '__main__':
    logger.info(f"Starting Flask app with config: {CONFIG}")
    app.run(debug=True, port=5000)