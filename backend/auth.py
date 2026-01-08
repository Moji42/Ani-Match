# backend/auth.py
from dotenv import load_dotenv
load_dotenv()  # ensure .env is loaded before any os.getenv calls

import os
import jwt
import requests
from functools import wraps
from flask import request, jsonify, redirect
from urllib.parse import urlencode
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Supabase configuration (be tolerant of alternate env var names)
SUPABASE_URL = os.getenv('SUPABASE_URL')
# accept either SUPABASE_JWT_SECRET or JWT_SECRET_KEY
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET') or os.getenv('JWT_SECRET_KEY')
# accept either SUPABASE_SERVICE_KEY or SUPABASE_KEY
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')
GITHUB_REDIRECT_URI = os.getenv('GITHUB_REDIRECT_URI') or os.getenv('GITHUB_CALLBACK') or 'http://127.0.0.1:5000/auth/callback/github'

# Initialize Supabase client only if credentials exist
supabase: Client = None
if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Supabase client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}", exc_info=True)
else:
    logger.warning("Supabase credentials not fully set - supabase client NOT initialized")

def verify_supabase_token(token):
    """Verify Supabase JWT token and extract user info"""
    try:
        if not token:
            return None

        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]

        # For development, if JWT secret is not set, use a simple fallback
        if not SUPABASE_JWT_SECRET:
            logger.warning("SUPABASE_JWT_SECRET/JWT_SECRET_KEY not set, using development fallback")
            # Extract user ID from token (assuming it's formatted as user_id) — fallback only
            return {'sub': token, 'email': f'user-{token}@example.com'}

        # Decode and verify the JWT token using the configured secret
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=['HS256'],
            audience="authenticated",
            options={"verify_aud": False}  # flexibility for tokens without aud
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

        # Attach user info to the request object
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

def github_auth():
    """Initialize GitHub OAuth flow (fallback direct GitHub URL if needed)"""
    try:
        redirect_url = request.args.get('redirect_to', 'http://localhost:8080')

        params = {
            'client_id': GITHUB_CLIENT_ID,
            'redirect_uri': GITHUB_REDIRECT_URI,
            'scope': 'user:email',
            'state': redirect_url
        }
        github_oauth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
        logger.info(f"Redirecting to GitHub OAuth: {github_oauth_url}")
        return redirect(github_oauth_url)

    except Exception as e:
        logger.error(f"GitHub OAuth initiation error: {str(e)}")
        return jsonify({"error": "GitHub OAuth initialization failed"}), 500

def github_oauth_callback():
    """Handle GitHub OAuth callback (manual flow)"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        error = request.args.get('error')

        logger.info(f"GitHub callback received - code: {code}, state: {state}, error: {error}")

        if error:
            logger.error(f"GitHub OAuth error: {error}")
            return jsonify({"error": f"GitHub OAuth failed: {error}"}), 400

        if not code:
            logger.error("No authorization code received from GitHub")
            return jsonify({"error": "Authorization code not received"}), 400

        # Exchange code for access token
        token_response = requests.post(
            'https://github.com/login/oauth/access_token',
            headers={'Accept': 'application/json'},
            data={
                'client_id': GITHUB_CLIENT_ID,
                'client_secret': GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': GITHUB_REDIRECT_URI
            },
            timeout=30
        )

        if not token_response.ok:
            logger.error(f"Failed to get access token from GitHub: {token_response.status_code} - {token_response.text}")
            return jsonify({"error": "Failed to get access token from GitHub"}), 400

        token_data = token_response.json()
        access_token = token_data.get('access_token')

        if not access_token:
            logger.error("No access token received from GitHub response")
            return jsonify({"error": "No access token received from GitHub"}), 400

        # Get user info from GitHub
        user_response = requests.get(
            'https://api.github.com/user',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            },
            timeout=30
        )

        if not user_response.ok:
            logger.error(f"Failed to get user info from GitHub: {user_response.status_code} - {user_response.text}")
            return jsonify({"error": "Failed to get user info from GitHub"}), 400

        user_data = user_response.json()

        # Get user email
        email_response = requests.get(
            'https://api.github.com/user/emails',
            headers={
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json'
            },
            timeout=30
        )

        email_data = email_response.json() if email_response.ok else []
        primary_email = next((email['email'] for email in email_data if email.get('primary') and email.get('verified')),
                             user_data.get('email'))

        if not primary_email:
            logger.error("No primary email found for GitHub user")
            verified_email = next((email['email'] for email in email_data if email.get('verified')), None)
            if not verified_email:
                return jsonify({"error": "Could not retrieve verified email from GitHub"}), 400
            primary_email = verified_email

        user_id = f"github_{user_data['id']}"

        # create_access_token imported at runtime to avoid a circular import if needed
        from flask_jwt_extended import create_access_token
        jwt_token = create_access_token(identity=user_id)

        # Return HTML that sends data back to parent window
        response_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitHub Authentication Successful</title>
            <script>
                const authData = {{
                    access_token: '{jwt_token}',
                    user_id: '{user_id}',
                    email: '{primary_email}',
                    provider: 'github'
                }};
                window.opener.postMessage({{
                    type: 'OAUTH_SUCCESS',
                    data: authData
                }}, '*');
                setTimeout(() => window.close(), 1000);
            </script>
        </head>
        <body>
            <div style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>GitHub Authentication Successful!</h2>
                <p>Welcome, {primary_email}!</p>
                <p>You can close this window now.</p>
            </div>
        </body>
        </html>
        """
        return response_html

    except requests.Timeout:
        logger.error("GitHub OAuth request timed out")
        return jsonify({"error": "GitHub OAuth request timed out"}), 504
    except requests.RequestException as e:
        logger.error(f"GitHub OAuth network error: {str(e)}")
        return jsonify({"error": "Network error during GitHub OAuth"}), 503
    except Exception as e:
        logger.error(f"GitHub OAuth callback error: {str(e)}", exc_info=True)
        return jsonify({"error": f"GitHub OAuth callback failed: {str(e)}"}), 500

def debug_github_config():
    """Debug endpoint to check GitHub OAuth configuration"""
    return jsonify({
        "github_client_id": GITHUB_CLIENT_ID if GITHUB_CLIENT_ID else "NOT SET",
        "github_client_secret": "SET" if GITHUB_CLIENT_SECRET else "NOT SET",
        "github_redirect_uri": GITHUB_REDIRECT_URI,
        "github_configured": bool(GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET),
        "note": "Make sure GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET are set in your .env file"
    })

# user service helpers (unchanged - simple mocks)
def add_user_preference(user_id: str, anime_name: str, action: str, value: float = None, genres: list = None):
    try:
        logger.info(f"User {user_id} {action} {anime_name} with value {value}")
        return True
    except Exception as e:
        logger.error(f"Failed to add user preference: {str(e)}")
        return False

def get_user_preferences(user_id: str, action: str = None):
    try:
        return []
    except Exception as e:
        logger.error(f"Failed to get user preferences: {str(e)}")
        return []

def get_user_stats(user_id: str):
    try:
        return {
            'total_ratings': 0,
            'average_rating': 0,
            'favorite_genres': [],
            'total_favorites': 0,
            'total_watchlist': 0,
            'recommendation_accuracy': 0
        }
    except Exception as e:
        logger.error(f"Failed to get user stats: {str(e)}")
        return {}
