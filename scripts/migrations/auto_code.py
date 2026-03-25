import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne, ReturnDocument


# MONGO_URL = "mongodb://mongo:gkMCqLnJLuQUVgRCNsEMoHFyLXQchjda@yamabiko.proxy.rlwy.net:28317/?directConnection=true&retryWrites=false"

MONGO_URL = "mongodb+srv://nathandraco22:nathandraco22db@cluster0.l8grx3u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


async def auto_code_products():
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client.get_database("variedades_etel")
    product_col = db.get_collection("Products")
    product_counter_col = db.get_collection("Counters")

    no_coded_products = await product_col.find(
        {
            "$or": [
                {"code": None},
                {"code": ""},
                {"code": {"$exists": False}},
            ],
        }
    ).to_list(length=None)

    if len(no_coded_products) == 0:
        print("No code products found. Exiting...")
        return

    current_counter = await product_counter_col.find_one_and_update(
        {"name": "productNumber"},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    current_index: int = current_counter["value"]

    update_ops = []

    for product in no_coded_products:
        formatted = str(current_index).zfill(5)
        update_ops.append(
            UpdateOne({"id": product["id"]}, {"$set": {"code": formatted}})
        )

        current_index += 1

    await product_col.bulk_write(update_ops)

    await product_counter_col.update_one(
        {"name": "productNumber"},
        {
            "$set": {"value": current_index},
        },
    )

    print("Done!!!")


if __name__ == "__main__":
    asyncio.run(auto_code_products())
