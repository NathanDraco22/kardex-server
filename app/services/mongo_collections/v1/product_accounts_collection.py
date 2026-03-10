from typing import AsyncGenerator
from typing import Any


from pymongo import ReturnDocument, IndexModel, UpdateOne
from pymongo.errors import OperationFailure

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

    async def create_many_product_accounts(
        self, product_accounts: list[dict], session: Any
    ) -> None:
        collection = self.__collection
        await collection.insert_many(product_accounts, session=session)

    async def get_product_account_by_product_and_branch_id(
        self, product_id: str, branch_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one(
            {"productId": product_id, "branchId": branch_id}
        )
        return result

    async def get_accounts_by_branch_id(
        self, branch_id: str, product_ids: list[str], session: Any
    ) -> list[dict[str, Any]]:
        collection = self.__collection

        cursor = collection.find(
            {
                "branchId": branch_id,
                "productId": {"$in": product_ids},
            },
            session=session,
        )

        res = await cursor.to_list(length=None)

        return res

    async def get_product_accounts_by_product(
        self,
        product_id: str,
    ) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find(
            {
                "productId": product_id,
            }
        )

        return await cursor.to_list(length=None)

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

    async def bulk_update_product_account_balance_with_average_cost(
        self,
        branch_id: str,
        bulk_data: list[dict[str, Any]],
        session: Any,
    ) -> bool:
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()

        operations: list[UpdateOne] = []

        for item in bulk_data:
            update_op = UpdateOne(
                {
                    "productId": item["product_id"],
                    "branchId": branch_id,
                },
                {
                    "$inc": {"currentStock": item["qty"]},
                    "$set": {
                        "lastCost": item["last_cost"],
                        "averageCost": item["avg_cost"],
                        "maximumCost": item["max_cost"],
                        "updatedAt": updated_at,
                    },
                    "$setOnInsert": {
                        "createdAt": updated_at,
                        "promiseStock": 0,
                    },
                },
                upsert=True,
            )
            operations.append(update_op)

        result = await collection.bulk_write(
            operations,
            ordered=True,
            session=session,
        )

        total_processed = result.matched_count + result.upserted_count

        if total_processed < len(operations):
            raise OperationFailure(
                f"No se pudieron procesar todas las entradas de inventario. "
                f"(Procesados: {total_processed}/{len(operations)})"
            )

        return True

    async def bulk_substract_product_account_data(
        self,
        branch_id: str,
        bulk_to_substrack: list[tuple[str, int]],
        session: Any,
    ) -> bool:
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()

        operations: list[UpdateOne] = []
        for update_element in bulk_to_substrack:
            product_id, substract_to_current_stock = update_element

            qty = abs(substract_to_current_stock)

            update_op = UpdateOne(
                {
                    "productId": product_id,
                    "branchId": branch_id,
                    "$expr": {
                        "$gte": [
                            {
                                "$subtract": [
                                    {"$ifNull": ["$currentStock", 0]},
                                    {"$ifNull": ["$promiseStock", 0]},
                                ]
                            },
                            qty,
                        ]
                    },
                },
                {
                    "$inc": {
                        "currentStock": -qty,
                    },
                    "$set": {
                        "updatedAt": updated_at,
                    },
                },
            )
            operations.append(update_op)

        result = await collection.bulk_write(
            operations,
            ordered=True,
            session=session,
        )

        if result.matched_count < len(operations):
            raise OperationFailure(
                f"No se pudieron actualizar todos los productos. "
                f"(Match: {result.matched_count}/{len(operations)}). "
                "Es posible que el stock disponible (Físico - Prometido) sea insuficiente."
            )

        return True

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

    async def bulk_add_to_promise_stock(
        self,
        branch_id: str,
        bulk_data: list[tuple[str, int]],
        session: Any,
    ) -> bool:
        """
        Incrementa masivamente el stock prometido (Reserva).
        Valida que: (Current - Promise) >= Cantidad a reservar.
        """
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()

        operations: list[UpdateOne] = []

        for product_id, quantity in bulk_data:
            qty_to_reserve = abs(quantity)

            op = UpdateOne(
                {
                    "productId": product_id,
                    "branchId": branch_id,
                    "$expr": {
                        "$gte": [
                            {
                                "$subtract": [
                                    {"$ifNull": ["$currentStock", 0]},
                                    {"$ifNull": ["$promiseStock", 0]},
                                ]
                            },
                            qty_to_reserve,
                        ]
                    },
                },
                {
                    "$inc": {
                        "promiseStock": qty_to_reserve,
                    },
                    "$set": {
                        "updatedAt": updated_at,
                    },
                },
            )
            operations.append(op)

        if not operations:
            return True

        result = await collection.bulk_write(
            operations,
            ordered=True,
            session=session,
        )

        if result.matched_count < len(operations):
            raise Exception(
                f"No se pudo reservar el stock para todos los productos. "
                f"(Match: {result.matched_count}/{len(operations)}). "
                "Stock disponible insuficiente (Físico - Prometido) para realizar la reserva."
            )

        return True

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

    async def bulk_substract_from_promise_stock(
        self,
        branch_id: str,
        bulk_data: list[tuple[str, int]],
        session: Any,
    ) -> bool:
        """
        Libera masivamente stock prometido (Ej: Cancelación de Pedido).
        Resta del promiseStock, pero NO toca el currentStock.
        """
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()

        operations: list[UpdateOne] = []

        for product_id, quantity in bulk_data:
            qty_to_release = abs(quantity)

            op = UpdateOne(
                {
                    "productId": product_id,
                    "branchId": branch_id,
                    "promiseStock": {"$gte": qty_to_release},
                },
                {
                    "$inc": {
                        "promiseStock": -qty_to_release,
                    },
                    "$set": {
                        "updatedAt": updated_at,
                    },
                },
            )
            operations.append(op)

        if not operations:
            return True

        result = await collection.bulk_write(
            operations,
            ordered=True,
            session=session,
        )

        if result.matched_count < len(operations):
            raise Exception(
                f"No se pudo liberar el stock prometido. "
                f"(Match: {result.matched_count}/{len(operations)}). "
                "Inconsistencia detectada: El stock prometido en BD es menor al que intentas liberar."
            )

        return True

    async def adjust_product_stock_only(
        self,
        product_id: str,
        branch_id: str,
        quantity_delta: int,
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
                            "$add": [{"$ifNull": ["$currentStock", 0]}, quantity_delta]
                        },
                        "updatedAt": update_at,
                        "createdAt": {"$ifNull": ["$createdAt", update_at]},
                    }
                },
            ],
            upsert=True,
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_product_account_balance_with_average_cost(
        self,
        product_id: str,
        branch_id: str,
        add_to_current_stock: int,
        last_cost: int,
        average_cost: int,
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
                        "averageCost": average_cost,
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
                        ("productId", 1),
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
                        "count": {"$sum": 1},
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

    async def bulk_dispatch_promise_stock(
        self,
        branch_id: str,
        bulk_data: list[tuple[str, int]],
        session: Any,
    ) -> bool:
        """
        Versión masiva de dispatch_promise_stock.
        Resta Current y Promise al mismo tiempo.
        """
        collection = self.__collection
        updated_at = TimeTools.get_now_in_milliseconds()

        operations = []
        for p_id, qty in bulk_data:
            op = UpdateOne(
                {
                    "productId": p_id,
                    "branchId": branch_id,
                    "promiseStock": {"$gte": qty},
                },
                {
                    "$inc": {
                        "promiseStock": -qty,
                        "currentStock": -qty,
                    },
                    "$set": {"updatedAt": updated_at},
                },
            )
            operations.append(op)

        if not operations:
            return True

        result = await collection.bulk_write(operations, session=session)

        if result.matched_count < len(operations):
            raise OperationFailure(
                f"No se pudo despachar el stock prometido para todos los items. "
                f"(Match: {result.matched_count}/{len(operations)}). "
                "Posible inconsistencia en promiseStock."
            )

        return True

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
