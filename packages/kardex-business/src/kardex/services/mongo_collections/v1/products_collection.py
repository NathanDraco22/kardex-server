import re
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
        safe_query = re.escape(text_query)

        pipeline = [
            {
                "$match": {
                    "isDeleted": False,
                    "$or": [
                        {
                            "$text": {
                                "$search": safe_query,
                                "$caseSensitive": False,
                                "$diacriticSensitive": False,
                            }
                        },
                        {
                            "code": {
                                "$regex": f"^{safe_query}",
                                "$options": "i",
                            }
                        },
                        {
                            "altCode": {
                                "$regex": f"^{safe_query}",
                                "$options": "i",
                            }
                        },
                    ]
                }
            },
            {
                "$addFields": {
                    "baseScore": {"$meta": "textScore"},
                    "nameBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$name",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                    "codeBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$code",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                    "altCodeBoost": {
                        "$cond": [
                            {
                                "$regexMatch": {
                                    "input": "$altCode",
                                    "regex": f"^{safe_query}",
                                    "options": "i",
                                }
                            },
                            100,
                            0,
                        ]
                    },
                }
            },
            {"$addFields": {"finalScore": {"$add": [{"$ifNull": ["$baseScore", 0]}, "$nameBoost", "$codeBoost", "$altCodeBoost"]}}},
            {"$sort": {"finalScore": -1, "name": 1}},
            {"$limit": 20},
            {"$project": {"baseScore": 0, "nameBoost": 0, "codeBoost": 0, "altCodeBoost": 0, "finalScore": 0}},
        ]
        cursor = await collection.aggregate(pipeline)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def searchProductWithAccount(
        self,
        branch_id: str,
        text_query: str,
    ) -> list[dict[str, Any]]:
        collection = self._collection
        safe_query = re.escape(text_query)
        cursor = await collection.aggregate(
            [
                {
                    "$match": {
                        "isDeleted": False,
                        "$or": [
                            {
                                "$text": {
                                    "$search": safe_query,
                                    "$caseSensitive": False,
                                    "$diacriticSensitive": False,
                                }
                            },
                            {
                                "code": {
                                    "$regex": f"^{safe_query}",
                                    "$options": "i",
                                }
                            },
                            {
                                "altCode": {
                                    "$regex": f"^{safe_query}",
                                    "$options": "i",
                                }
                            },
                        ]
                    }
                },
                {
                    "$addFields": {
                        "baseScore": {"$meta": "textScore"},
                        "nameBoost": {
                            "$cond": [
                                {
                                    "$regexMatch": {
                                        "input": "$name",
                                        "regex": f"^{safe_query}",
                                        "options": "i",
                                    }
                                },
                                100,
                                0,
                            ]
                        },
                        "codeBoost": {
                            "$cond": [
                                {
                                    "$regexMatch": {
                                        "input": "$code",
                                        "regex": f"^{safe_query}",
                                        "options": "i",
                                    }
                                },
                                100,
                                0,
                            ]
                        },
                        "altCodeBoost": {
                            "$cond": [
                                {
                                    "$regexMatch": {
                                        "input": "$altCode",
                                        "regex": f"^{safe_query}",
                                        "options": "i",
                                    }
                                },
                                100,
                                0,
                            ]
                        },
                    }
                },
                {"$addFields": {"finalScore": {"$add": [{"$ifNull": ["$baseScore", 0]}, "$nameBoost", "$codeBoost", "$altCodeBoost"]}}},
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
                    "$sort": {"finalScore": -1, "name": 1},
                },
                {
                    "$limit": 20,
                },
                {"$project": {"baseScore": 0, "nameBoost": 0, "codeBoost": 0, "altCodeBoost": 0, "finalScore": 0}},
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
        safe_query = re.escape(text_query)
        cursor = await collection.aggregate(
            [
                {
                    "$match": {
                        "isDeleted": False,
                        "$or": [
                            {
                                "$text": {
                                    "$search": safe_query,
                                    "$caseSensitive": False,
                                    "$diacriticSensitive": False,
                                }
                            },
                            {
                                "code": {
                                    "$regex": f"^{safe_query}",
                                    "$options": "i",
                                }
                            },
                            {
                                "altCode": {
                                    "$regex": f"^{safe_query}",
                                    "$options": "i",
                                }
                            },
                        ]
                    }
                },
                {
                    "$addFields": {
                        "baseScore": {"$meta": "textScore"},
                        "nameBoost": {
                            "$cond": [
                                {
                                    "$regexMatch": {
                                        "input": "$name",
                                        "regex": f"^{safe_query}",
                                        "options": "i",
                                    }
                                },
                                100,
                                0,
                            ]
                        },
                        "codeBoost": {
                            "$cond": [
                                {
                                    "$regexMatch": {
                                        "input": "$code",
                                        "regex": f"^{safe_query}",
                                        "options": "i",
                                    }
                                },
                                100,
                                0,
                            ]
                        },
                        "altCodeBoost": {
                            "$cond": [
                                {
                                    "$regexMatch": {
                                        "input": "$altCode",
                                        "regex": f"^{safe_query}",
                                        "options": "i",
                                    }
                                },
                                100,
                                0,
                            ]
                        },
                    }
                },
                {"$addFields": {"finalScore": {"$add": [{"$ifNull": ["$baseScore", 0]}, "$nameBoost", "$codeBoost", "$altCodeBoost"]}}},
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
                    "$sort": {"finalScore": -1, "name": 1},
                },
                {
                    "$limit": 21,
                },
                {"$project": {"baseScore": 0, "nameBoost": 0, "codeBoost": 0, "altCodeBoost": 0, "finalScore": 0}},
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
        cursor = await collection.aggregate(
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

        cursor = await collection.aggregate(
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

        cursor = await collection.aggregate(
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

        cursor = await collection.aggregate(
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

        cursor = await collection.aggregate(
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
        text_index_name = "TextSearchIndex"
        desired_text_weights = {
            "name": 7,
            "code": 3,
            "altCode": 3,
            "brandName": 10,
            "unitName": 5,
            "categoryName": 3,
            "searchPrefixes": 5,
            "tags": 7,
        }

        # Inspeccionar índices existentes para eliminar cualquier índice de texto previo
        # que sea autogenerado o que difiera del nombre/pesos actuales.
        existing_indexes = await collection.index_information()
        for idx_name, idx_info in existing_indexes.items():
            is_text_index = "weights" in idx_info or any(
                k[1] == "text" for k in idx_info.get("key", [])
            )
            if is_text_index:
                current_weights = idx_info.get("weights", {})
                if idx_name != text_index_name or current_weights != desired_text_weights:
                    await collection.drop_index(idx_name)

        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("name", 1)]),
                IndexModel([("code", 1)]),
                IndexModel([("altCode", 1)]),
                IndexModel(
                    [
                        ("name", "text"),
                        ("code", "text"),
                        ("altCode", "text"),
                        ("brandName", "text"),
                        ("unitName", "text"),
                        ("categoryName", "text"),
                        ("tags", "text"),
                        ("searchPrefixes", "text"),
                    ],
                    weights=desired_text_weights,
                    name=text_index_name,
                ),
            ]
        )
