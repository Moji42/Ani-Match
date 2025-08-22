# backend/auth.py
import os
import jwt
import requests
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

def verify_supabase_token(token):
    """Verify Supabase JWT token and extract user info"""
    try:
        if not token:
            return None
            
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # For development, if JWT_SECRET is not set, use a simple user ID extraction
        if not SUPABASE_JWT_SECRET:
            logger.warning("SUPABASE_JWT_SECRET not set, using development mode")
            # Extract user ID from token (assuming it's formatted as user_id)
            return {'sub': token, 'email': f'user-{token}@example.com'}
        
        # Decode and verify the JWT token using Supabase's JWT secret
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience="authenticated",
            options={"verify_aud": False}  # Supabase tokens might not have proper audience
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None

def auth_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        user_info = verify_supabase_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user info to request context
        request.user = user_info
        return f(*args, **kwargs)
    
    return decorated_function

def auth_optional(f):
    """Decorator to optionally extract user info if token is present"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        request.user = None
        
        if auth_header:
            user_info = verify_supabase_token(auth_header)
            if user_info:
                request.user = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function

# backend/user_service.py
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db_path='user_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for user data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    anime_name TEXT NOT NULL,
                    action TEXT NOT NULL, -- 'like', 'dislike', 'rating'
                    value REAL, -- rating value if applicable
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    genres TEXT, -- JSON array of genres
                    UNIQUE(user_id, anime_name, action)
                )
            ''')
            
            # User stats table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id TEXT PRIMARY KEY,
                    total_ratings INTEGER DEFAULT 0,
                    average_rating REAL DEFAULT 0,
                    favorite_genres TEXT, -- JSON array
                    total_favorites INTEGER DEFAULT 0,
                    total_watchlist INTEGER DEFAULT 0,
                    recommendation_accuracy REAL DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("User database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
    
    def add_user_preference(self, user_id: str, anime_name: str, action: str, value: Optional[float] = None, genres: Optional[List[str]] = None):
        """Add or update user preference"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            genres_json = json.dumps(genres) if genres else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, anime_name, action, value, genres)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, anime_name, action, value, genres_json))
            
            conn.commit()
            conn.close()
            
            # Update user stats
            self.update_user_stats(user_id)
            
            logger.info(f"Added preference for user {user_id}: {action} {anime_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add user preference: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: str, action: Optional[str] = None) -> List[Dict]:
        """Get user preferences, optionally filtered by action"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if action:
                cursor.execute('''
                    SELECT * FROM user_preferences 
                    WHERE user_id = ? AND action = ?
                    ORDER BY timestamp DESC
                ''', (user_id, action))
            else:
                cursor.execute('''
                    SELECT * FROM user_preferences 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                ''', (user_id,))
            
            columns = [desc[0] for desc in cursor.description]
            preferences = []
            
            for row in cursor.fetchall():
                pref = dict(zip(columns, row))
                if pref['genres']:
                    pref['genres'] = json.loads(pref['genres'])
                preferences.append(pref)
            
            conn.close()
            return preferences
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {str(e)}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                # Create default stats
                default_stats = {
                    'total_ratings': 0,
                    'average_rating': 0,
                    'favorite_genres': [],
                    'total_favorites': 0,
                    'total_watchlist': 0,
                    'recommendation_accuracy': 0
                }
                self.update_user_stats(user_id)
                conn.close()
                return default_stats
            
            columns = [desc[0] for desc in cursor.description]
            stats = dict(zip(columns, result))
            
            if stats['favorite_genres']:
                stats['favorite_genres'] = json.loads(stats['favorite_genres'])
            else:
                stats['favorite_genres'] = []
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {str(e)}")
            return {}
    
    def update_user_stats(self, user_id: str):
        """Update calculated user statistics"""
        try:
            preferences = self.get_user_preferences(user_id)
            
            # Calculate stats
            ratings = [p for p in preferences if p['action'] == 'rating' and p['value']]
            likes = [p for p in preferences if p['action'] == 'like']
            
            total_ratings = len(ratings)
            average_rating = sum(r['value'] for r in ratings) / total_ratings if ratings else 0
            total_favorites = len(likes)
            
            # Calculate favorite genres
            all_genres = []
            for pref in preferences:
                if pref.get('genres'):
                    all_genres.extend(pref['genres'])
            
            genre_counts = {}
            for genre in all_genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            favorite_genres = [genre for genre, count in favorite_genres]
            
            # Update database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_stats 
                (user_id, total_ratings, average_rating, favorite_genres, total_favorites, total_watchlist, recommendation_accuracy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                total_ratings,
                average_rating,
                json.dumps(favorite_genres),
                total_favorites,
                0,  # total_watchlist - not implemented yet
                85.3  # recommendation_accuracy - mock value
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update user stats: {str(e)}")
    
    def get_recent_activity(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent user activity"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT anime_name, action, value, timestamp, genres
                FROM user_preferences 
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            
            activities = []
            for row in cursor.fetchall():
                activity = {
                    'anime_name': row[0],
                    'action': row[1],
                    'value': row[2],
                    'timestamp': row[3],
                    'genres': json.loads(row[4]) if row[4] else []
                }
                activities.append(activity)
            
            conn.close()
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {str(e)}")
            return []

# Initialize user service
user_service = UserService()