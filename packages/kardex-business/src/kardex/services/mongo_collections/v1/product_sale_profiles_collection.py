from dataclasses import dataclass
from typing import Any

from pymongo import ReturnDocument, IndexModel, UpdateOne
from kardex.services import BaseMongoCollection


@dataclass
class UpdateSaleProfileOperation:
    branchId: str
    productId: str
    data: dict


class ProductSaleProfilesCollection(BaseMongoCollection):
    collection_name = "ProductSaleProfiles"

    async def create_product_sale_profile(self, product_sale_profile: dict) -> None:
        collection = self._collection
        await collection.insert_one(product_sale_profile)

    async def fetch_all_product_sale_profiles(
        self, branch_id: str
    ) -> list[dict[str, Any]]:
        collection = self._collection

        cursor = await collection.aggregate(
            [
                {
                    "$match": {
                        "branchId": branch_id,
                    },
                },
                {
                    "$lookup": {
                        "from": "Products",
                        "localField": "productId",
                        "foreignField": "id",
                        "as": "product",
                        "pipeline": [
                            {
                                "$match": {
                                    "isDeleted": False,
                                },
                            },
                        ],
                    }
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "productId",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                },
                            },
                        ],
                    }
                },
                {
                    "$unwind": "$product",
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$sort": {
                        "product.name": 1,
                    },
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_sale_profile_by_branch_product(
        self,
        branch_id: str,
        product_id: str,
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {
                "branchId": branch_id,
                "productId": product_id,
            }
        )
        return result

    async def update_product_sale_profile_by_id(
        self,
        branch_id: str,
        product_id: str,
        product_sale_profile: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {
                "branchId": branch_id,
                "productId": product_id,
            },
            {"$set": product_sale_profile},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def bulk_update_product_sale_profiles(
        self, update_operations: list[UpdateSaleProfileOperation], session: Any
    ):
        if not update_operations:
            return

        collection = self._collection

        update_ops: list[UpdateOne] = []

        for update_operation in update_operations:
            update_ops.append(
                UpdateOne(
                    {
                        "branchId": update_operation.branchId,
                        "productId": update_operation.productId,
                    },
                    {"$set": update_operation.data},
                )
            )

        await collection.bulk_write(update_ops, session=session)

    async def delete_product_sale_profile_by_id(
        self, product_sale_profile_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete({"id": product_sale_profile_id})
        return result

    async def create_product_sale_profile_with_session(
        self, product_sale_profile: dict, session: Any
    ) -> None:
        collection = self._collection
        await collection.insert_one(
            product_sale_profile,
            session=session,
        )

    async def create_index(self):
        collection = self._collection
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

    async def bulk_create_product_sale_profiles(
        self, product_sale_profiles: list[dict], session: Any
    ):
        if not product_sale_profiles:
            return

        collection = self._collection

        update_operations = [
            UpdateOne(
                {
                    "branchId": product_sale_profile["branchId"],
                    "productId": product_sale_profile["productId"],
                },
                {"$setOnInsert": product_sale_profile},
                upsert=True,
            )
            for product_sale_profile in product_sale_profiles
        ]

        await collection.bulk_write(update_operations, session=session)

    async def create_product_sale_profile_if_not_exist_with_session(
        self,
        branch_id: str,
        product_id: str,
        product_sale_profile: dict,
        session: Any,
    ):
        collection = self._collection

        await collection.find_one_and_update(
            {
                "branchId": branch_id,
                "productId": product_id,
            },
            {"$setOnInsert": product_sale_profile},
            return_document=ReturnDocument.AFTER,
            session=session,
            upsert=True,
        )

    async def update_product_sale_profile_with_session(
        self,
        branch_id: str,
        product_id: str,
        product_sale_profile: dict,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {
                "branchId": branch_id,
                "productId": product_id,
            },
            {"$set": product_sale_profile},
            return_document=ReturnDocument.AFTER,
            session=session,
            upsert=True,
        )

        return result
