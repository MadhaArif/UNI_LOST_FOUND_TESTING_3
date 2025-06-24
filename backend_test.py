import requests
import json
import unittest
import random
import string
import os
from datetime import datetime

# Get the backend URL from environment or use default
BACKEND_URL = "http://localhost:8001"

class UMTBelongingsHubBackendTest(unittest.TestCase):
    """Test suite for UMT Belongings Hub FastAPI backend"""
    
    def setUp(self):
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
    
    def test_01_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("✅ Health check endpoint is working")
    
    def test_02_html_page_serving(self):
        """Test HTML page serving endpoints"""
        # Test index page
        response = requests.get(f"{BACKEND_URL}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        
        # Test lost page
        response = requests.get(f"{BACKEND_URL}/lost")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        
        # Test found page
        response = requests.get(f"{BACKEND_URL}/found")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        
        # Test dashboard page
        response = requests.get(f"{BACKEND_URL}/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        
        # Test admin page
        response = requests.get(f"{BACKEND_URL}/admin")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        
        print("✅ HTML page serving endpoints are working")
    
    def test_03_user_registration(self):
        """Test user registration endpoint"""
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json=self.test_user
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_user["email"])
        self.assertEqual(data["user"]["firstName"], self.test_user["firstName"])
        self.assertEqual(data["user"]["lastName"], self.test_user["lastName"])
        
        # Save token for subsequent tests
        self.auth_token = data["token"]
        print("✅ User registration endpoint is working")
    
    def test_04_user_login(self):
        """Test user login endpoint"""
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=self.test_login
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_user["email"])
        
        # Update token
        self.auth_token = data["token"]
        print("✅ User login endpoint is working")
    
    def test_05_get_current_user(self):
        """Test get current user endpoint"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/auth/me",
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user["email"])
        self.assertEqual(data["firstName"], self.test_user["firstName"])
        self.assertEqual(data["lastName"], self.test_user["lastName"])
        print("✅ Get current user endpoint is working")
    
    def test_06_create_lost_post(self):
        """Test creating a lost post"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.post(
            f"{BACKEND_URL}/api/posts",
            json=self.test_lost_post,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], self.test_lost_post["title"])
        self.assertEqual(data["type"], "lost")
        
        # Save post ID for later tests
        self.created_post_ids.append(data["_id"])
        print("✅ Create lost post endpoint is working")
    
    def test_07_create_found_post(self):
        """Test creating a found post"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = requests.post(
            f"{BACKEND_URL}/api/posts",
            json=self.test_found_post,
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], self.test_found_post["title"])
        self.assertEqual(data["type"], "found")
        
        # Save post ID for later tests
        self.created_post_ids.append(data["_id"])
        print("✅ Create found post endpoint is working")
    
    def test_08_get_all_posts(self):
        """Test getting all posts"""
        response = requests.get(f"{BACKEND_URL}/api/posts")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        # Verify our created posts are in the list
        post_ids = [post["_id"] for post in data]
        for post_id in self.created_post_ids:
            self.assertIn(post_id, post_ids)
        print("✅ Get all posts endpoint is working")
    
    def test_09_get_filtered_posts(self):
        """Test getting filtered posts"""
        # Test filtering by type
        response = requests.get(f"{BACKEND_URL}/api/posts?type=lost")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        for post in data:
            self.assertEqual(post["type"], "lost")
        
        # Test filtering by category
        response = requests.get(f"{BACKEND_URL}/api/posts?category=Electronics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        for post in data:
            self.assertEqual(post["category"], "Electronics")
        
        # Test filtering by location
        response = requests.get(f"{BACKEND_URL}/api/posts?location=University Library")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        for post in data:
            self.assertEqual(post["location"], "University Library")
        
        print("✅ Get filtered posts endpoint is working")
    
    def test_10_get_specific_post(self):
        """Test getting a specific post by ID"""
        if not self.created_post_ids:
            self.skipTest("No posts created to test with")
        
        post_id = self.created_post_ids[0]
        response = requests.get(f"{BACKEND_URL}/api/posts/{post_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["_id"], post_id)
        print("✅ Get specific post endpoint is working")
    
    def test_11_invalid_registration(self):
        """Test registration with invalid data"""
        # Test with non-university email
        invalid_user = self.test_user.copy()
        invalid_user["email"] = "test@gmail.com"
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/register",
            json=invalid_user
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        print("✅ Registration validation is working")
    
    def test_12_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_login = {
            "email": self.test_user["email"],
            "password": "WrongPassword123"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=invalid_login
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        print("✅ Login validation is working")
    
    def test_13_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        # Try to create a post without authentication
        response = requests.post(
            f"{BACKEND_URL}/api/posts",
            json=self.test_lost_post
        )
        self.assertNotEqual(response.status_code, 200)
        
        # Try to access user info without authentication
        response = requests.get(f"{BACKEND_URL}/api/auth/me")
        self.assertNotEqual(response.status_code, 200)
        
        print("✅ Authentication protection is working")

if __name__ == "__main__":
    # Run the tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(UMTBelongingsHubBackendTest('test_01_health_check'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_02_html_page_serving'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_03_user_registration'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_04_user_login'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_05_get_current_user'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_06_create_lost_post'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_07_create_found_post'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_08_get_all_posts'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_09_get_filtered_posts'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_10_get_specific_post'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_11_invalid_registration'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_12_invalid_login'))
    test_suite.addTest(UMTBelongingsHubBackendTest('test_13_unauthorized_access'))
    
    runner = unittest.TextTestRunner()
    runner.run(test_suite)