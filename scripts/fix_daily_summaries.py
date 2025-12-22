import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from services import MongoService
from services.mongo_collections.v1 import DailySummariesCollection

async def fix_daily_summaries():
    print("🚀 Starting Daily Summaries Cleanup...")
    collection = DailySummariesCollection()
    
    # 1. Pipeline to find duplicates
    pipeline = [
        {
            "$group": {
                "_id": "$dateId",
                "ids": {"$push": "$id"},
                "count": {"$sum": 1}
            }
        },
        {
            "$match": {
                "count": {"$gt": 1}
            }
        }
    ]
    
    # Needs to access the underlying pymongo collection to run aggregate
    # Accessing private attribute strictly for script usage
    mongo_collection = collection._DailySummariesCollection__collection
    
    cursor = mongo_collection.aggregate(pipeline)
    duplicates = await cursor.to_list(length=None)
    
    total_deleted = 0
    
    for group in duplicates:
        print(f"found {group['count']} duplicates for dateId: {group['_id']}")
        ids_to_delete = group['ids'][1:] # Keep the first one
        
        for doc_id in ids_to_delete:
            await collection.delete_daily_summary_by_id(doc_id)
            total_deleted += 1
            
    print(f"✅ Cleanup complete. Deleted {total_deleted} duplicate records.")
    
    # 2. Re-create indexes to enforce uniqueness
    print("🔒 Creating Indexes...")
    await collection.create_indexes()
    print("✅ Indexes created successfully.")

if __name__ == "__main__":
    asyncio.run(fix_daily_summaries())
