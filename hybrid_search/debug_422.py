import requests
import json

BASE_URL = "http://localhost:8000"

def test_malformed_requests():
    """Test requests that should trigger 422 errors"""
    print("🔍 Testing malformed requests that should trigger 422...")
    
    # Test 1: Invalid JSON
    try:
        response1 = requests.post(f"{BASE_URL}/search", data="invalid json", headers={"Content-Type": "application/json"})
        print(f"Invalid JSON - Status: {response1.status_code}")
        if response1.status_code == 422:
            print(f"Error: {response1.json()}")
    except Exception as e:
        print(f"Invalid JSON - Exception: {e}")
    
    # Test 2: Missing Content-Type
    payload2 = {"query": "test", "index_name": "test"}
    response2 = requests.post(f"{BASE_URL}/search", data=json.dumps(payload2))
    print(f"Missing Content-Type - Status: {response2.status_code}")
    if response2.status_code == 422:
        print(f"Error: {response2.json()}")
    
    # Test 3: Wrong data type for num_results
    payload3 = {
        "query": "test",
        "index_name": "test",
        "num_results": "not_a_number"
    }
    response3 = requests.post(f"{BASE_URL}/search", json=payload3)
    print(f"Wrong data type - Status: {response3.status_code}")
    if response3.status_code == 422:
        print(f"Error: {response3.json()}")

def test_authenticated_malformed():
    """Test malformed requests with authentication"""
    print("\n🔍 Testing authenticated malformed requests...")
    
    # First login to get a token
    login_data = {
        "username": "testuser2",
        "password": "testpassword123"
    }
    login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        # Test with missing required field
        payload = {
            "query": "test"
            # Missing index_name
        }
        response = requests.post(f"{BASE_URL}/search", json=payload, headers=headers)
        print(f"Missing index_name (authenticated) - Status: {response.status_code}")
        if response.status_code == 422:
            print(f"Error: {response.json()}")
    else:
        print("Could not login to test authenticated requests")

if __name__ == "__main__":
    test_malformed_requests()
    test_authenticated_malformed() 