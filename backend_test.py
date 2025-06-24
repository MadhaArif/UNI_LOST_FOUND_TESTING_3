import requests
import json
import unittest
import random
import string
import base64
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

class UMTLostAndFoundTester:
    """Test suite for UMT Lost & Found FastAPI backend"""
    
    def __init__(self):
        """Setup for tests - generate random data for testing"""
        # Generate random data for testing
        random_str = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        # Test lost item data
        self.test_lost_item = {
            "title": "Lost MacBook Pro",
            "category": "Electronics",
            "description": "Silver MacBook Pro 16-inch with stickers on the cover. Last seen in the University Library.",
            "location": "University Library",
            "specificLocation": "Second floor, study area near window",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "image": None,  # Will be populated with base64 image if needed
            "ownerInfo": {
                "name": "John Smith",
                "email": f"john.smith.{random_str}@university.edu",
                "phone": "555-123-4567"
            },
            "offerReward": True,
            "rewardAmount": "50",
            "additionalNotes": "The laptop has a distinctive UMT sticker on the cover."
        }
        
        # Test found item data
        self.test_found_item = {
            "title": "Found Student ID Card",
            "category": "Documents",
            "description": "Found a student ID card for Jane Doe",
            "location": "Student Union",
            "specificLocation": "Near the coffee shop",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "image": None,  # Will be populated with base64 image if needed
            "finderInfo": {
                "name": "Bob Johnson",
                "email": f"bob.johnson.{random_str}@university.edu",
                "phone": "555-987-6543"
            },
            "additionalNotes": "The ID card was found on a table."
        }
        
        # Store created item IDs for cleanup
        self.created_lost_item_ids = []
        self.created_found_item_ids = []
        
        # Sample base64 image (1x1 pixel transparent PNG)
        self.sample_base64_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    
    @run_test
    def test_health_check(self):
        """Health check endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/health")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy", f"Expected status 'healthy', got {data['status']}"
    
    @run_test
    def test_root_api(self):
        """Root API endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "message" in data, "Response missing message field"
        assert "endpoints" in data, "Response missing endpoints information"
    
    @run_test
    def test_report_lost_item(self):
        """Report lost item endpoint"""
        # Add sample image to test data
        test_data = self.test_lost_item.copy()
        test_data["image"] = self.sample_base64_image
        
        response = requests.post(
            f"{BACKEND_URL}/api/items/lost",
            json=test_data
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, f"Expected success to be True, got {data['success']}"
        assert "item" in data, "Response missing item data"
        assert data["item"]["title"] == test_data["title"], f"Title mismatch: {data['item']['title']} != {test_data['title']}"
        
        # Save item ID for later tests
        self.created_lost_item_ids.append(data["item"]["id"])
    
    @run_test
    def test_report_found_item(self):
        """Report found item endpoint"""
        # Add sample image to test data
        test_data = self.test_found_item.copy()
        test_data["image"] = self.sample_base64_image
        
        response = requests.post(
            f"{BACKEND_URL}/api/items/found",
            json=test_data
        )
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, f"Expected success to be True, got {data['success']}"
        assert "item" in data, "Response missing item data"
        assert data["item"]["title"] == test_data["title"], f"Title mismatch: {data['item']['title']} != {test_data['title']}"
        
        # Save item ID for later tests
        self.created_found_item_ids.append(data["item"]["id"])
    
    @run_test
    def test_get_lost_items(self):
        """Get all lost items endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/items/lost")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, f"Expected success to be True, got {data['success']}"
        assert "items" in data, "Response missing items array"
        assert isinstance(data["items"], list), f"Expected items to be a list, got {type(data['items'])}"
        
        # Verify our created item is in the list
        if self.created_lost_item_ids:
            item_ids = [item["id"] for item in data["items"]]
            assert any(item_id in item_ids for item_id in self.created_lost_item_ids), "Created lost item not found in response"
    
    @run_test
    def test_get_found_items(self):
        """Get all found items endpoint"""
        response = requests.get(f"{BACKEND_URL}/api/items/found")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, f"Expected success to be True, got {data['success']}"
        assert "items" in data, "Response missing items array"
        assert isinstance(data["items"], list), f"Expected items to be a list, got {type(data['items'])}"
        
        # Verify our created item is in the list
        if self.created_found_item_ids:
            item_ids = [item["id"] for item in data["items"]]
            assert any(item_id in item_ids for item_id in self.created_found_item_ids), "Created found item not found in response"
    
    @run_test
    def test_get_specific_item(self):
        """Get specific item endpoint"""
        # Test getting a lost item
        if self.created_lost_item_ids:
            item_id = self.created_lost_item_ids[0]
            response = requests.get(f"{BACKEND_URL}/api/items/lost/{item_id}")
            assert response.status_code == 200, f"Lost item: Expected status code 200, got {response.status_code}"
            data = response.json()
            assert data["success"] is True, f"Lost item: Expected success to be True, got {data['success']}"
            assert data["item"]["id"] == item_id, f"Lost item: ID mismatch: {data['item']['id']} != {item_id}"
        
        # Test getting a found item
        if self.created_found_item_ids:
            item_id = self.created_found_item_ids[0]
            response = requests.get(f"{BACKEND_URL}/api/items/found/{item_id}")
            assert response.status_code == 200, f"Found item: Expected status code 200, got {response.status_code}"
            data = response.json()
            assert data["success"] is True, f"Found item: Expected success to be True, got {data['success']}"
            assert data["item"]["id"] == item_id, f"Found item: ID mismatch: {data['item']['id']} != {item_id}"
    
    @run_test
    def test_quick_search(self):
        """Quick search endpoint"""
        # Test searching for lost items
        search_data = {
            "searchType": "lost",
            "itemCategory": "Electronics",
            "location": "Library",
            "date": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"Lost search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Lost search: Response missing items array"
        assert "success" in data, "Lost search: Response missing success field"
        assert "message" in data, "Lost search: Response missing message field"
        
        # Test searching for found items
        search_data = {
            "searchType": "found",
            "itemCategory": "Documents",
            "location": "Student Union",
            "date": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"Found search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Found search: Response missing items array"
        assert "success" in data, "Found search: Response missing success field"
        assert "message" in data, "Found search: Response missing message field"
        
        # Test searching for both types
        search_data = {
            "searchType": "both",
            "itemCategory": None,
            "location": None,
            "date": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"Both search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Both search: Response missing items array"
        assert "success" in data, "Both search: Response missing success field"
        assert "message" in data, "Both search: Response missing message field"
        
        # Test with specific date
        today = datetime.now().strftime("%Y-%m-%d")
        search_data = {
            "searchType": "both",
            "itemCategory": None,
            "location": None,
            "date": today
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"Date search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Date search: Response missing items array"
        
        # Test with all parameters
        search_data = {
            "searchType": "lost",
            "itemCategory": "Electronics",
            "location": "Library",
            "date": today
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"All params search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "All params search: Response missing items array"
        
        # Test with empty search (no parameters)
        search_data = {
            "searchType": "both",
            "itemCategory": None,
            "location": None,
            "date": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"Empty search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Empty search: Response missing items array"
        
        # Test with invalid search type
        search_data = {
            "searchType": "invalid",
            "itemCategory": None,
            "location": None,
            "date": None
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/quick",
            json=search_data
        )
        assert response.status_code == 200, f"Invalid type search: Expected status code 200, got {response.status_code}"
        # The API should handle invalid search type gracefully
    
    @run_test
    def test_visual_search(self):
        """Visual search endpoint"""
        # Test with valid image and 'both' search type
        search_data = {
            "imageBase64": self.sample_base64_image,
            "searchType": "both"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/visual",
            json=search_data
        )
        assert response.status_code == 200, f"Valid image search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Valid image search: Response missing items array"
        assert "success" in data, "Valid image search: Response missing success field"
        assert "message" in data, "Valid image search: Response missing message field"
        
        # Test with 'lost' search type
        search_data = {
            "imageBase64": self.sample_base64_image,
            "searchType": "lost"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/visual",
            json=search_data
        )
        assert response.status_code == 200, f"Lost image search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Lost image search: Response missing items array"
        
        # Test with 'found' search type
        search_data = {
            "imageBase64": self.sample_base64_image,
            "searchType": "found"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/visual",
            json=search_data
        )
        assert response.status_code == 200, f"Found image search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert "items" in data, "Found image search: Response missing items array"
        
        # Test with invalid search type
        search_data = {
            "imageBase64": self.sample_base64_image,
            "searchType": "invalid"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/visual",
            json=search_data
        )
        assert response.status_code == 200, f"Invalid type image search: Expected status code 200, got {response.status_code}"
        # The API should handle invalid search type gracefully
        
        # Test with corrupted base64 image data
        search_data = {
            "imageBase64": "invalid-base64-data",
            "searchType": "both"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/visual",
            json=search_data
        )
        # The API should handle invalid base64 data gracefully
        # Either return a 400 error or a 200 with an error message
        assert response.status_code in [200, 400, 422], f"Invalid image data: Expected status code 200, 400, or 422, got {response.status_code}"
        
        # Test with empty image data
        search_data = {
            "imageBase64": "",
            "searchType": "both"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/api/search/visual",
            json=search_data
        )
        # The API should handle empty image data gracefully
        assert response.status_code in [200, 400, 422], f"Empty image data: Expected status code 200, 400, or 422, got {response.status_code}"
    
    @run_test
    def test_search_items(self):
        """Search items with filters endpoint"""
        # Test searching lost items
        response = requests.get(f"{BACKEND_URL}/api/search/items?item_type=lost&q=MacBook&category=Electronics&location=Library")
        assert response.status_code == 200, f"Lost search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, f"Lost search: Expected success to be True, got {data['success']}"
        assert "items" in data, "Lost search: Response missing items array"
        
        # Test searching found items
        response = requests.get(f"{BACKEND_URL}/api/search/items?item_type=found&q=ID&category=Documents")
        assert response.status_code == 200, f"Found search: Expected status code 200, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, f"Found search: Expected success to be True, got {data['success']}"
        assert "items" in data, "Found search: Response missing items array"
        
        # Test with invalid item type
        response = requests.get(f"{BACKEND_URL}/api/search/items?item_type=invalid")
        assert response.status_code == 400, f"Invalid type: Expected status code 400, got {response.status_code}"
    
    @run_test
    def test_data_validation(self):
        """Data validation for item submission"""
        # Test missing required field for lost item
        invalid_lost_item = self.test_lost_item.copy()
        del invalid_lost_item["title"]
        
        response = requests.post(
            f"{BACKEND_URL}/api/items/lost",
            json=invalid_lost_item
        )
        assert response.status_code == 422, f"Missing field: Expected status code 422, got {response.status_code}"
        
        # Test missing required field for found item
        invalid_found_item = self.test_found_item.copy()
        del invalid_found_item["location"]
        
        response = requests.post(
            f"{BACKEND_URL}/api/items/found",
            json=invalid_found_item
        )
        assert response.status_code == 422, f"Missing field: Expected status code 422, got {response.status_code}"
    
    @run_test
    def test_error_handling(self):
        """Error handling for invalid requests"""
        # Test invalid item ID
        response = requests.get(f"{BACKEND_URL}/api/items/lost/invalid-id")
        assert response.status_code in [404, 400], f"Invalid ID: Expected status code 404 or 400, got {response.status_code}"
        
        # Test invalid search parameters
        response = requests.get(f"{BACKEND_URL}/api/search/items?item_type=invalid")
        assert response.status_code == 400, f"Invalid search: Expected status code 400, got {response.status_code}"

def run_all_tests():
    """Run all tests in sequence"""
    print("\n🔍 TESTING UMT LOST & FOUND BACKEND API 🔍\n")
    
    tester = UMTLostAndFoundTester()
    
    # Run tests in sequence
    tests = [
        tester.test_health_check,
        tester.test_root_api,
        tester.test_report_lost_item,
        tester.test_report_found_item,
        tester.test_get_lost_items,
        tester.test_get_found_items,
        tester.test_get_specific_item,
        tester.test_quick_search,
        tester.test_visual_search,
        tester.test_search_items,
        tester.test_data_validation,
        tester.test_error_handling
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