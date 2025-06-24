import asyncio
import base64
import json
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Sample images converted to base64 (small placeholders for testing)
SAMPLE_IMAGES = {
    "wallet": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
    "phone": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=",
    "keys": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
}

async def add_sample_data():
    """Add sample lost and found items with images for testing visual search"""
    
    client = AsyncIOMotorClient('mongodb://localhost:27017/umt_belongings_hub')
    db = client.umt_belongings_hub
    
    # Sample lost items
    lost_items = [
        {
            "id": "lost_001",
            "type": "lost",
            "title": "Black Leather Wallet",
            "category": "Wallets & Accessories",
            "description": "Lost my black leather wallet containing student ID, credit cards, and some cash. Very important to me.",
            "location": "Student Center",
            "specificLocation": "Near the food court",
            "date": "2025-06-20",
            "image": SAMPLE_IMAGES["wallet"],
            "status": "active",
            "ownerInfo": {
                "name": "Ahmed Khan",
                "email": "ahmed.khan@umt.edu.pk",
                "phone": "+92 300 1234567"
            },
            "offerReward": True,
            "rewardAmount": "Rs. 500",
            "additionalNotes": "Please contact me if found. Reward offered.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "id": "lost_002",
            "type": "lost",
            "title": "iPhone 13 Pro Max",
            "category": "Electronics",
            "description": "Silver iPhone 13 Pro Max with a blue protective case. Lost during physics lab session.",
            "location": "Science Building",
            "specificLocation": "Physics Lab 2",
            "date": "2025-06-21",
            "image": SAMPLE_IMAGES["phone"],
            "status": "active",
            "ownerInfo": {
                "name": "Sara Ahmed",
                "email": "sara.ahmed@umt.edu.pk",
                "phone": "+92 300 9876543"
            },
            "offerReward": True,
            "rewardAmount": "Rs. 2000",
            "additionalNotes": "Very urgent - contains important data.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    # Sample found items
    found_items = [
        {
            "id": "found_001",
            "type": "found",
            "title": "Set of Keys with Car Remote",
            "category": "Keys & ID Cards",
            "description": "Found a set of keys with a car remote and a dorm key. Found on the table near cafeteria entrance.",
            "location": "Cafeteria",
            "specificLocation": "Near the main entrance",
            "date": "2025-06-20",
            "image": SAMPLE_IMAGES["keys"],
            "status": "active",
            "finderInfo": {
                "name": "Hassan Raza",
                "email": "hassan.raza@umt.edu.pk",
                "phone": "+92 300 7777777"
            },
            "additionalNotes": "Contact me to claim your keys.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "id": "found_002",
            "type": "found",
            "title": "Brown Leather Wallet",
            "category": "Wallets & Accessories",
            "description": "Found a brown leather wallet near the library. Contains some cards and documents.",
            "location": "Main Library",
            "specificLocation": "Reading Area 1",
            "date": "2025-06-21",
            "image": SAMPLE_IMAGES["wallet"],
            "status": "active",
            "finderInfo": {
                "name": "Fatima Ali",
                "email": "fatima.ali@umt.edu.pk",
                "phone": "+92 300 5555555"
            },
            "additionalNotes": "Please provide ID to claim.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "id": "found_003",
            "type": "found",
            "title": "Samsung Galaxy Phone",
            "category": "Electronics",
            "description": "Found a Samsung Galaxy phone with a black case in the sports complex locker room.",
            "location": "Sports Complex",
            "specificLocation": "Men's Locker Room",
            "date": "2025-06-22",
            "image": SAMPLE_IMAGES["phone"],
            "status": "active",
            "finderInfo": {
                "name": "Usman Ali",
                "email": "usman.ali@umt.edu.pk",
                "phone": "+92 300 9999999"
            },
            "additionalNotes": "Contact me with proof of ownership.",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    
    try:
        # Insert lost items
        print("Inserting lost items...")
        result = await db.lost_items.insert_many(lost_items)
        print(f"Inserted {len(result.inserted_ids)} lost items")
        
        # Insert found items
        print("Inserting found items...")
        result = await db.found_items.insert_many(found_items)
        print(f"Inserted {len(result.inserted_ids)} found items")
        
        print("Sample data added successfully!")
        
        # Verify data
        lost_count = await db.lost_items.count_documents({"status": "active"})
        found_count = await db.found_items.count_documents({"status": "active"})
        print(f"Total active lost items: {lost_count}")
        print(f"Total active found items: {found_count}")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(add_sample_data())