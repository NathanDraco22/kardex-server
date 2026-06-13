import asyncio
from pymongo import AsyncMongoClient

MONGO_URL = "mongodb://mongo:gkMCqLnJLuQUVgRCNsEMoHFyLXQchjda@yamabiko.proxy.rlwy.net:28317/?directConnection=true&retryWrites=false"

async def delete_operation_data():
    mongo_client = AsyncMongoClient(MONGO_URL)
    db = mongo_client.get_database("LedgerDB")

    cols = [
        "AdjustExits",
        "AdjustEntries",
        "ClientTransactions",
        "Clients",
        "DailySummaries",
        "Devolutions",
        "EntryDocs",
        "ExecutiveSummaries",
        "ExitDocs",
        "ExpirationLogs",
        "Invoices",
        "Orders",
        "ProductAccounts",
        "ProductSaleProfiles",
        "ProductStats",
        "ProductTransactions",
        "Products",
        "Receipts",
        "Suppliers",
        "Transfers",
    ]

    counters_col_name = "Counters"

    counter_user_name = "userNumber"

    coros = []

    for col_name in cols:
        col = db.get_collection(col_name)
        coro = col.delete_many({})
        coros.append(coro)

    await asyncio.gather(*coros)

    counter_col = db.get_collection(counters_col_name)

    await counter_col.delete_many({"name": {"$ne": counter_user_name}})

    await mongo_client.close()

    print("Commercial Data cleaned.")


asyncio.run(delete_operation_data())
