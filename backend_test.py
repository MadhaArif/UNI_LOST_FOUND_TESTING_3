import requests
import json
import unittest
import random
import string
import os
import traceback
from datetime import datetime

# Get the backend URL from environment or use default
BACKEND_URL = "http://localhost:8001"

def run_test(func):
    """Decorator to run a test function and print results"""
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
            print(f"✅ {func.__doc__}")
            return True
        except Exception as e:
            print(f"❌ {func.__doc__}")
            print(f"   Error: {str(e)}")
            traceback.print_exc()
            return False
    return wrapper

class UMTBelongingsHubTester:
    """Test suite for UMT Belongings Hub FastAPI backend"""
    
    def __init__(self):
        """Setup for tests - generate random data for testing"""
        # Generate random user data for testing
        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.test_user = {
            "firstName": "Test",
            "lastName": "User",
            "email": f"test.user.{random_str}@university.edu",
            "password": "SecurePassword123!"
        }
        self.test_login = {
            "email": self.test_user["email"],
            "password": self.test_user["password"]
        }
        self.auth_token = None
        
        # Test post data
        self.test_lost_post = {
            "title": "Lost MacBook Pro",
            "description": "Silver MacBook Pro 16-inch with stickers on the cover. Last seen in the University Library.",
            "category": "Electronics",
            "location": "University Library",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "lost",
            "image_base64": None
        }
        
        self.test_found_post = {
            "title": "Found Student ID Card",
            "description": "Found a student ID card near the Student Union Building.",
            "category": "Documents",
            "location": "Student Union",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "found",
            "image_base64": None
        }
        
        # Store created post IDs for cleanup
        self.created_post_ids = []
    
    @run_test
    def test_health_check(self):
        """Health check endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/health")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy", f"Expected status 'healthy', got {data['status']}"
    
    @run_test
    def test_html_page_serving(self):
        """HTML page serving endpoints"""
        # Test index page
        response = requests.get(f"{BACKEND_URL}/")
        assert response.status_code == 200, f"Index page: Expected status code 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Index page: Expected HTML content type"
        
        # Test lost page
        response = requests.get(f"{BACKEND_URL}/lost")
        assert response.status_code == 200, f"Lost page: Expected status code 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Lost page: Expected HTML content type"
        
        # Test found page
        response = requests.get(f"{BACKEND_URL}/found")
        assert response.status_code == 200, f"Found page: Expected status code 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Found page: Expected HTML content type"
        
        # Test dashboard page
        response = requests.get(f"{BACKEND_URL}/dashboard")
        assert response.status_code == 200, f"Dashboard page: Expected status code 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Dashboard page: Expected HTML content type"
        
        # Test admin page
        response = requests.get(f"{BACKEND_URL}/admin")
        assert response.status_code == 200, f"Admin page: Expected status code 200, got {response.status_code}"
        assert "text/html" in response.headers.get("content-type", ""), "Admin page: Expected HTML content type"
    
    @run_test
    def test_user_registration(self):
        """User registration endpoint"""
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json=self.test_user
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "token" in data, "Response missing token"
        assert "user" in data, "Response missing user data"
        assert data["user"]["email"] == self.test_user["email"], f"Email mismatch: {data['user']['email']} != {self.test_user['email']}"
        
        # Save token for subsequent tests
        self.auth_token = data["token"]
    
    @run_test
    def test_user_login(self):
        """User login endpoint"""
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=self.test_login
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "token" in data, "Response missing token"
        assert "user" in data, "Response missing user data"
        assert data["user"]["email"] == self.test_user["email"], f"Email mismatch: {data['user']['email']} != {self.test_user['email']}"
        
        # Update token
        self.auth_token = data["token"]
    
    @run_test
    def test_get_current_user(self):
        """Get current user endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/auth/me",
            headers=headers
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["email"] == self.test_user["email"], f"Email mismatch: {data['email']} != {self.test_user['email']}"
    
    @run_test
    def test_create_lost_post(self):
        """Create lost post endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.post(
            f"{BACKEND_URL}/api/posts",
            json=self.test_lost_post,
            headers=headers
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["title"] == self.test_lost_post["title"], f"Title mismatch: {data['title']} != {self.test_lost_post['title']}"
        assert data["type"] == "lost", f"Type mismatch: {data['type']} != lost"
        
        # Save post ID for later tests
        self.created_post_ids.append(data["_id"])
    
    @run_test
    def test_create_found_post(self):
        """Create found post endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.post(
            f"{BACKEND_URL}/api/posts",
            json=self.test_found_post,
            headers=headers
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["title"] == self.test_found_post["title"], f"Title mismatch: {data['title']} != {self.test_found_post['title']}"
        assert data["type"] == "found", f"Type mismatch: {data['type']} != found"
        
        # Save post ID for later tests
        self.created_post_ids.append(data["_id"])
    
    @run_test
    def test_get_all_posts(self):
        """Get all posts endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/posts")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Expected list response, got {type(data)}"
        
        # Verify our created posts are in the list
        post_ids = [post["_id"] for post in data]
        for post_id in self.created_post_ids:
            assert post_id in post_ids, f"Created post {post_id} not found in response"
    
    @run_test
    def test_get_filtered_posts(self):
        """Get filtered posts endpoint"""
        # Test filtering by type
        response = requests.get(f"{BACKEND_URL}/api/posts?type=lost")
        assert response.status_code == 200, f"Type filter: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Type filter: Expected list response, got {type(data)}"
        for post in data:
            assert post["type"] == "lost", f"Type filter: Found post with type {post['type']}, expected 'lost'"
        
        # Test filtering by category
        response = requests.get(f"{BACKEND_URL}/api/posts?category=Electronics")
        assert response.status_code == 200, f"Category filter: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Category filter: Expected list response, got {type(data)}"
        
        # Test filtering by location
        response = requests.get(f"{BACKEND_URL}/api/posts?location=University Library")
        assert response.status_code == 200, f"Location filter: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), f"Location filter: Expected list response, got {type(data)}"
    
    @run_test
    def test_get_specific_post(self):
        """Get specific post endpoint"""
        if not self.created_post_ids:
            print("   Skipping: No posts created to test with")
            return
        
        post_id = self.created_post_ids[0]
        response = requests.get(f"{BACKEND_URL}/api/posts/{post_id}")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["_id"] == post_id, f"ID mismatch: {data['_id']} != {post_id}"
    
    @run_test
    def test_invalid_registration(self):
        """Registration validation"""
        # Test with non-university email
        invalid_user = self.test_user.copy()
        invalid_user["email"] = "test@gmail.com"
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json=invalid_user
        )
        assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Response missing error detail"
    
    @run_test
    def test_invalid_login(self):
        """Login validation"""
        invalid_login = {
            "email": self.test_user["email"],
            "password": "WrongPassword123"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=invalid_login
        )
        assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Response missing error detail"
    
    @run_test
    def test_unauthorized_access(self):
        """Authentication protection"""
        # Try to create a post without authentication
        response = requests.post(
            f"{BACKEND_URL}/api/posts",
            json=self.test_lost_post
        )
        assert response.status_code != 200, f"Expected non-200 status code, got {response.status_code}"
        
        # Try to access user info without authentication
        response = requests.get(f"{BACKEND_URL}/api/auth/me")
        assert response.status_code != 200, f"Expected non-200 status code, got {response.status_code}"

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🔍 TESTING UMT BELONGINGS HUB BACKEND API 🔍\n")
    
    tester = UMTBelongingsHubTester()
    
    # Run tests in sequence
    tests = [
        tester.test_health_check,
        tester.test_html_page_serving,
        tester.test_user_registration,
        tester.test_user_login,
        tester.test_get_current_user,
        tester.test_create_lost_post,
        tester.test_create_found_post,
        tester.test_get_all_posts,
        tester.test_get_filtered_posts,
        tester.test_get_specific_post,
        tester.test_invalid_registration,
        tester.test_invalid_login,
        tester.test_unauthorized_access
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    # Print summary
    print("\n📊 TEST SUMMARY 📊")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {results.count(True)}")
    print(f"Failed: {results.count(False)}")
    
    return results.count(True) == len(tests)

if __name__ == "__main__":
    run_all_tests()