from unittest.mock import AsyncMock, MagicMock

import pytest

from kardex.services.mongo_collections.v1.invoices_collection import InvoicesCollection


@pytest.mark.asyncio
async def test_fetch_all_invoices_by_product_excludes_cancelled_and_applies_filters() -> None:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[])
    cursor.close = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.find.return_value = cursor

    invoices_collection = InvoicesCollection.__new__(InvoicesCollection)
    invoices_collection._collection = mock_collection

    await invoices_collection.fetch_all_invoices_by_product(
        "prod-1",
        branchId="branch-1",
        clientId="client-9",
        startDate=1_700_000_000_000,
        endDate=1_700_086_400_000,
        createdBy="seller-7",
    )

    query = mock_collection.find.call_args.args[0]

    assert query == {
        "clientId": "client-9",
        "branchId": "branch-1",
        "status": {"$ne": "cancelled"},
        "createdAt": {"$gte": 1_700_000_000_000, "$lte": 1_700_086_400_000},
        "createdBy.id": "seller-7",
        "saleItems.product.id": "prod-1",
    }
    cursor.sort.assert_called_once_with([("createdAt", -1), ("id", -1)])

    await invoices_collection.fetch_all_invoices_by_product(
        "prod-1",
        branchId="branch-1",
        status="cancelled",
    )

    query_with_status = mock_collection.find.call_args.args[0]
    assert query_with_status["status"] == "cancelled"


@pytest.mark.asyncio
async def test_fetch_all_invoices_by_product_uses_cursor_pagination() -> None:
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = cursor
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[])
    cursor.close = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.find.return_value = cursor

    invoices_collection = InvoicesCollection.__new__(InvoicesCollection)
    invoices_collection._collection = mock_collection

    await invoices_collection.fetch_all_invoices_by_product(
        "prod-1",
        branchId="branch-1",
        cursorDate=1_700_000_000_000,
        cursorId="invoice-50",
        limit=50,
    )

    query = mock_collection.find.call_args.args[0]

    assert query["$or"] == [
        {"createdAt": {"$lt": 1_700_000_000_000}},
        {"createdAt": 1_700_000_000_000, "id": {"$lt": "invoice-50"}},
    ]
    cursor.skip.assert_called_once_with(0)
    cursor.limit.assert_called_once_with(50)
    cursor.sort.assert_called_once_with([("createdAt", -1), ("id", -1)])


@pytest.mark.asyncio
async def test_fetch_product_sales_summary_aggregates_only_product_lines() -> None:
    cursor = MagicMock()
    cursor.to_list = AsyncMock(
        return_value=[
            {
                "invoiceCount": 2,
                "totalQuantity": 5,
                "totalBonQuantity": 1,
                "total": 12_500,
            }
        ]
    )
    cursor.close = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.aggregate = AsyncMock(return_value=cursor)

    invoices_collection = InvoicesCollection.__new__(InvoicesCollection)
    invoices_collection._collection = mock_collection

    result = await invoices_collection.fetch_product_sales_summary(
        "prod-1",
        branchId="branch-1",
        clientId="client-9",
        startDate=1_700_000_000_000,
        endDate=1_700_086_400_000,
        createdBy="seller-7",
    )

    assert result == {
        "productId": "prod-1",
        "invoiceCount": 2,
        "totalQuantity": 5,
        "totalBonQuantity": 1,
        "total": 12_500,
    }

    pipeline = mock_collection.aggregate.call_args.args[0]

    assert pipeline[0]["$match"] == {
        "clientId": "client-9",
        "branchId": "branch-1",
        "status": {"$ne": "cancelled"},
        "createdAt": {"$gte": 1_700_000_000_000, "$lte": 1_700_086_400_000},
        "createdBy.id": "seller-7",
        "saleItems.product.id": "prod-1",
    }
    assert pipeline[1] == {"$unwind": "$saleItems"}
    assert pipeline[2] == {"$match": {"saleItems.product.id": "prod-1"}}
    assert pipeline[3]["$group"]["invoiceIds"] == {"$addToSet": "$id"}
    assert pipeline[3]["$group"]["total"] == {"$sum": "$saleItems.total"}


@pytest.mark.asyncio
async def test_fetch_product_sales_summary_returns_zeros_without_sales() -> None:
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[])
    cursor.close = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.aggregate = AsyncMock(return_value=cursor)

    invoices_collection = InvoicesCollection.__new__(InvoicesCollection)
    invoices_collection._collection = mock_collection

    result = await invoices_collection.fetch_product_sales_summary(
        "prod-1",
        branchId="branch-1",
    )

    assert result == {
        "productId": "prod-1",
        "totalQuantity": 0,
        "totalBonQuantity": 0,
        "total": 0,
        "invoiceCount": 0,
    }
