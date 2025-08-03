from flask import Flask, request, jsonify
from content_based import load_and_preprocess_data, build_similarity_matrix, get_recommendations
import os

app = Flask(__name__)


# Will load the data and similarity matrix upon startup
data_path = os.path.join(os.path.dirname(__file__), '../data/anime_clean.csv')
df, features = load_and_preprocess_data(data_path)
similarity_matrix = build_similarity_matrix(features)


@app.route('/recommend/content', methods=['GET'])
def content_based():
    title = request.args.get('title',default = '', type = str)
    n = request.args.get('n', default=5, type = int)

    if not title:
        return jsonify({"error": "Title parameter is required"}), 400

    recommendations = get_recommendations(title,df,similarity_matrix,n)
    return jsonify(recommendations.to_dict('records'))
    
@app.route('/recommend/collab',methods=['GET'])
def collab_based():
    user_id = request.args.get('user_id', type = int)
    n =  request.args.get('n', default = 5, type = int)

    if user_id is None:
        return jsonify({"error": "user_id parameter is required"}), 400
    
    return jsonify({
        "status": "PLACEHOLDER",
        "message": "Collaborative filtering coming soon!",
        "expected_request": {
            "user_id": user_id,
            "n_recommendations": n
        }
    })
@app.route('/recommend/hybrid', methods=['GET'])
def hybrid_based():
    title = request.args.get('title', default='', type=str)
    user_id = request.args.get('user_id', type=int)
    n = request.args.get('n', default=5, type=int)

    if not title or user_id is None:
        return jsonify({
            "error": "Both title and user_id are required",
            "example_request": "/recommend/hybrid?title=Naruto&user_id=123&n=5"
        }), 400
    
    return jsonify({
        "status": "PLACEHOLDER",
        "message": "Hybrid recommendations coming soon!",
        "expected_behavior": "Will combine content-based and collaborative filtering",
        "parameters_received": {
            "title": title,
            "user_id": user_id,
            "n_recommendations": n
        },
        "mock_response": {
            "content_based": f"5 recommendations based on '{title}'",
            "collaborative": f"5 recommendations for user {user_id}",
            "hybrid": "Combined and ranked results"
        }
    })


if __name__ == '__main__':
    app.run(debug=True,port = 5000)
