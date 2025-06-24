import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Depends, status, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from passlib.context import CryptContext
from jose import JWTError, jwt
import bcrypt
from bson import ObjectId
from bson.errors import InvalidId
import base64
from io import BytesIO
from PIL import Image
import numpy as np

# Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/umt_belongings_hub')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your_jwt_secret_key_here')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Initialize FastAPI app
app = FastAPI(title="UMT Belongings Hub API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient(MONGO_URL)
db = client.umt_belongings_hub

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# Serve static files
app.mount("/static", StaticFiles(directory="/app/frontend/public"), name="static")

# Pydantic models
class UserCreate(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PostCreate(BaseModel):
    title: str
    description: str
    category: str
    location: str
    date: str
    type: str  # 'lost' or 'found'
    image_base64: Optional[str] = None

class ClaimCreate(BaseModel):
    postId: str
    message: str

class MessageCreate(BaseModel):
    content: str

# Utility functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

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

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    with open("/app/frontend/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/admin", response_class=HTMLResponse)
async def serve_admin():
    with open("/app/frontend/admin.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/about", response_class=HTMLResponse)
async def serve_about():
    with open("/app/frontend/about.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/report-lost", response_class=HTMLResponse)
async def serve_report_lost():
    with open("/app/frontend/report-lost.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/my-posts", response_class=HTMLResponse)
async def serve_my_posts():
    with open("/app/frontend/my-posts.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/my-requests", response_class=HTMLResponse)
async def serve_my_requests():
    with open("/app/frontend/my-requests.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/item-details", response_class=HTMLResponse)
async def serve_item_details():
    with open("/app/frontend/item-details.html", "r") as f:
        return HTMLResponse(content=f.read())

# API Routes

# Authentication routes
@app.post("/api/auth/register")
async def register(user: UserCreate):
    # Check if user already exists
    existing_user = db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists with this email")
    
    # Validate university email
    if not user.email.endswith('.edu'):
        raise HTTPException(status_code=400, detail="Please use a valid university email address")
    
    # Hash password
    hashed_password = hash_password(user.password)
    
    # Create user
    user_doc = {
        "firstName": user.firstName,
        "lastName": user.lastName,
        "email": user.email,
        "password": hashed_password,
        "role": "STUDENT",
        "createdAt": datetime.utcnow(),
        "notifications": []
    }
    
    result = db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    # Create JWT token
    token = create_jwt_token(user_id)
    
    return {
        "token": token,
        "user": {
            "_id": user_id,
            "firstName": user.firstName,
            "lastName": user.lastName,
            "email": user.email,
            "role": "STUDENT"
        }
    }

@app.post("/api/auth/login")
async def login(user: UserLogin):
    # Find user
    db_user = db.users.find_one({"email": user.email})
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token(str(db_user["_id"]))
    
    return {
        "token": token,
        "user": {
            "_id": str(db_user["_id"]),
            "firstName": db_user["firstName"],
            "lastName": db_user["lastName"],
            "email": db_user["email"],
            "role": db_user["role"]
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {
        "_id": str(current_user["_id"]),
        "firstName": current_user["firstName"],
        "lastName": current_user["lastName"],
        "email": current_user["email"],
        "role": current_user["role"],
        "notificationCount": len([n for n in current_user.get("notifications", []) if not n.get("read", False)])
    }

# Posts routes
@app.post("/api/posts")
async def create_post(post: PostCreate, current_user: dict = Depends(get_current_user)):
    post_doc = {
        "title": post.title,
        "description": post.description,
        "category": post.category,
        "location": post.location,
        "date": post.date,
        "type": post.type,
        "image_base64": post.image_base64,
        "author": current_user["_id"],
        "authorName": f"{current_user['firstName']} {current_user['lastName']}",
        "createdAt": datetime.utcnow(),
        "status": "ACTIVE",
        "claims": []
    }
    
    result = db.posts.insert_one(post_doc)
    post_doc["_id"] = str(result.inserted_id)
    post_doc["author"] = str(post_doc["author"])
    
    return convert_objectid_to_str(post_doc)

@app.get("/api/posts")
async def get_posts(type: Optional[str] = None, category: Optional[str] = None, location: Optional[str] = None):
    query = {"status": "ACTIVE"}
    
    if type:
        query["type"] = type
    if category:
        query["category"] = category
    if location:
        query["location"] = location
    
    posts = list(db.posts.find(query).sort("createdAt", -1))
    return convert_objectid_to_str(posts)

@app.get("/api/posts/{post_id}")
async def get_post(post_id: str):
    try:
        post = db.posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        return convert_objectid_to_str(post)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid post ID")

@app.get("/api/posts/user/{user_id}")
async def get_user_posts(user_id: str, current_user: dict = Depends(get_current_user)):
    try:
        posts = list(db.posts.find({"author": ObjectId(user_id)}).sort("createdAt", -1))
        return convert_objectid_to_str(posts)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user ID")

# Claims routes
@app.post("/api/claims")
async def create_claim(claim: ClaimCreate, current_user: dict = Depends(get_current_user)):
    try:
        # Check if post exists
        post = db.posts.find_one({"_id": ObjectId(claim.postId)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        # Check if user is not the author
        if str(post["author"]) == str(current_user["_id"]):
            raise HTTPException(status_code=400, detail="You cannot claim your own post")
        
        # Create claim
        claim_doc = {
            "postId": ObjectId(claim.postId),
            "claimantId": current_user["_id"],
            "claimantName": f"{current_user['firstName']} {current_user['lastName']}",
            "message": claim.message,
            "status": "PENDING",
            "createdAt": datetime.utcnow()
        }
        
        result = db.claims.insert_one(claim_doc)
        
        # Add claim to post
        db.posts.update_one(
            {"_id": ObjectId(claim.postId)},
            {"$push": {"claims": result.inserted_id}}
        )
        
        # Add notification to post author
        db.users.update_one(
            {"_id": post["author"]},
            {"$push": {
                "notifications": {
                    "message": f"New claim on your {post['type']} item: {post['title']}",
                    "type": "CLAIM",
                    "link": f"/dashboard?tab=posts&post={claim.postId}",
                    "read": False,
                    "date": datetime.utcnow()
                }
            }}
        )
        
        claim_doc["_id"] = str(result.inserted_id)
        return convert_objectid_to_str(claim_doc)
    
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid post ID")

@app.get("/api/claims/post/{post_id}")
async def get_post_claims(post_id: str, current_user: dict = Depends(get_current_user)):
    try:
        claims = list(db.claims.find({"postId": ObjectId(post_id)}).sort("createdAt", -1))
        return convert_objectid_to_str(claims)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid post ID")

@app.get("/api/claims/user")
async def get_user_claims(current_user: dict = Depends(get_current_user)):
    claims = list(db.claims.find({"claimantId": current_user["_id"]}).sort("createdAt", -1))
    return convert_objectid_to_str(claims)

# Notifications routes
@app.get("/api/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = current_user.get("notifications", [])
    return convert_objectid_to_str(notifications)

@app.put("/api/notifications/{notification_index}/read")
async def mark_notification_read(notification_index: int, current_user: dict = Depends(get_current_user)):
    db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {f"notifications.{notification_index}.read": True}}
    )
    return {"message": "Notification marked as read"}

# Admin routes
@app.get("/api/admin/stats")
async def get_admin_stats(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_posts = db.posts.count_documents({})
    total_users = db.users.count_documents({})
    active_posts = db.posts.count_documents({"status": "ACTIVE"})
    resolved_posts = db.posts.count_documents({"status": "RESOLVED"})
    
    return {
        "totalPosts": total_posts,
        "totalUsers": total_users,
        "activePosts": active_posts,
        "resolvedPosts": resolved_posts
    }

@app.get("/api/admin/posts")
async def get_all_posts_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    posts = list(db.posts.find({}).sort("createdAt", -1))
    return convert_objectid_to_str(posts)

@app.get("/api/admin/users")
async def get_all_users_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = list(db.users.find({}, {"password": 0}).sort("createdAt", -1))
    return convert_objectid_to_str(users)

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)