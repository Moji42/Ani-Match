
# backend/unit_tests.py
import requests
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:5000"
TEST_RESULTS = {
    "health_check": {},
    "content_based": {},
    "collab_based": {},
    "hybrid_based": {}
}

def make_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make HTTP request and return response data"""
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
        return {
            "status_code": response.status_code,
            "response": response.json(),
            "error": None
        }
    except Exception as e:
        return {
            "status_code": None,
            "response": None,
            "error": str(e)
        }

def test_health_check():
    """Test health check endpoint"""
    TEST_RESULTS["health_check"] = make_request("health", {})

def test_content_based():
    """Test content-based recommendation endpoint"""
    # Test cases
    test_cases = [
        {"title": "Naruto", "n": 5},  # Valid case
        {"title": "Narut", "n": 3},   # Fuzzy match
        {"title": "", "n": 5},         # Empty title
        {"title": "A", "n": 5},        # Too short title
        {"title": "Nonexistent Anime Title 12345", "n": 5},  # No match
        {"title": 12345, "n": 5},      # Invalid type
    ]
    
    for i, case in enumerate(test_cases):
        TEST_RESULTS["content_based"][f"case_{i+1}"] = {
            "params": case,
            "result": make_request("recommend/content", case)
        }

def test_collab_based():
    """Test collaborative filtering recommendation endpoint"""
    # Test cases
    test_cases = [
        {"user_id": 1, "n": 5},       # Valid case
        {"user_id": 999999, "n": 5},   # New user (should return popular)
        {"user_id": 0, "n": 5},        # Invalid user_id
        {"user_id": -1, "n": 5},       # Negative user_id
        {"user_id": "abc", "n": 5},    # Invalid type
        {"user_id": None, "n": 5},     # Missing user_id
    ]
    
    for i, case in enumerate(test_cases):
        TEST_RESULTS["collab_based"][f"case_{i+1}"] = {
            "params": case,
            "result": make_request("recommend/collab", case)
        }

def test_hybrid_based():
    """Test hybrid recommendation endpoint"""
    # Test cases
    test_cases = [
        {"title": "Naruto", "user_id": 1, "n": 5},    # Valid case
        {"title": "Narut", "user_id": 1, "n": 3},      # Fuzzy match
        {"title": "Naruto", "user_id": 999999, "n": 5},  # New user
        {"title": "", "user_id": 1, "n": 5},           # Empty title
        {"title": "Naruto", "user_id": 0, "n": 5},     # Invalid user_id
        {"title": 12345, "user_id": 1, "n": 5},        # Invalid title type
        {"title": "Naruto", "user_id": None, "n": 5},  # Missing user_id
        {"title": None, "user_id": 1, "n": 5},         # Missing title
    ]
    
    for i, case in enumerate(test_cases):
        TEST_RESULTS["hybrid_based"][f"case_{i+1}"] = {
            "params": case,
            "result": make_request("recommend/hybrid", case)
        }

def run_tests():
    """Run all test cases"""
    print("Running health check test...")
    test_health_check()
    
    print("Running content-based recommendation tests...")
    test_content_based()
    
    print("Running collaborative filtering recommendation tests...")
    test_collab_based()
    
    print("Running hybrid recommendation tests...")
    test_hybrid_based()
    
    # Save results to JSON file
    with open("backend_test_results.json", "w") as f:
        json.dump(TEST_RESULTS, f, indent=2)
    
    print("All tests completed. Results saved to backend_test_results.json")

if __name__ == "__main__":
    run_tests()