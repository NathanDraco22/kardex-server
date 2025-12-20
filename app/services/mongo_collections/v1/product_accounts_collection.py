from typing import AsyncGenerator
from typing import Any


from pymongo import ReturnDocument, IndexModel

from services import MongoService

from tools import TimeTools


class ProductAccountsCollection:
    collection_name = "ProductAccounts"

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_product_account(self, product_account: dict) -> None:
        collection = self.__collection
        await collection.insert_one(product_account)

    async def get_product_account_by_product_and_branch_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {"productId": product_id, "branchId": branch_id}
        )
        return result

    async def get_product_account_with_product_data(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection

        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "productId": product_id,
                        "branchId": branch_id,
                    }
                },
                {
                    "$lookup": {
                        "from": "Products",
                        "localField": "productId",
                        "foreignField": "id",
                        "as": "product",
                    }
                },
                {"$unwind": "$product"},
            ]
        )

        result = await cursor.to_list(length=None)

        if result:
            result = result[0]
            return result

        return None

    async def create_new_product_account_with_session(
        self, product_account: dict, session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_one(product_account, session=session)

    async def substract_product_account_data(
        self,
        product_id: str,
        branch_id: str,
        substract_to_current_stock: int,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()
        result = await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
                "currentStock": {"$gte": abs(substract_to_current_stock)},
            },
            {
                "$inc": {
                    "currentStock": -abs(substract_to_current_stock),
                },
                "$set": {
                    "updatedAt": updated_at,
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def add_to_promise_stock(
        self, product_id: str, branch_id: str, quantity: int, session: Any
    ) -> dict[str, Any] | None:
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()
        result = await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
                "$expr": {
                    "$gte": [
                        {
                            "$subtract": [
                                "$currentStock",
                                "$promiseStock",
                            ],
                        },
                        quantity,
                    ]
                },
            },
            {
                "$inc": {
                    "promiseStock": quantity,
                },
                "$set": {
                    "updatedAt": updated_at,
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def substract_from_promise_stock(
        self, product_id: str, branch_id: str, quantity: int, session: Any
    ) -> dict[str, Any] | None:
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()
        result = await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
                "promiseStock": {"$gte": quantity},
            },
            {
                "$inc": {
                    "promiseStock": -abs(quantity),
                },
                "$set": {
                    "updatedAt": updated_at,
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_product_account_balance_data(
        self,
        product_id: str,
        branch_id: str,
        add_to_current_stock: int,
        last_cost: int,
        session: Any,
    ) -> dict[str, Any]:
        collection = self.__collection
        update_at = TimeTools.get_now_in_milliseconds()

        result = await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
            },
            [
                {
                    "$set": {
                        "currentStock": {
                            "$add": [
                                {"$ifNull": ["$currentStock", 0]},
                                add_to_current_stock,
                            ]
                        },
                        "lastCost": last_cost,
                        "averageCost": {
                            "$convert": {
                                "input": {
                                    "$round": [
                                        {
                                            "$divide": [
                                                {
                                                    "$add": [
                                                        {
                                                            "$multiply": [
                                                                {
                                                                    "$ifNull": [
                                                                        "$currentStock",
                                                                        0,
                                                                    ]
                                                                },
                                                                {
                                                                    "$ifNull": [
                                                                        "$averageCost",
                                                                        0,
                                                                    ]
                                                                },
                                                            ]
                                                        },
                                                        {
                                                            "$multiply": [
                                                                add_to_current_stock,
                                                                last_cost,
                                                            ]
                                                        },
                                                    ]
                                                },
                                                {
                                                    "$add": [
                                                        {
                                                            "$ifNull": [
                                                                "$currentStock",
                                                                0,
                                                            ]
                                                        },
                                                        add_to_current_stock,
                                                    ]
                                                },
                                            ]
                                        },
                                        0,
                                    ]
                                },
                                "to": "long",
                            }
                        },
                        "updatedAt": update_at,
                        "createdAt": {"$ifNull": ["$createdAt", update_at]},
                        "promiseStock": {"$ifNull": ["$promiseStock", 0]},
                    }
                },
            ],
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def create_index(self):
        collection = self.__collection
        await collection.create_indexes(
            [
                IndexModel(
                    [
                        ("branchId", 1),
                    ]
                ),
                IndexModel(
                    [
                        ("branchId", 1),
                        ("productId", 1),
                    ]
                ),
            ]
        )

    async def get_all_product_accounts_with_product(
        self, branch_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        collection = self.__collection
        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "branchId": branch_id,
                    }
                },
                {
                    "$lookup": {
                        "from": "Products",
                        "localField": "productId",
                        "foreignField": "id",
                        "as": "product",
                    }
                },
                {"$unwind": "$product"},
                {"$sort": {"product.name": 1}},
            ]
        )

        async for product_account in cursor:
            yield product_account

    async def get_total_current_stock(self, branch_id: str) -> int:
        collection = self.__collection
        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "branchId": branch_id,
                    }
                },
                {
                    "$group": {
                        "_id": branch_id,
                        "total": {
                            "$sum": {
                                "$multiply": [
                                    "$currentStock",
                                    "$averageCost",
                                ],
                            },
                        },
                    }
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        if result:
            return result[0]["total"]

        return 0

    async def dispatch_promise_stock(
        self,
        product_id: str,
        branch_id: str,
        quantity_dispatched: int,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self.__collection
        return await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
                "promiseStock": {"$gte": quantity_dispatched},
            },
            {
                "$inc": {
                    "promiseStock": -quantity_dispatched,
                    "currentStock": -quantity_dispatched,
                },
                "$set": {
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

    async def dispatch_direct_stock(
        self, product_id: str, branch_id: str, quantity_to_dispatch: int, session: Any
    ) -> dict[str, Any] | None:
        collection = self.__collection
        return await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
                "$expr": {
                    "$gte": [
                        {
                            "$subtract": [
                                "$currentStock",
                                "$promiseStock",
                            ],
                        },
                        quantity_to_dispatch,
                    ]
                },
            },
            {
                "$inc": {"currentStock": -quantity_to_dispatch},
                "$set": {
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )
