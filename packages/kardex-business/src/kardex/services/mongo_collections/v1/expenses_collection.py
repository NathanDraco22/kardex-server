from datetime import datetime
from typing import Any

from pymongo import ReturnDocument, IndexModel
from kardex.services import BaseMongoCollection
from kardex.tools import TimeTools


class ExpensesCollection(BaseMongoCollection):
    collection_name = "Expenses"

    async def create_expense(self, expense: dict, session: Any = None) -> None:
        collection = self._collection
        await collection.insert_one(expense, session=session)

    async def create_many_expenses_with_session(
        self, expenses: list[dict[str, Any]], session: Any
    ) -> None:
        collection = self._collection
        if expenses:
            await collection.insert_many(expenses, session=session)

    async def fetch_existing_doc_numbers(
        self, doc_numbers: list[str], include_deleted: bool = True
    ) -> set[str]:
        if not doc_numbers:
            return set()
        collection = self._collection
        query: dict[str, Any] = {"docNumber": {"$in": doc_numbers}}
        if not include_deleted:
            query["isDeleted"] = False
        cursor = collection.find(query, {"docNumber": 1})
        rows = await cursor.to_list(length=None)
        await cursor.close()
        return {
            row["docNumber"]
            for row in rows
            if isinstance(row.get("docNumber"), str) and row["docNumber"]
        }

    async def fetch_all_expenses(self, **kwargs) -> list[dict[str, Any]]:
        collection = self._collection

        query = {"isDeleted": False}

        params = kwargs.copy()
        offset = params.pop("offset", 0)
        limit = params.pop("limit", 50)

        query.update(params)

        cursor = collection.find(query).sort("createdAt", -1).skip(offset).limit(limit)
        result = await cursor.to_list(length=None)
        await cursor.close()
        return result

    async def fetch_expense_by_id(self, expense_id: str) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one({"id": expense_id, "isDeleted": False})
        return result

    async def fetch_expense_by_doc_number(
        self, doc_number: str
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one(
            {"docNumber": doc_number, "isDeleted": False}
        )
        return result

    async def update_expense_by_id(
        self,
        expense_id: str,
        expense: dict,
    ) -> dict[str, Any] | None:
        collection = self._collection

        result = await collection.find_one_and_update(
            {"id": expense_id, "isDeleted": False},
            {"$set": expense},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def update_expenses_category(
        self, old_category: str, new_category: str, session: Any
    ):
        collection = self._collection

        await collection.update_many(
            {
                "category": old_category,
            },
            {"$set": {"category": new_category}},
            session=session,
        )

    async def delete_expense_by_id(
        self, expense_id: str, session: Any = None
    ) -> dict[str, Any] | None:
        collection = self._collection
        result = await collection.find_one_and_update(
            {"id": expense_id, "isDeleted": False},
            {
                "$set": {
                    "isDeleted": True,
                    "deletedAt": TimeTools.get_now_in_milliseconds(),
                }
            },
            return_document=ReturnDocument.AFTER,
            session=session,
        )
        return result

    async def add_to_amount_paid(
        self,
        expense_id: str,
        amount_paid: int,
        payment_record: dict[str, Any] | None = None,
        session: Any = None,
    ) -> dict[str, Any] | None:
        collection = self._collection
        now_ms = TimeTools.get_now_in_milliseconds()
        paid_at_value = (
            payment_record["paidAt"]
            if payment_record is not None and payment_record.get("paidAt") is not None
            else now_ms
        )

        first_stage: dict[str, Any] = {
            "amountPaid": {
                "$add": [{"$ifNull": ["$amountPaid", 0]}, amount_paid],
            },
            "updatedAt": now_ms,
        }
        if payment_record is not None:
            first_stage["payments"] = {
                "$concatArrays": [
                    {"$ifNull": ["$payments", []]},
                    [payment_record],
                ]
            }

        pipeline = [
            {"$set": first_stage},
            {
                "$set": {
                    "status": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$amount"]},
                            "then": "paid",
                            "else": "partiallyPaid",
                        }
                    },
                    "paidAt": {
                        "$cond": {
                            "if": {"$gte": ["$amountPaid", "$amount"]},
                            "then": paid_at_value,
                            "else": None,
                        }
                    },
                }
            },
        ]

        query: dict[str, Any] = {
            "id": expense_id,
            "isDeleted": False,
            "isActive": True,
            "status": {"$nin": ["paid", "cancelled"]},
            "$expr": {
                "$lte": [
                    {"$add": [{"$ifNull": ["$amountPaid", 0]}, amount_paid]},
                    "$amount",
                ]
            },
        }

        result = await collection.find_one_and_update(
            query,
            pipeline,
            return_document=ReturnDocument.AFTER,
            session=session,
        )

        return result

    async def get_accounts_payable_summary(
        self,
        branch_id: str | None = None,
        overdue_cutoff_ms: int | None = None,
    ) -> dict[str, Any]:
        collection = self._collection
        if overdue_cutoff_ms is None:
            now_dt = datetime.now(TimeTools.default_timezone).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            overdue_cutoff_ms = int(now_dt.timestamp() * 1000)

        match_query: dict[str, Any] = {
            "isDeleted": False,
            "isActive": True,
            "type": "supplier",
            "status": {"$in": ["draft", "open", "partiallyPaid"]},
        }
        if branch_id:
            match_query["branchId"] = branch_id

        effective_paid_expr: dict[str, Any] = {
            "$min": ["$amount", {"$max": [0, {"$ifNull": ["$amountPaid", 0]}]}]
        }

        pipeline: list[dict[str, Any]] = [
            {"$match": match_query},
            {
                "$addFields": {
                    "effectivePaid": effective_paid_expr,
                    "remaining": {
                        "$max": [
                            0,
                            {"$subtract": ["$amount", effective_paid_expr]},
                        ]
                    },
                    "isOverdue": {
                        "$and": [
                            {"$ne": ["$expirationDate", None]},
                            {"$lt": ["$expirationDate", overdue_cutoff_ms]},
                        ]
                    },
                    "groupKey": {
                        "$cond": [
                            {
                                "$gt": [
                                    {"$strLenCP": {"$ifNull": ["$supplierId", ""]}},
                                    0,
                                ]
                            },
                            "$supplierId",
                            {
                                "$let": {
                                    "vars": {
                                        "trimmedName": {
                                            "$trim": {
                                                "input": {"$ifNull": ["$supplierName", ""]}
                                            }
                                        }
                                    },
                                    "in": {
                                        "$cond": [
                                            {"$gt": [{"$strLenCP": "$$trimmedName"}, 0]},
                                            "$$trimmedName",
                                            "SIN_PROVEEDOR",
                                        ]
                                    },
                                }
                            },
                        ]
                    },
                }
            },
            {"$match": {"remaining": {"$gt": 0}}},
            {
                "$group": {
                    "_id": "$groupKey",
                    "supplierId": {"$first": {"$ifNull": ["$supplierId", ""]}},
                    "supplierName": {
                        "$first": {
                            "$cond": [
                                {
                                    "$gt": [
                                        {
                                            "$strLenCP": {
                                                "$ifNull": ["$supplierName", ""]
                                            }
                                        },
                                        0,
                                    ]
                                },
                                "$supplierName",
                                "Proveedor sin nombre",
                            ]
                        }
                    },
                    "totalAmount": {"$sum": "$amount"},
                    "totalPaid": {"$sum": "$effectivePaid"},
                    "pendingAmount": {"$sum": "$remaining"},
                    "overdueAmount": {
                        "$sum": {"$cond": ["$isOverdue", "$remaining", 0]}
                    },
                    "pendingCount": {"$sum": 1},
                    "overdueCount": {"$sum": {"$cond": ["$isOverdue", 1, 0]}},
                    "oldestDueDate": {"$min": "$expirationDate"},
                }
            },
            {
                "$sort": {
                    "overdueAmount": -1,
                    "pendingAmount": -1,
                    "supplierName": 1,
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        rows = await cursor.to_list(length=None)
        await cursor.close()

        suppliers: list[dict[str, Any]] = []
        total_pending = 0
        total_overdue = 0
        documents_count = 0

        for row in rows:
            pending_amount = int(row.get("pendingAmount", 0))
            overdue_amount = int(row.get("overdueAmount", 0))
            pending_count = int(row.get("pendingCount", 0))

            suppliers.append(
                {
                    "supplierId": row.get("supplierId", "") or "",
                    "supplierName": row.get("supplierName", "Proveedor sin nombre"),
                    "totalAmount": int(row.get("totalAmount", 0)),
                    "totalPaid": int(row.get("totalPaid", 0)),
                    "pendingAmount": pending_amount,
                    "overdueAmount": overdue_amount,
                    "pendingCount": pending_count,
                    "overdueCount": int(row.get("overdueCount", 0)),
                    "oldestDueDate": row.get("oldestDueDate"),
                }
            )

            total_pending += pending_amount
            total_overdue += overdue_amount
            documents_count += pending_count

        return {
            "totalPending": total_pending,
            "totalOverdue": total_overdue,
            "suppliersCount": len(suppliers),
            "documentsCount": documents_count,
            "suppliers": suppliers,
        }

    async def get_expenses_summary_in_range(
        self, start_date: int, end_date: int
    ) -> dict[str, Any]:
        collection = self._collection

        query = {
            "isDeleted": False,
            "isActive": True,
            "createdAt": {"$gte": start_date, "$lte": end_date},
        }

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$branchId",
                    "expensesTotal": {"$sum": "$amount"},
                    "expensesPaid": {
                        "$sum": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$status", "paid"]}, "then": "$amount"},
                                    {
                                        "case": {"$eq": ["$status", "partiallyPaid"]},
                                        "then": {
                                            "$min": [
                                                "$amount",
                                                {"$max": [0, {"$ifNull": ["$amountPaid", 0]}]},
                                            ]
                                        },
                                    },
                                ],
                                "default": 0,
                            }
                        }
                    },
                }
            },
        ]

        cursor = await collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        await cursor.close()

        branches_map = {}
        global_total = 0
        global_paid = 0

        for row in results:
            b_id = row["_id"]
            total = row.get("expensesTotal", 0)
            paid = row.get("expensesPaid", 0)
            branches_map[b_id] = {
                "expensesTotal": total,
                "expensesPaid": paid,
            }
            global_total += total
            global_paid += paid

        return {
            "branches": branches_map,
            "expensesTotal": global_total,
            "expensesPaid": global_paid,
        }

    async def get_expenses_totals_in_range(
        self,
        start_date: int,
        end_date: int,
        branch_id: str,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        collection = self._collection

        query: dict[str, Any] = {
            "isDeleted": False,
            "isActive": True,
            "branchId": branch_id,
            "date": {"$gte": start_date, "$lte": end_date},
        }

        if user_id is not None:
            query["createdBy.id"] = user_id

        pipeline = [
            {"$match": query},
            {
                "$group": {
                    "_id": "$type",
                    "total": {"$sum": "$amount"},
                    "paid": {
                        "$sum": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": ["$status", "paid"]}, "then": "$amount"},
                                    {
                                        "case": {"$eq": ["$status", "partiallyPaid"]},
                                        "then": {
                                            "$min": [
                                                "$amount",
                                                {"$max": [0, {"$ifNull": ["$amountPaid", 0]}]},
                                            ]
                                        },
                                    },
                                ],
                                "default": 0,
                            }
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        cursor = await collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        await cursor.close()

        by_type: list[dict[str, Any]] = []
        global_total = 0
        global_paid = 0
        global_count = 0

        for row in results:
            total = row.get("total", 0)
            paid = row.get("paid", 0)
            count = row.get("count", 0)

            by_type.append(
                {
                    "type": row.get("_id"),
                    "total": total,
                    "paid": paid,
                    "pending": total - paid,
                    "count": count,
                }
            )

            global_total += total
            global_paid += paid
            global_count += count

        return {
            "total": global_total,
            "paid": global_paid,
            "pending": global_total - global_paid,
            "count": global_count,
            "byType": by_type,
        }

    async def create_indexes(self):

        collection = self._collection
        await collection.create_indexes(
            [
                IndexModel([("id", 1)], unique=True),
                IndexModel([("docNumber", 1)], unique=True),
                IndexModel([("branchId", 1)]),
                IndexModel([("dateId", 1)]),
                IndexModel([("createdAt", -1)]),
                IndexModel([("type", 1), ("createdAt", -1)]),
                IndexModel([("branchId", 1), ("date", -1)]),
                IndexModel([("shiftId", 1)]),
                IndexModel(
                    [("branchId", 1), ("type", 1), ("status", 1), ("supplierId", 1)]
                ),
            ]
        )
