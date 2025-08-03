from flask import Flask, request, jsonify
from content_based import load_and_preprocess_data, build_similarity_matrix, get_recommendations
import pandas as pd
from surprise import Dataset, Reader, SVD
import pickle
import os

app = Flask(__name__)

# Configuration
CONFIG = {
    'content_weight': 0.6,
    'collab_weight': 0.4,
    'top_n_hybrid': 10,
    'default_recommendations': 5
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

# Load data and similarity matrix
df, features = load_and_preprocess_data(data_path)
similarity_matrix = build_similarity_matrix(features)

def get_collab_recommendations(user_id, model, anime_df, n=5):

    all_anime_ids = anime_df['anime_id'].unique()
    user_predictions = []
    
    for anime_id in all_anime_ids:
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
            'Predicted Rating': f"{rating:.2f}",
            'Genres': anime['genre']
        })
    
    return recommendations

# Load or train collaborative model
try:
    collab_model = pickle.load(open('collab_model.pkl', 'rb'))
except (FileNotFoundError, EOFError):
    print("Training new collaborative model...")
    reader = Reader(rating_scale=(1, 10))
    data = Dataset.load_from_df(pd.read_csv(ratings_path)[['user_id', 'anime_id', 'rating']], reader)
    trainset = data.build_full_trainset()
    collab_model = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02)
    collab_model.fit(trainset)
    pickle.dump(collab_model, open('collab_model.pkl', 'wb'))

@app.route('/recommend/content', methods=['GET'])
def content_based():
    title = request.args.get('title', default='', type=str)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)

    if not title:
        return jsonify({"error": "Title parameter is required"}), 400

    recommendations = get_recommendations(title, df, similarity_matrix, n)
    return jsonify(recommendations.to_dict('records'))

@app.route('/recommend/collab', methods=['GET'])
def collab_based():

    user_id = request.args.get('user_id', type=int)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)

    if user_id is None:
        return jsonify({"error": "user_id parameter is required"}), 400
    
    recommendations = get_collab_recommendations(user_id, collab_model, df, n)
    return jsonify(recommendations)

@app.route('/recommend/hybrid', methods=['GET'])
def hybrid_based():
    title = request.args.get('title', default='', type=str)
    user_id = request.args.get('user_id', type=int)
    n = request.args.get('n', default=CONFIG['default_recommendations'], type=int)

    if not title or user_id is None:
        return jsonify({"error": "Both title and user_id are required"}), 400
    
    # Get recommendations from both methods
    content_recs = get_recommendations(title, df, similarity_matrix, n)
    collab_recs = get_collab_recommendations(user_id, collab_model, df, n)
    
    # Convert content_recs to dict list
    content_list = content_recs.to_dict('records')
    
    # Get hybrid recommendations
    hybrid_list = merge_recommendations(content_list, collab_recs)
    
    return jsonify({
        'content_based': content_list,
        'collaborative': collab_recs,
        'hybrid': hybrid_list
    })

def merge_recommendations(content_recs, collab_recs):

    hybrid = []
    
    # Create combined recommendations
    for c_item in content_recs:
        for collab_item in collab_recs:
            if collab_item['Anime'] == c_item['Anime']:
                try:
                    content_score = float(c_item['Similarity Score'])
                    collab_score = float(collab_item['Predicted Rating']) / 10  # Normalize to 0-1
                    combined_score = (content_score * CONFIG['content_weight'] + 
                                    collab_score * CONFIG['collab_weight'])
                    
                    hybrid.append({
                        'Anime': c_item['Anime'],
                        'Genres': c_item['Genres'],
                        'Content_Score': f"{content_score:.2f}",
                        'Collab_Score': collab_item['Predicted Rating'],
                        'Combined_Score': f"{combined_score:.2f}",
                        'Method': 'hybrid'
                    })
                except (KeyError, ValueError) as e:
                    print(f"Error processing item: {e}")
                    continue
    
    # Sort by combined score
    hybrid.sort(key=lambda x: float(x['Combined_Score']), reverse=True)
    
    return hybrid[:CONFIG['top_n_hybrid']]

if __name__ == '__main__':
    app.run(debug=True, port=5000)