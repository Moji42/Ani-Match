#!/usr/bin/env python3
"""
Test script to verify persistence endpoints and Supabase connectivity.
"""
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"

# Step 1: Register and login
print("=" * 60)
print("STEP 1: Register or Login")
print("=" * 60)

test_email = "test@example.com"
test_password = "TestPassword123!"

# Try login first
login_payload = {
    "email": test_email,
    "password": test_password
}

print(f"\nAttempting login with {test_email}...")
response = requests.post(f"{BASE_URL}/auth/login", json=login_payload)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code != 200:
    print("\nLogin failed. Trying registration...")
    response = requests.post(f"{BASE_URL}/auth/register", json=login_payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code in [200, 201]:
    data = response.json()
    access_token = data.get('access_token')
    user_id = data.get('user_id')
    print(f"\n✓ Auth successful!")
    print(f"  User ID: {user_id}")
    print(f"  Token: {access_token[:30]}...")
else:
    print("\n✗ Auth failed!")
    exit(1)

# Step 2: Test GET favorites (should be empty)
print("\n" + "=" * 60)
print("STEP 2: GET favorites (should be empty)")
print("=" * 60)

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

response = requests.get(f"{BASE_URL}/user/favorites", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 3: Add favorite
print("\n" + "=" * 60)
print("STEP 3: POST favorite (add 'Naruto')")
print("=" * 60)

payload = {"anime": "Naruto"}
response = requests.post(f"{BASE_URL}/user/favorites", json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

if response.status_code == 201:
    print("✓ Add favorite successful!")
else:
    print("✗ Add favorite failed!")
    print("  (Check Flask logs for Supabase error details)")

# Step 4: GET favorites again (should contain Naruto)
print("\n" + "=" * 60)
print("STEP 4: GET favorites again (should have 'Naruto')")
print("=" * 60)

response = requests.get(f"{BASE_URL}/user/favorites", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 5: Add watchlist
print("\n" + "=" * 60)
print("STEP 5: POST watchlist (add 'One Piece')")
print("=" * 60)

payload = {"anime": "One Piece"}
response = requests.post(f"{BASE_URL}/user/watchlist", json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 6: Add preference (like)
print("\n" + "=" * 60)
print("STEP 6: POST preference (like 'Attack on Titan')")
print("=" * 60)

payload = {"anime": "Attack on Titan", "action": "like", "value": None}
response = requests.post(f"{BASE_URL}/user/preferences", json=payload, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Step 7: GET all preferences
print("\n" + "=" * 60)
print("STEP 7: GET all preferences")
print("=" * 60)

response = requests.get(f"{BASE_URL}/user/preferences", headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
