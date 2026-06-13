import asyncio
from pymongo import AsyncMongoClient

MONGO_URL = "mongodb://mongo:gkMCqLnJLuQUVgRCNsEMoHFyLXQchjda@yamabiko.proxy.rlwy.net:28317/?directConnection=true&retryWrites=false"


async def add_invoice_doc_number_devolutions():
    client = AsyncMongoClient(MONGO_URL)
    db = client["LedgerDB"]
    devol_col = db["Devolutions"]
    inv_col = db["Invoices"]

    cursor = devol_col.find({})

    devolutions = await cursor.to_list(length=None)

    for devolution in devolutions:
        invoice_id = devolution.get("originalInvoiceId")

        if invoice_id is None:
            return

        invoice = await inv_col.find_one({"id": invoice_id})

        if invoice is None:
            return

        doc_number = invoice.get("docNumber")

        if doc_number is None:
            return

        await devol_col.update_one(
            {"id": devolution.get("id")},
            {"$set": {"originalInvoiceDocNumber": doc_number}},
        )


async def main():
    await add_invoice_doc_number_devolutions()


if __name__ == "__main__":
    asyncio.run(main())
