import os
import json
import uuid
import base64
import asyncio
import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from io import BytesIO
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/umt_belongings_hub')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize FastAPI app
app = FastAPI(title="UMT Belongings Hub API", version="1.0.0")

# Add CORS middleware manually to avoid issues
@app.middleware("http")
async def cors_handler(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# MongoDB connection
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.umt_belongings_hub
except Exception as e:
    print(f"MongoDB connection error: {e}")
    db = None

# Pydantic models
class QuickSearchRequest(BaseModel):
    searchType: str = "both"  # 'lost', 'found', or 'both' 
    itemCategory: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None

class VisualSearchRequest(BaseModel):
    imageBase64: str
    searchType: str = "both"  # 'lost', 'found', or 'both'

class LostItemCreate(BaseModel):
    title: str
    category: str
    description: str
    location: str
    specificLocation: Optional[str] = None
    date: str
    image: Optional[str] = None
    ownerInfo: Dict[str, Any]
    offerReward: Optional[bool] = False
    rewardAmount: Optional[str] = None
    additionalNotes: Optional[str] = None

class FoundItemCreate(BaseModel):
    title: str
    category: str
    description: str
    location: str
    specificLocation: Optional[str] = None
    date: str
    image: Optional[str] = None
    finderInfo: Dict[str, Any]
    additionalNotes: Optional[str] = None

# Image Processing Utilities
class ImageSimilarityEngine:
    def __init__(self):
        # Initialize ORB detector for feature extraction
        self.orb = cv2.ORB_create(nfeatures=500)
    
    def base64_to_image(self, base64_string: str) -> np.ndarray:
        """Convert base64 string to OpenCV image"""
        try:
            # Remove data URL prefix if present
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_string)
            
            # Convert to PIL Image
            pil_image = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Convert to OpenCV format (BGR)
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return opencv_image
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
    
    def extract_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract ORB features from image"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Resize image to standard size for consistency
            gray = cv2.resize(gray, (300, 300))
            
            # Detect keypoints and compute descriptors
            keypoints, descriptors = self.orb.detectAndCompute(gray, None)
            
            if descriptors is not None:
                # If we have fewer than 10 descriptors, the image might not be suitable
                if len(descriptors) < 10:
                    return None
                
                # Flatten descriptors to create a feature vector
                # Take mean of descriptors to create a fixed-size feature vector
                feature_vector = np.mean(descriptors, axis=0)
                return feature_vector
            
            return None
        except Exception as e:
            print(f"Feature extraction error: {e}")
            return None
    
    def calculate_similarity(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """Calculate cosine similarity between two feature vectors"""
        try:
            # Reshape for sklearn
            features1 = features1.reshape(1, -1)
            features2 = features2.reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(features1, features2)[0][0]
            
            # Convert to percentage
            return float(similarity * 100)
        except Exception as e:
            print(f"Similarity calculation error: {e}")
            return 0.0

# Initialize image similarity engine
image_engine = ImageSimilarityEngine()

# Utility functions
def convert_objectid_to_str(obj):
    """Convert ObjectId to string for JSON serialization"""
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_objectid_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj

# Basic endpoints first
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        if db is None:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": "MongoDB connection failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Test database connection
        result = await db.lost_items.find_one()
        return {
            "status": "healthy",
            "database": "connected", 
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/")
async def root():
    """Root API endpoint"""
    return {
        "message": "UMT Belongings Hub API is running",
        "version": "1.0.0",
        "endpoints": {
            "quick_search": "/api/search/quick",
            "visual_search": "/api/search/visual", 
            "search_items": "/api/search/items",
            "report_lost": "/api/items/lost",
            "report_found": "/api/items/found",
            "get_lost_items": "/api/items/lost",
            "get_found_items": "/api/items/found",
            "health": "/api/health"
        }
    }

# Search endpoints
@app.post("/api/search/quick")
async def quick_search(search_data: QuickSearchRequest):
    """Quick search functionality for home page"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Build query based on search criteria
        query = {"status": "active"}
        
        if search_data.searchType in ["lost", "found"]:
            query["type"] = search_data.searchType
        
        if search_data.itemCategory:
            query["category"] = {"$regex": search_data.itemCategory, "$options": "i"}
        
        if search_data.location:
            query["$or"] = [
                {"location": {"$regex": search_data.location, "$options": "i"}},
                {"specificLocation": {"$regex": search_data.location, "$options": "i"}}
            ]
        
        if search_data.date:
            query["date"] = search_data.date
        
        # Search in both collections
        lost_items = []
        found_items = []
        
        if search_data.searchType in ["lost", "both"]:
            lost_cursor = db.lost_items.find(query).sort("createdAt", -1).limit(20)
            lost_items = await lost_cursor.to_list(length=20)
        
        if search_data.searchType in ["found", "both"]:
            found_cursor = db.found_items.find(query).sort("createdAt", -1).limit(20)
            found_items = await found_cursor.to_list(length=20)
        
        # Combine results
        all_items = lost_items + found_items
        
        return {
            "success": True,
            "message": f"Found {len(all_items)} matching items",
            "items": convert_objectid_to_str(all_items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/search/visual")
async def visual_search(search_data: VisualSearchRequest):
    """Enhanced visual search using image similarity"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Convert uploaded image to OpenCV format
        uploaded_image = image_engine.base64_to_image(search_data.imageBase64)
        
        # Extract features from uploaded image
        uploaded_features = image_engine.extract_features(uploaded_image)
        
        if uploaded_features is None:
            return {
                "success": False,
                "message": "Could not extract features from uploaded image. Please try a clearer image.",
                "items": []
            }
        
        # Get all items from both collections that have images
        all_items = []
        
        # Get lost items with images
        if search_data.searchType in ["lost", "both"]:
            lost_cursor = db.lost_items.find({
                "status": "active", 
                "image": {"$exists": True, "$ne": None, "$ne": ""}
            })
            lost_items = await lost_cursor.to_list(length=None)
            all_items.extend(lost_items)
        
        # Get found items with images
        if search_data.searchType in ["found", "both"]:
            found_cursor = db.found_items.find({
                "status": "active", 
                "image": {"$exists": True, "$ne": None, "$ne": ""}
            })
            found_items = await found_cursor.to_list(length=None)
            all_items.extend(found_items)
        
        if not all_items:
            return {
                "success": False,
                "message": "No items with images found for comparison",
                "items": []
            }
        
        # Calculate similarity for each item
        similar_items = []
        
        for item in all_items:
            try:
                # Extract features from database item image
                item_image = image_engine.base64_to_image(item['image'])
                item_features = image_engine.extract_features(item_image)
                
                if item_features is not None:
                    # Calculate similarity
                    similarity_score = image_engine.calculate_similarity(uploaded_features, item_features)
                    
                    # Only include items with significant similarity (>= 20%)
                    if similarity_score >= 20:
                        item['similarity_score'] = round(similarity_score, 2)
                        similar_items.append(item)
                        
            except Exception as e:
                print(f"Error processing item {item.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by similarity score (highest first)
        similar_items.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit results to top 15 matches
        similar_items = similar_items[:15]
        
        return {
            "success": True,
            "message": f"Found {len(similar_items)} visually similar items",
            "items": convert_objectid_to_str(similar_items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")

@app.get("/api/search/items")
async def search_items(
    item_type: str = Query(..., description="Type: lost or found"),
    q: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    limit: int = Query(50, ge=1, le=100)
):
    """Search items on lost/found pages"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
            
        if item_type not in ["lost", "found"]:
            raise HTTPException(status_code=400, detail="item_type must be 'lost' or 'found'")
        
        # Build search query
        query = {"status": "active"}
        
        # Text search across multiple fields
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"location": {"$regex": q, "$options": "i"}},
                {"specificLocation": {"$regex": q, "$options": "i"}}
            ]
        
        # Category filter
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        
        # Location filter
        if location:
            if "$or" in query:
                # If text search exists, combine with location
                query = {
                    "$and": [
                        query,
                        {
                            "$or": [
                                {"location": {"$regex": location, "$options": "i"}},
                                {"specificLocation": {"$regex": location, "$options": "i"}}
                            ]
                        }
                    ]
                }
            else:
                query["$or"] = [
                    {"location": {"$regex": location, "$options": "i"}},
                    {"specificLocation": {"$regex": location, "$options": "i"}}
                ]
        
        # Choose collection based on type
        collection = db.lost_items if item_type == "lost" else db.found_items
        
        # Execute search
        cursor = collection.find(query).sort("createdAt", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        
        return {
            "success": True,
            "count": len(items),
            "items": convert_objectid_to_str(items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# CRUD endpoints
@app.get("/api/items/lost")
async def get_lost_items(limit: int = Query(50, ge=1, le=100)):
    """Get all lost items"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
            
        cursor = db.lost_items.find({"status": "active"}).sort("createdAt", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return {
            "success": True,
            "count": len(items),
            "items": convert_objectid_to_str(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lost items: {str(e)}")

@app.get("/api/items/found")
async def get_found_items(limit: int = Query(50, ge=1, le=100)):
    """Get all found items"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
            
        cursor = db.found_items.find({"status": "active"}).sort("createdAt", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return {
            "success": True,
            "count": len(items),
            "items": convert_objectid_to_str(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch found items: {str(e)}")

@app.post("/api/items/lost")
async def report_lost_item(item_data: LostItemCreate):
    """Report a lost item"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
            
        # Create lost item document
        lost_item = {
            "id": str(uuid.uuid4()),
            "type": "lost",
            "title": item_data.title,
            "category": item_data.category,
            "description": item_data.description,
            "location": item_data.location,
            "specificLocation": item_data.specificLocation,
            "date": item_data.date,
            "image": item_data.image,
            "status": "active",
            "ownerInfo": item_data.ownerInfo,
            "offerReward": item_data.offerReward,
            "rewardAmount": item_data.rewardAmount,
            "additionalNotes": item_data.additionalNotes,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        # Insert into database
        result = await db.lost_items.insert_one(lost_item)
        lost_item["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "message": "Lost item reported successfully",
            "item": convert_objectid_to_str(lost_item)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to report lost item: {str(e)}")

@app.post("/api/items/found")
async def report_found_item(item_data: FoundItemCreate):
    """Report a found item"""
    try:
        if db is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
            
        # Create found item document
        found_item = {
            "id": str(uuid.uuid4()),
            "type": "found",
            "title": item_data.title,
            "category": item_data.category,
            "description": item_data.description,
            "location": item_data.location,
            "specificLocation": item_data.specificLocation,
            "date": item_data.date,
            "image": item_data.image,
            "status": "active",
            "finderInfo": item_data.finderInfo,
            "additionalNotes": item_data.additionalNotes,
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        
        # Insert into database
        result = await db.found_items.insert_one(found_item)
        found_item["_id"] = str(result.inserted_id)
        
        return {
            "success": True,
            "message": "Found item reported successfully",
            "item": convert_objectid_to_str(found_item)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to report found item: {str(e)}")

# Serve static HTML files
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    try:
        with open("/app/frontend/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(status_code=404, detail="Home page not found")

@app.get("/lost", response_class=HTMLResponse)
async def serve_lost():
    try:
        with open("/app/frontend/lost.html", "r") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(status_code=404, detail="Lost page not found")

@app.get("/found", response_class=HTMLResponse)
async def serve_found():
    try:
        with open("/app/frontend/found.html", "r") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(status_code=404, detail="Found page not found")

@app.get("/report-lost", response_class=HTMLResponse)
async def serve_report_lost():
    try:
        with open("/app/frontend/report-lost.html", "r") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(status_code=404, detail="Report lost page not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)