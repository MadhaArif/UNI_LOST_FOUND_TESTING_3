import asyncio
import base64
import json
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

def create_test_image(width=200, height=200, color=(100, 150, 200), shape='rectangle'):
    """Create a simple test image with basic shapes and patterns"""
    
    # Create a new image with RGB mode
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    if shape == 'rectangle':
        # Draw a colored rectangle
        draw.rectangle([20, 20, width-20, height-20], fill=color, outline=(0, 0, 0), width=3)
        # Add some text-like patterns
        for i in range(3):
            y = 50 + i * 30
            draw.rectangle([40, y, width-40, y+10], fill=(50, 50, 50))
    
    elif shape == 'circle':
        # Draw a colored circle
        draw.ellipse([20, 20, width-20, height-20], fill=color, outline=(0, 0, 0), width=3)
        # Add some internal patterns
        draw.ellipse([60, 60, width-60, height-60], fill=(200, 200, 200))
    
    elif shape == 'phone':
        # Draw a phone-like shape
        draw.rectangle([30, 10, width-30, height-10], fill=color, outline=(0, 0, 0), width=3)
        # Screen
        draw.rectangle([40, 30, width-40, height-50], fill=(0, 0, 0))
        # Button
        draw.ellipse([width//2-10, height-25, width//2+10, height-15], fill=(100, 100, 100))
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return f"data:image/jpeg;base64,{img_base64}"

async def add_realistic_test_data():
    """Add more realistic test data with proper images"""
    
    client = AsyncIOMotorClient('mongodb://localhost:27017/umt_belongings_hub')
    db = client.umt_belongings_hub
    
    # Clear existing data
    await db.lost_items.delete_many({})
    await db.found_items.delete_many({})
    
    # Create test images
    wallet_img = create_test_image(200, 150, (139, 69, 19), 'rectangle')  # Brown wallet
    phone_img = create_test_image(180, 320, (70, 70, 70), 'phone')  # Dark phone
    keys_img = create_test_image(150, 200, (255, 215, 0), 'circle')  # Golden keys
    
    # Similar images for testing matching
    wallet_similar = create_test_image(190, 140, (160, 82, 45), 'rectangle')  # Similar wallet
    phone_similar = create_test_image(170, 310, (85, 85, 85), 'phone')  # Similar phone
    
    lost_items = [
        {
            "id": "lost_wallet_001",
            "type": "lost",
            "title": "Brown Leather Wallet",
            "category": "Wallets & Accessories",
            "description": "Lost my brown leather wallet with university ID and credit cards.",
            "location": "Student Center",
            "specificLocation": "Near the food court",
            "date": "2025-06-23",
            "image": wallet_img,
            "status": "active",
            "ownerInfo": {
                "name": "Ahmed Khan",
                "email": "ahmed.khan@umt.edu.pk",
                "phone": "+92 300 1234567"
            },
            "offerReward": True,
            "rewardAmount": "Rs. 500",
            "additionalNotes": "Please contact me if found.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "id": "lost_phone_001", 
            "type": "lost",
            "title": "Samsung Galaxy S22",
            "category": "Electronics",
            "description": "Lost my Samsung Galaxy phone with black case during lecture.",
            "location": "Science Building",
            "specificLocation": "Lecture Hall 3",
            "date": "2025-06-23",
            "image": phone_img,
            "status": "active",
            "ownerInfo": {
                "name": "Sara Ahmed",
                "email": "sara.ahmed@umt.edu.pk",
                "phone": "+92 300 9876543"
            },
            "offerReward": True,
            "rewardAmount": "Rs. 1000",
            "additionalNotes": "Urgent - important data inside.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    found_items = [
        {
            "id": "found_wallet_001",
            "type": "found", 
            "title": "Dark Brown Wallet",
            "category": "Wallets & Accessories",
            "description": "Found a brown wallet near library entrance. Contains some cards.",
            "location": "Main Library",
            "specificLocation": "Main entrance",
            "date": "2025-06-23",
            "image": wallet_similar,
            "status": "active",
            "finderInfo": {
                "name": "Hassan Raza",
                "email": "hassan.raza@umt.edu.pk",
                "phone": "+92 300 7777777"
            },
            "additionalNotes": "Contact me to claim with ID proof.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "id": "found_phone_001",
            "type": "found",
            "title": "Black Android Phone", 
            "category": "Electronics",
            "description": "Found a black smartphone in the cafeteria. Looks like Samsung Galaxy.",
            "location": "Cafeteria",
            "specificLocation": "Table near window",
            "date": "2025-06-23",
            "image": phone_similar,
            "status": "active",
            "finderInfo": {
                "name": "Fatima Ali",
                "email": "fatima.ali@umt.edu.pk", 
                "phone": "+92 300 5555555"
            },
            "additionalNotes": "Please provide unlock code to verify ownership.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "id": "found_keys_001",
            "type": "found",
            "title": "Set of Keys with Keychain",
            "category": "Keys & ID Cards", 
            "description": "Found a set of keys with a golden keychain near the sports complex.",
            "location": "Sports Complex",
            "specificLocation": "Basketball court",
            "date": "2025-06-23",
            "image": keys_img,
            "status": "active",
            "finderInfo": {
                "name": "Usman Ali",
                "email": "usman.ali@umt.edu.pk",
                "phone": "+92 300 9999999"
            },
            "additionalNotes": "Safe with me, contact anytime.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    try:
        print("Inserting new test data...")
        
        # Insert lost items
        if lost_items:
            result = await db.lost_items.insert_many(lost_items)
            print(f"Inserted {len(result.inserted_ids)} lost items")
        
        # Insert found items  
        if found_items:
            result = await db.found_items.insert_many(found_items)
            print(f"Inserted {len(result.inserted_ids)} found items")
        
        print("Test data added successfully!")
        
        # Verify data
        lost_count = await db.lost_items.count_documents({"status": "active"})
        found_count = await db.found_items.count_documents({"status": "active"})
        print(f"Total active lost items: {lost_count}")
        print(f"Total active found items: {found_count}")
        
        # Return test image for manual testing
        print("\nTest wallet image for visual search:")
        print(wallet_img[:100] + "...")
        
    except Exception as e:
        print(f"Error adding test data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_realistic_test_data())