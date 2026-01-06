import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URL = "mongodb://mongo:gkMCqLnJLuQUVgRCNsEMoHFyLXQchjda@yamabiko.proxy.rlwy.net:28317/?directConnection=true&retryWrites=false"


async def add_names_tranfers():
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client.get_database("LedgerDB")
    col = db.get_collection("Branches")

    all_branches = await col.find({}).to_list(length=None)

    branches_mapping = {}

    for branch in all_branches:
        branches_mapping[branch["id"]] = branch["name"]

    col = db.get_collection("Transfers")

    for key, value in branches_mapping.items():
        await col.update_many({"origin": key}, {"$set": {"originName": value}})

        await col.update_many(
            {"destination": key}, {"$set": {"destinationName": value}}
        )


async def main():
    await add_names_tranfers()


if __name__ == "__main__":
    asyncio.run(main())
