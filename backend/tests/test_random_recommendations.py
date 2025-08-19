# test_random_recommendations.py
import requests
import json
import sys
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"  # Changed from localhost to 127.0.0.1

def debug_print_response(response):
    """Helper function to print response details"""
    print(f"\nResponse Details:")
    print(f"URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print("Headers:")
    for k, v in response.headers.items():
        print(f"  {k}: {v}")
    print("Body Preview:", response.text[:200] + ("..." if len(response.text) > 200 else ""))

def test_random_endpoint():
    print("=== Testing Random Recommendations Endpoint ===")
    
    try:
        # Test 0: Server connectivity
        print("\n[0] Testing server health endpoint...")
        try:
            health_url = urljoin(BASE_URL, "/health")
            response = requests.get(health_url, timeout=2)
            debug_print_response(response)
            response.raise_for_status()
            print("✓ Server is responding")
        except requests.RequestException as e:
            print(f"✗ Connection failed: {str(e)}")
            print("Please ensure:")
            print("1. The Flask server is running")
            print("2. The server is accessible at", BASE_URL)
            print("3. No firewall is blocking port 5000")
            sys.exit(1)

        # Test 1: Default recommendations
        print("\n[1] Testing default recommendations...")
        try:
            url = urljoin(BASE_URL, "/recommend/random")
            response = requests.get(url, timeout=5)
            debug_print_response(response)
            response.raise_for_status()
            
            data = response.json()
            if not isinstance(data, list):
                raise ValueError("Response is not a list")
                
            print(f"✓ Received {len(data)} recommendations")
            print("First item structure:", json.dumps({k: type(v).__name__ for k, v in data[0].items()}, indent=2))
            
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            sys.exit(1)

        # Test 2: Specific count
        print("\n[2] Testing specific count parameter...")
        try:
            url = urljoin(BASE_URL, "/recommend/random?n=3")
            response = requests.get(url, timeout=5)
            debug_print_response(response)
            response.raise_for_status()
            
            data = response.json()
            if len(data) != 3:
                raise ValueError(f"Expected 3 items, got {len(data)}")
                
            print("✓ Received exactly 3 recommendations")
            
        except Exception as e:
            print(f"✗ Test failed: {str(e)}")
            sys.exit(1)

        print("\n=== All tests passed successfully ===")

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)

if __name__ == "__main__":
    test_random_endpoint()