from typing import Any
from datetime import datetime

from pymongo import ReturnDocument

from services import MongoService


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
            {"product_id": product_id, "branch_id": branch_id}
        )
        return result

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
        updated_at = datetime.now()
        result = await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
                "currentStock": {"$gte": abs(substract_to_current_stock)},
            },
            {
                "$inc": {
                    "currentStock": substract_to_current_stock,
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
        update_at = datetime.now()

        result = await collection.find_one_and_update(
            {
                "productId": product_id,
                "branchId": branch_id,
            },
            [
                {
                    "$set": {
                        # Usamos $ifNull para manejar el caso de un documento nuevo
                        "currentStock": {
                            "$add": [
                                {"$ifNull": ["$currentStock", 0]},
                                add_to_current_stock,
                            ]
                        },
                        "lastCost": last_cost,
                        "averageCost": {
                            # Tu cálculo con $round y $convert ya es robusto
                            # Solo necesita $ifNull para el caso de la creación
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
                    }
                }
            ],
            # AÑADIMOS UPSERT=TRUE
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result
