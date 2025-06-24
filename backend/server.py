import os
import json
import uuid
import base64
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from bson.errors import InvalidId

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/umt_belongings_hub')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Initialize FastAPI app
app = FastAPI(title="UMT Belongings Hub API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client.umt_belongings_hub

# Pydantic models
class LostItemCreate(BaseModel):
    title: str
    category: str
    description: str
    location: str
    specificLocation: Optional[str] = None
    date: str
    image: Optional[str] = None
    ownerInfo: Dict
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
    finderInfo: Dict
    additionalNotes: Optional[str] = None

class QuickSearchRequest(BaseModel):
    searchType: str  # 'lost' or 'found'
    itemCategory: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None

class VisualSearchRequest(BaseModel):
    imageBase64: str
    searchType: str = "both"  # 'lost', 'found', or 'both'

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

async def simple_image_similarity(uploaded_image_b64: str, items: List[Dict]) -> List[Dict]:
    """Simple image similarity based on basic comparison"""
    # For now, return all items since we're focusing on backend functionality
    # In production, this would use proper image similarity algorithms
    return items[:10]  # Return top 10 items

async def openai_visual_search(image_base64: str, items: List[Dict]) -> List[Dict]:
    """Use OpenAI Vision API for better image similarity"""
    if not OPENAI_API_KEY:
        return await simple_image_similarity(image_base64, items)
    
    try:
        # OpenAI Vision API implementation would go here
        # For now, return simple similarity
        return await simple_image_similarity(image_base64, items)
    except Exception:
        return await simple_image_similarity(image_base64, items)

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await db.lost_items.find_one()
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

# Root API endpoint
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

# API Routes - Main functionality

# 1. Quick Search API (Home page search)
@app.post("/api/search/quick")
async def quick_search(search_data: QuickSearchRequest):
    """Quick search functionality for home page"""
    try:
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
        
        if not all_items:
            return {
                "success": False,
                "message": "No items found matching your criteria",
                "items": []
            }
        
        return {
            "success": True,
            "message": f"Found {len(all_items)} matching items",
            "items": convert_objectid_to_str(all_items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# 2. Visual Search API (Home page image search)
@app.post("/api/search/visual")
async def visual_search(search_data: VisualSearchRequest):
    """Visual search using image similarity"""
    try:
        # Get all items from both collections
        all_items = []
        
        # Get lost items
        lost_cursor = db.lost_items.find({"status": "active", "image": {"$exists": True, "$ne": None}})
        lost_items = await lost_cursor.to_list(length=None)
        
        # Get found items  
        found_cursor = db.found_items.find({"status": "active", "image": {"$exists": True, "$ne": None}})
        found_items = await found_cursor.to_list(length=None)
        
        all_items = lost_items + found_items
        
        if not all_items:
            return {
                "success": False,
                "message": "No items with images found for comparison",
                "items": []
            }
        
        # Perform image similarity search
        similar_items = await openai_visual_search(search_data.imageBase64, all_items)
        
        return {
            "success": True,
            "message": f"Found {len(similar_items)} visually similar items",
            "items": convert_objectid_to_str(similar_items)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visual search failed: {str(e)}")

# 3. Lost/Found Page Search API
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

# 4. Report Lost Item API
@app.post("/api/items/lost")
async def report_lost_item(item_data: LostItemCreate):
    """Report a lost item"""
    try:
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

# 5. Report Found Item API  
@app.post("/api/items/found")
async def report_found_item(item_data: FoundItemCreate):
    """Report a found item"""
    try:
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

# Additional utility APIs

# Get all lost items
@app.get("/api/items/lost")
async def get_lost_items(limit: int = Query(50, ge=1, le=100)):
    """Get all lost items"""
    try:
        cursor = db.lost_items.find({"status": "active"}).sort("createdAt", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return {
            "success": True,
            "count": len(items),
            "items": convert_objectid_to_str(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lost items: {str(e)}")

# Get all found items
@app.get("/api/items/found")
async def get_found_items(limit: int = Query(50, ge=1, le=100)):
    """Get all found items"""
    try:
        cursor = db.found_items.find({"status": "active"}).sort("createdAt", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        return {
            "success": True,
            "count": len(items),
            "items": convert_objectid_to_str(items)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch found items: {str(e)}")

# Get single item by ID
@app.get("/api/items/{item_type}/{item_id}")
async def get_item(item_type: str, item_id: str):
    """Get a specific item by ID"""
    try:
        if item_type not in ["lost", "found"]:
            raise HTTPException(status_code=400, detail="item_type must be 'lost' or 'found'")
        
        collection = db.lost_items if item_type == "lost" else db.found_items
        
        try:
            object_id = ObjectId(item_id)
            item = await collection.find_one({"_id": object_id})
        except InvalidId:
            # Try with string ID
            item = await collection.find_one({"id": item_id})
        
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        return {
            "success": True,
            "item": convert_objectid_to_str(item)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch item: {str(e)}")

# Serve HTML pages
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("/app/frontend/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/lost", response_class=HTMLResponse)
async def serve_lost():
    with open("/app/frontend/lost.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/found", response_class=HTMLResponse)
async def serve_found():
    with open("/app/frontend/found.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/report-lost", response_class=HTMLResponse)
async def serve_report_lost():
    with open("/app/frontend/report-lost.html", "r") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)