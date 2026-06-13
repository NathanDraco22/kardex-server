from typing import Any, AsyncGenerator
from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection

from kardex.tools import TimeTools, build_query


class InvoicesCollection(BaseMongoCollection):
    collection_name = "Invoices"

    async def create_invoice(self, invoice: dict) -> None:
        collection = self._collection
        await collection.insert_one(invoice)

    async def fetch_all_invoices_stream(
        self, **kargs
    ) -> AsyncGenerator[dict[str, Any], None]:
        collection = self._collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)

        cursor = (
            collection.find(result.query)
            .skip(result.offset)
            .limit(result.limit)
            .sort(date_field, -1)
        )

        async for result in cursor:
            yield result

    async def fetch_all_invoices(self, **kargs) -> list[dict[str, Any]]:
        collection = self._collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)

        cursor = (
            collection.find(result.query)
            .skip(result.offset)
            .limit(result.limit)
            .sort(date_field, -1)
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_all_invoices_by_product(
        self, product_id: str, **kargs
    ) -> list[dict[str, Any]]:
        collection = self._collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)
        result.query["saleItems.product.id"] = product_id

        cursor = (
            collection.find(result.query)
            .skip(result.offset)
            .limit(result.limit)
            .sort(date_field, -1)
        )

        result_list = await cursor.to_list(length=None)
        await cursor.close()

        return result_list

    async def fetch_all_product_sales(self, **kargs) -> list[dict[str, Any]]:
        collection = self._collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)

        pipeline = [
            {"$match": result.query},
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

    async def fetch_all_invoices_by(
        self,
        client_id: str,
        offset: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find({"clientId": client_id})

        cursor = cursor.sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_pending_to_paid_invoices(
        self, client_id: str
    ) -> list[dict[str, Any]]:
        collection = self._collection
        cursor = collection.find(
            {
                "clientId": client_id,
                "status": {"$ne": "paid"},
            }
        )

        result = await cursor.sort("createdAt", -1).to_list(length=None)
        await cursor.close()

        return result

    async def fetch_invoice_by_id(self, invoice_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": invoice_id})
        return result

    async def fetch_invoice_by_id_with_session(
        self, invoice_id: str, session: Any
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": invoice_id}, session=session)
        return result

    async def fetch_invoice_by_doc_number(
        self, docNumber: str
    ) -> dict[str, Any] | None:
        collection = self._collection

        query = {
            "docNumber": docNumber,
        }

        result = await collection.find_one(query)
        return result

    async def update_invoice_by_id(
        self,
        invoice_id: str,
        invoice: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            {"$set": invoice},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def create_invoice_with_session(self, invoice: dict, session: Any) -> dict:
        collection = self._collection
        await collection.insert_one(
            invoice,
            session=session,
        )

        return invoice

    async def add_to_amount_paid(self, invoice_id: str, amount_paid: int, session: Any):
        collection = self._collection

        pipeline = [
            {
                "$set": {
                    "amountPaid": {
                        "$add": ["$amountPaid", amount_paid],
                    },
                },
            },
            {
                "$set": {
                    "status": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$total"]},
                            "then": "paid",
                            "else": "partiallyPaid",
                        }
                    },
                    "paidAt": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$total"]},
                            "then": TimeTools.get_now_in_milliseconds(),
                            "else": None,
                        }
                    },
                }
            },
        ]

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            pipeline,
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def subtract_from_amount_paid(
        self, invoice_id: str, amount_paid: int, session: Any
    ) -> dict[str, Any] | None:
        collection = self._collection

        pipeline = [
            {
                "$set": {
                    "amountPaid": {
                        "$subtract": ["$amountPaid", amount_paid],
                    },
                },
            },
            {
                "$set": {
                    "status": {
                        "$cond": {
                            "if": {"$lte": ["$amountPaid", 0]},
                            "then": "open",
                            "else": "partiallyPaid",
                        }
                    },
                    "paidAt": {
                        "$cond": {
                            "if": {"$lte": ["$amountPaid", 0]},
                            "then": None,
                            "else": "$paidAt",
                        }
                    },
                }
            },
        ]

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            pipeline,
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def update_invoice_by_id_with_session(
        self,
        invoice_id: str,
        invoice: dict,
        session: Any,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": invoice_id},
            {"$set": invoice},
            session=session,
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def get_totals_from_invoices(self, **kargs) -> dict[str, Any]:
        collection = self._collection

        date_field = "paidAt" if kargs.get("byPaidAt") else "createdAt"

        result = build_query(date_field, **kargs)

        cursor = await collection.aggregate(
            [
                {"$match": result.query},
                {
                    "$group": {
                        "_id": None,
                        "totalCost": {"$sum": "$totalCost"},
                        "total": {"$sum": "$total"},
                        "count": {"$sum": 1},
                    }
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        if result:
            data = result[0]
            return data

        return {
            "totalCost": 0,
            "total": 0,
        }

    async def get_totals_from_invoices_by_payment_type(
        self,
        **kwargs,
    ) -> list[dict[str, Any]]:
        collection = self._collection

        query = {}

        payment_type = kwargs.pop("paymentType", None)
        ne_type = kwargs.pop("nePaymentType", None)

        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)

        query = kwargs

        if not start_date or not end_date:
            return []

        query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        if payment_type:
            query["paymentType"] = payment_type

        if ne_type:
            query["paymentType"] = {"$ne": ne_type}

        query = {key: value for key, value in query.items() if value is not None}

        cursor = await collection.aggregate(
            [
                {"$match": query},
                {
                    "$group": {
                        "_id": "$paymentType",
                        "totalCost": {"$sum": "$totalCost"},
                        "total": {"$sum": "$total"},
                        "count": {"$sum": 1},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "paymentType": "$_id",
                        "totalCost": 1,
                        "total": 1,
                        "count": 1,
                    }
                },
            ]
        )

        result = await cursor.to_list(length=None)
        await cursor.close()

        if result:
            return result

        return []

    async def get_invoice_resume(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {}

        start_date = kwargs.pop("startDate", None)
        end_date = kwargs.pop("endDate", None)

        if not start_date or not end_date:
            return []

        query["createdAt"] = {"$gte": start_date, "$lte": end_date}

        query["status"] = {"$in": ["open", "paid", "partiallyPaid"]}

        pipeline = [
            # 1. Filtramos solo las ventas reales (ignoramos borradores y canceladas)
            {"$match": query},
            # 2. Agrupamos por sucursal y hacemos los cálculos condicionales
            {
                "$group": {
                    "_id": "$branchId",
                    "totalSales": {"$sum": "$total"},
                    "totalCost": {"$sum": "$totalCost"},
                    "totalPaid": {"$sum": "$amountPaid"},
                    # Cartera: Lo que falta por pagar
                    "totalOwed": {"$sum": {"$subtract": ["$total", "$amountPaid"]}},
                    # Crédito: Suma solo si es "credit"
                    "creditSales": {
                        "$sum": {
                            "$cond": [{"$eq": ["$paymentType", "credit"]}, "$total", 0]
                        }
                    },
                    # Contado: Suma todo lo que NO sea "credit"
                    "cashSales": {
                        "$sum": {
                            "$cond": [{"$ne": ["$paymentType", "credit"]}, "$total", 0]
                        }
                    },
                    "totalInvoices": {"$sum": 1},
                }
            },
            # 3. Limpiamos la salida para el formato final
            {
                "$project": {
                    "_id": 0,
                    "branchId": "$_id",
                    "totalSales": 1,
                    "totalCost": 1,
                    "totalPaid": 1,
                    "totalOwed": 1,
                    "creditSales": 1,
                    "cashSales": 1,
                    "totalInvoices": 1,
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)

        result = await cursor.to_list(length=None)
        await cursor.close()

        if result:
            return result

        return []

    async def get_pending_invoice_totals_by_branch(
        self, **kwargs
    ) -> list[dict[str, Any]]:
        collection = self._collection

        query = {}
        query["status"] = {"$in": ["open", "partiallyPaid"]}

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$branchId",
                    "total": {"$sum": "$total"},
                    "totalCost": {"$sum": "$totalCost"},
                    "amountPaid": {"$sum": "$amountPaid"},
                    "totalOwed": {"$sum": {"$subtract": ["$total", "$amountPaid"]}},
                    "count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "branchId": "$_id",
                    "total": 1,
                    "totalCost": 1,
                    "amountPaid": 1,
                    "totalOwed": 1,
                    "count": 1,
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)

        result = await cursor.to_list(length=None)
        await cursor.close()

        if result:
            return result

        return []

    async def fetch_invoice_history(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {key: value for key, value in kwargs.items() if value is not None}

        offset = query.pop("offset", 0)
        limit = query.pop("limit", 50)

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def create_indexes(self):
        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("status", 1)]),
                IndexModel([("id", 1)], unique=True),
                IndexModel([("clientId", 1), ("status", 1), ("docDate", -1)]),
                IndexModel([("paymentType", 1)]),
                IndexModel([("saleItems.product.id", 1)]),
                IndexModel([("branchId", 1), ("saleItems.product.id", 1)]),
                IndexModel([("branchId", 1), ("createdAt", -1)]),
                IndexModel([("createdAt", -1)]),
                IndexModel([("paidAt", -1)]),
                IndexModel([("createdBy.id", 1)]),
            ]
        )
