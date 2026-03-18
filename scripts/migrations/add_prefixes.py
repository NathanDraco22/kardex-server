import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import UpdateOne

MONGO_URL = (
    "mongodb+srv://cristianmorazan94_db_user:cristian_db@clustere.tqsmkqo.mongodb.net/"
)
DB_NAME = "LedgerDB"


def generate_prefixes(text: str, min_size: int = 2, max_size: int = 10) -> list[str]:
    prefixes = set()
    text = text.lower()
    for word in text.split():
        word_len = len(word)

        for n in range(min_size, min(word_len, max_size) + 1):
            prefixes.add(word[:n])
    return list(prefixes)


async def add_product_prefix():
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client.get_database("LedgerDB")
    collection = db.get_collection("Clients")

    cursor = collection.find({})

    products = await cursor.to_list(length=None)

    update_ops = []

    for product in products:
        prefixes = generate_prefixes(product["name"])
        update_ops.append(
            UpdateOne(
                {"id": product["id"]},
                {
                    "$set": {
                        "searchPrefixes": prefixes,
                    },
                },
            )
        )

    await collection.bulk_write(update_ops)

    print("Done!!!")


if __name__ == "__main__":
    asyncio.run(add_product_prefix())
