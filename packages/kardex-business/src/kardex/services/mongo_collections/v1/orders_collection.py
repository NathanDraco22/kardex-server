from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection

from kardex.tools import TimeTools


class OrdersCollection(BaseMongoCollection):
    collection_name = "Orders"

    async def create_order(self, order: dict) -> None:
        collection = self._collection
        await collection.insert_one(order)

    async def create_order_with_session(self, order: dict, session: Any) -> dict:
        collection = self._collection
        await collection.insert_one(order, session=session)
        return order

    async def fetch_paginated_orders(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        skip = kwargs.pop("skip", 0)
        limit = kwargs.pop("limit", 50)
        status = kwargs.pop("status", None)
        ne_status = kwargs.pop("neStatus", None)
        cliend_id = kwargs.pop("clientId", None)
        branch_id = kwargs.pop("branchId", None)

        created_by = kwargs.pop("createdBy", None)

        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)

        query = {}

        if branch_id:
            query["branchId"] = branch_id

        if cliend_id:
            query["clientId"] = cliend_id

        if status:
            query["status"] = status

        if ne_status:
            query["status"] = {"$ne": ne_status}

        if created_by:
            query["createdBy.id"] = created_by

        if start_date and end_date:
            query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        cursor = collection.find(query).sort("createdAt", -1).skip(skip).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_products_in_orders(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection
        branch_id = kwargs.pop("branchId", None)
        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)
        neStatus = kwargs.pop("neStatus", None)
        created_by_param = kwargs.pop("createdBy", None)

        query = {}

        if branch_id:
            query["branchId"] = branch_id

        if neStatus:
            query["status"] = {"$ne": neStatus}

        if start_date and end_date:
            query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        if created_by_param:
            query["createdBy.id"] = created_by_param

        pipeline = [
            {"$match": query},
            {"$unwind": "$saleItems"},
            {
                "$group": {
                    "_id": "$saleItems.product.id",
                    "productId": {"$first": "$saleItems.product.id"},
                    "productName": {"$first": "$saleItems.product.name"},
                    "totalQuantity": {"$sum": "$saleItems.quantity"},
                    "totalBonQuantity": {"$sum": "$saleItems.bonQuantity"},
                    "total": {"$sum": "$saleItems.total"},
                }
            },
            {"$sort": {"productName": 1}},
        ]

        cursor = await collection.aggregate(pipeline)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_demand_vs_stock(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection
        branch_id = kwargs.pop("branchId", None)
        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)
        ne_status = kwargs.pop("neStatus", None)
        status = kwargs.pop("status", None)
        created_by = kwargs.pop("createdBy", None)

        if not branch_id:
            # Para cruzar con stock, branchId es obligatorio
            return []

        # Construcción de la query (igual que antes)
        query = {"branchId": branch_id}
        if ne_status:
            query["status"] = {"$ne": ne_status}
        if status:
            query["status"] = status
        if created_by:
            query["createdBy.id"] = created_by

        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["createdAt"] = date_filter

        pipeline = [
            {"$match": query},
            {"$unwind": "$saleItems"},
            {
                "$group": {
                    "_id": "$saleItems.product.id",
                    "productId": {"$first": "$saleItems.product.id"},
                    "productName": {"$first": "$saleItems.product.name"},
                    "totalOrdered": {"$sum": "$saleItems.quantity"},
                    "totalBonification": {"$sum": "$saleItems.bonQuantity"},
                }
            },
            # 🔥 EL CRUCE CON EL STOCK REAL
            {
                "$lookup": {
                    "from": "ProductAccounts",
                    "let": {"pid": "$productId"},
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$productId", "$$pid"]},
                                        {"$eq": ["$branchId", branch_id]},
                                    ]
                                }
                            }
                        }
                    ],
                    "as": "inventory",
                }
            },
            # Aplanamos el inventario (si no hay, el stock es 0)
            {
                "$addFields": {
                    "currentStock": {
                        "$ifNull": [{"$arrayElemAt": ["$inventory.currentStock", 0]}, 0]
                    }
                }
            },
            # Calculamos cuánto falta (Diferencia)
            {
                "$addFields": {
                    "shortage": {
                        "$subtract": [
                            "$currentStock",
                            {"$add": ["$totalOrdered", "$totalBonification"]},
                        ]
                    }
                }
            },
            {
                "$sort": {"shortage": 1}
            },  # Mostramos primero lo que más falta (negativos)
            {"$project": {"inventory": 0}},  # Limpiamos el campo temporal
        ]

        cursor = await collection.aggregate(pipeline)
        result = await cursor.to_list(length=None)
        return result

    async def fetch_order_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": order_id})
        return result

    async def fetch_order_by_doc_number(self, doc_number: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"docNumber": doc_number})
        return result

    async def update_order_draft_by_id(
        self,
        order_id: str,
        order: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {
                "id": order_id,
                "status": "draft",
            },
            {"$set": order},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_order_by_doc_number(
        self,
        doc_number: str,
        order: dict,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"docNumber": doc_number},
            {"$set": order},
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def update_order_status_by_doc_number(
        self,
        doc_number: str,
        status: str,
        session: Any,
    ) -> None:
        collection = self._collection

        await collection.update_one(
            {"docNumber": doc_number},
            {
                "$set": {
                    "status": status,
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                },
            },
            session=session,
        )

    async def delete_order_draft_by_id(self, order_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_delete(
            {
                "id": order_id,
                "status": "draft",
            }
        )
        return result

    async def update_order_status(
        self,
        order_id: str,
        status: str,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self._collection
        return await collection.find_one_and_update(
            {"id": order_id},
            {
                "$set": {
                    "status": status,
                    "updatedAt": TimeTools.get_now_in_milliseconds(),
                },
            },
            session=session,
            return_document=ReturnDocument.AFTER,
        )

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)]),
                IndexModel([("clientId", 1), ("status", 1), ("createdAt", -1)]),
                IndexModel(
                    [("branchId", 1), ("clientId", 1), ("status", 1), ("createdAt", -1)]
                ),
                IndexModel([("status", 1), ("createdAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
                IndexModel([("invoiceId", 1)]),
            ]
        )
