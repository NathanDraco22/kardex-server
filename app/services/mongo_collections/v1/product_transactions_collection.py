from typing import Any

from pymongo import ReturnDocument, IndexModel
from services import MongoService


class ProductTransactionsCollection:
    collection_name = "ProductTransactions"
    _instance: "ProductTransactionsCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_product_transaction(self, product_transaction: dict) -> None:
        collection = self.__collection
        await collection.insert_one(product_transaction)

    async def fetch_all_product_transactions(self, **kwargs) -> list[dict[str, Any]]:
        collection = self.__collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        if kwargs.get("endDate") is not None:
            query["createdAt"] = {
                "$lte": kwargs.get("endDate"),
            }
            del query["endDate"]

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)

        cursor = collection.find(query).skip(offset).limit(limit).sort("createdAt", -1)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_transaction_by_id(
        self, product_transaction_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": product_transaction_id})
        return result

    async def update_product_transaction_by_id(
        self,
        product_transaction_id: str,
        product_transaction: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"id": product_transaction_id},
            {"$set": product_transaction},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def create_index(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("id", 1),
                    ],
                    unique=True,
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("type", 1),
                        ("subtype", 1),
                        ("createdAt", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("productId", 1),
                        ("createdAt", -1),
                    ]
                ),
                IndexModel(
                    [
                        ("createdAt", -1),
                    ],
                ),
            ]
        )

    async def create_product_transaction_with_session(
        self, product_transaction: dict, session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_one(product_transaction, session=session)

    async def create_many_product_transactions_with_session(
        self, product_transactions: list[dict], session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_many(product_transactions, session=session)

    async def estimate_invoice_product_stats(self, **kwargs) -> None:
        collection = self.__collection
        start_date = kwargs.get("startDate")
        end_date = kwargs.get("endDate")
        batch_time = kwargs.get("batchTime")
        days_analysis = kwargs.get("daysAnalysis")
        pipeline = [
            # 1. Filtro: Solo ventas válidas del periodo
            {
                "$match": {
                    "subtype": "invoice",
                    "createdAt": {"$gte": start_date, "$lte": end_date},
                    # "isDeleted": {"$ne": True}
                }
            },
            # 2. AGRUPACIÓN COMPUESTA
            # Agrupamos por la combinación única de Producto + Sucursal
            {
                "$group": {
                    "_id": {"productId": "$productId", "branchId": "$branchId"},
                    "totalUnits": {"$sum": "$quantity"},
                    "totalTransactions": {"$sum": 1},
                }
            },
            # 3. PROYECCIÓN (Aplanar la estructura)
            {
                "$project": {
                    "_id": 0,
                    # Sacamos los campos del objeto _id para que queden al nivel raíz
                    "productId": "$_id.productId",
                    "branchId": "$_id.branchId",
                    "startDate": {"$literal": start_date},
                    "endDate": {"$literal": end_date},
                    "totalUnits": {"$abs": "$totalUnits"},
                    "totalTransactions": 1,
                    "daysAnalyzed": {"$literal": days_analysis},
                    "lastEstimation": {"$literal": batch_time},
                }
            },
            # 4. MERGE CON CLAVE COMPUESTA
            {
                "$merge": {
                    "into": "ProductStats",
                    "on": ["productId", "branchId"],
                    "whenMatched": "merge",
                    "whenNotMatched": "insert",
                }
            },
        ]
        await collection.aggregate(pipeline).to_list(length=None)
