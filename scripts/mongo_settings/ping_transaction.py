import asyncio
from pymongo import AsyncMongoClient


async def create_transaction():
    # Initialize the MongoDB client
    client = AsyncMongoClient(
        "mongodb://mongo:AOlhqQqCfLDhbwfIgqfVWOKOZdtYhPqt@trolley.proxy.rlwy.net:51439?directConnection=true&retryWrites=false"
    )
    db = client["your_database"]
    collection = db["your_collection"]

    # Start a session
    async with client.start_session() as session:
        # Start a transaction
        async with await session.start_transaction():
            # Define the document to insert
            transaction_data = {
                "field1": "value1",
                "field2": "value2",
                # Add more fields as needed
            }

            # Insert the document within the transaction
            result = await collection.insert_one(transaction_data, session=session)

            transaction_data = {
                "field1": "value1",
                "field2": "value2",
                # Add more fields as needed
            }

            result = await collection.insert_one(transaction_data, session=session)

            # Optionally return the inserted document or its ID
            return result.inserted_id


async def main():
    result = await create_transaction()
    print("Transaction result:", result)


asyncio.run(main())
