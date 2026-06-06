from typing import Any, AsyncIterable

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection


class ProductsCollection(BaseMongoCollection):
    collection_name = "Products"

    async def create_product(self, product: dict) -> None:
        collection = self._collection
        await collection.insert_one(product)

    async def create_product_with_session(self, product: dict, session: Any) -> None:
        collection = self._collection
        await collection.insert_one(product, session=session)

    async def create_many_products(self, products: list[dict], session: Any) -> None:
        collection = self._collection
        await collection.insert_many(products, session=session)

    async def fetch_all_products(self) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"isDeleted": False})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_paginated_products(
        self, offset: int, limit: int
    ) -> list[dict[str, Any]]:
        collection = self._collection

        cursor = collection.find({"isDeleted": False})
        cursor = cursor.sort("name", 1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": product_id, "isDeleted": False})
        return result

    async def fetch_product_by_code(self, product_code: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"code": product_code, "isDeleted": False})
        return result

    async def fetch_product_by_ids(
        self, product_ids: list[str]
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"id": {"$in": product_ids}})

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def search_product_by_text(self, text_query: str) -> list[dict[str, Any]]:
        collection = self._collection

        query = {
            "$text": {
                "$search": text_query,
                "$caseSensitive": False,
                "$diacriticSensitive": False,
            },
            "isDeleted": False,
        }

        projection = {"score": {"$meta": "textScore"}}

        cursor = (
            collection.find(query, projection)
            .sort([("score", {"$meta": "textScore"})])
            .limit(7)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def searchProductWithAccount(
        self,
        branch_id: str,
        text_query: str,
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "$and": [
                            {
                                "$text": {
                                    "$search": text_query,
                                    "$caseSensitive": False,
                                    "$diacriticSensitive": False,
                                },
                            },
                            {"isDeleted": False},
                        ]
                    }
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$sort": {"name": 1},
                },
                {
                    "$limit": 7,
                },
            ]
        )

        result = await cursor.to_list(length=None)

        return result

    async def searchProductInBranch(
        self,
        branch_id: str,
        text_query: str,
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "$and": [
                            {
                                "$text": {
                                    "$search": text_query,
                                    "$caseSensitive": False,
                                    "$diacriticSensitive": False,
                                },
                            },
                            {"isDeleted": False},
                        ]
                    }
                },
                {
                    "$sort": {"name": 1},
                },
                {
                    "$limit": 21,
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$lookup": {
                        "from": "ProductSaleProfiles",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "saleProfile",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$saleProfile",
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_products_in_branch_by_ids(
        self,
        branch_id: str,
        product_ids: list[str],
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "id": {"$in": product_ids},
                        "isDeleted": False,
                    }
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {"$unwind": "$account"},
                {
                    "$lookup": {
                        "from": "ProductSaleProfiles",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "saleProfile",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {"$unwind": "$saleProfile"},
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def get_all_product_in_branch(self, **kwargs) -> list[dict[str, Any]]:

        collection = self._collection
        branch_id = kwargs.get("branchId")
        limit = kwargs.get("limit", 50)
        offset = kwargs.get("offset", 0)

        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "isDeleted": False,
                    }
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$lookup": {
                        "from": "ProductSaleProfiles",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "saleProfile",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$saleProfile",
                },
                {
                    "$sort": {"name": 1},
                },
                {
                    "$skip": offset,
                },
                {
                    "$limit": limit,
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def get_all_product_in_branch_streamed(
        self, **kwargs
    ) -> AsyncIterable[dict[str, Any]]:
        collection = self._collection
        branch_id = kwargs.get("branchId")

        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "isDeleted": False,
                    }
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$lookup": {
                        "from": "ProductSaleProfiles",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "saleProfile",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {
                    "$unwind": "$saleProfile",
                },
                {
                    "$sort": {"name": 1},
                },
            ]
        )

        async for document in cursor:
            yield document

    async def get_product_in_branch_by_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self._collection

        cursor = collection.aggregate(
            [
                {
                    "$match": {
                        "id": product_id,
                        "isDeleted": False,
                    }
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {"$unwind": "$account"},
                {
                    "$lookup": {
                        "from": "ProductSaleProfiles",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "saleProfile",
                        "pipeline": [
                            {
                                "$match": {
                                    "branchId": branch_id,
                                }
                            }
                        ],
                    }
                },
                {"$unwind": "$saleProfile"},
            ]
        )

        result = await cursor.to_list(length=1)

        return result[0] if result else None

    async def fetch_all_products_with_accounts(
        self, branch_id: str, page: int, limit: int
    ):
        collection = self._collection

        cursor = collection.aggregate(
            [
                {
                    "$match": {"isDeleted": False},
                },
                {
                    "$lookup": {
                        "from": "ProductAccounts",
                        "localField": "id",
                        "foreignField": "productId",
                        "as": "account",
                    }
                },
                {
                    "$unwind": "$account",
                },
                {
                    "$match": {"account.branchId": branch_id},
                },
                {
                    "$sort": {"name": 1},
                },
                {
                    "$skip": (page - 1) * limit,
                },
                {
                    "$limit": limit,
                },
            ]
        )

        result = await cursor.to_list(length=None)

        return result

    async def update_product_by_id(
        self,
        product_id: str,
        product: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": product_id},
            {"$set": product},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": product_id},
            {"$set": {"isDeleted": True}},
            return_document=ReturnDocument.AFTER,
        )
        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)]),
                IndexModel([("code", 1)]),
                IndexModel(
                    [
                        ("name", "text"),
                        ("code", "text"),
                        ("brandName", "text"),
                        ("unitName", "text"),
                        ("categoryName", "text"),
                        ("tags", "text"),
                        ("searchPrefixes", "text"),
                    ],
                    weights={
                        "name": 7,
                        "code": 3,
                        "brandName": 10,
                        "unitName": 5,
                        "categoryName": 3,
                        "searchPrefixes": 5,
                        "tags": 7,
                    },
                ),
            ]
        )
