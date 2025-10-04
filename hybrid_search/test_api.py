# test_api.py
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def register_user():
    """Register a test user"""
    print("👤 Registering test user...")
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"Register Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ User registered successfully")
    else:
        print(f"❌ Registration failed: {response.json()}")
    print()

def login_user():
    """Login and get access token"""
    print("🔐 Logging in...")
    login_data = {
        "username": "testuser2",
        "password": "testpassword123"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print("✅ Login successful")
        return token_data["access_token"]
    else:
        print(f"❌ Login failed: {response.json()}")
        return None

def test_search_with_auth(token):
    """Test search endpoint with authentication"""
    print("🔍 Testing search endpoint with authentication...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with minimal required fields
    payload = {
        "query": "What is machine learning?",
        "index_name": "passage_index"
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{BASE_URL}/search", json=payload, headers=headers)
    print(f"Search Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Search successful")
        result = response.json()
        print(f"Query: {result.get('query')}")
        print(f"Answer: {result.get('answer')}")
        print(f"Method: {result.get('method')}")
        print(f"Error: {result.get('error')}")
    else:
        print(f"❌ Search failed: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Error text: {response.text}")
    print()

def test_search_with_full_payload(token):
    """Test search endpoint with full payload"""
    print("🔍 Testing search endpoint with full payload...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test with all fields
    payload = {
        "query": "What is machine learning?",
        "index_name": "passage_index",
        "search_method": "multi_stage",
        "num_results": 5
    }
    
    print(f"Sending payload: {json.dumps(payload, indent=2)}")
    response = requests.post(f"{BASE_URL}/search", json=payload, headers=headers)
    print(f"Search Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Search successful")
        result = response.json()
        print(f"Query: {result.get('query')}")
        print(f"Answer: {result.get('answer')}")
        print(f"Method: {result.get('method')}")
        print(f"Error: {result.get('error')}")
    else:
        print(f"❌ Search failed: {response.status_code}")
        try:
            error_detail = response.json()
            print(f"Error details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"Error text: {response.text}")
    print()

def test_search_without_auth():
    """Test search endpoint without authentication (should fail)"""
    print("🔍 Testing search endpoint without authentication...")
    
    payload = {
        "query": "What is machine learning?",
        "index_name": "passage_index",
        "num_results": 5
    }
    
    response = requests.post(f"{BASE_URL}/search", json=payload)
    print(f"Search Status: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected unauthorized request")
    else:
        print(f"❌ Unexpected response: {response.status_code}")
        print(f"Response: {response.text}")
    print()

def main():
    """Run all tests"""
    print("🚀 Starting API Tests")
    print("=" * 50)
    
    # Test health endpoint
    test_health()
    
    # Test search without auth (should fail)
    test_search_without_auth()
    
    # Register and login
    register_user()
    token = login_user()
    
    if token:
        # Test search with minimal payload
        test_search_with_auth(token)
        
        # Test search with full payload
        test_search_with_full_payload(token)
    else:
        print("❌ Cannot test search - no valid token")
    
    print("🏁 Tests completed")

if __name__ == "__main__":
    main()