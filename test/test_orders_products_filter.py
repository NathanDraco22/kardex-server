from unittest.mock import AsyncMock, MagicMock

import pytest

from kardex.services.mongo_collections.v1.orders_collection import OrdersCollection


@pytest.mark.asyncio
async def test_fetch_products_in_orders_applies_date_range_client_and_user() -> None:
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[])
    cursor.close = AsyncMock()

    mock_collection = MagicMock()
    mock_collection.aggregate = AsyncMock(return_value=cursor)

    orders_collection = OrdersCollection.__new__(OrdersCollection)
    orders_collection._collection = mock_collection

    await orders_collection.fetch_products_in_orders(
        branchId="branch-1",
        startDate=1_700_000_000_000,
        endDate=1_700_086_400_000,
        neStatus="cancelled",
        clientId="client-99",
        createdBy="seller-7",
    )

    pipeline = mock_collection.aggregate.call_args.args[0]
    match_stage = pipeline[0]["$match"]

    assert match_stage == {
        "branchId": "branch-1",
        "clientId": "client-99",
        "status": {"$ne": "cancelled"},
        "createdAt": {"$gte": 1_700_000_000_000, "$lte": 1_700_086_400_000},
        "createdBy.id": "seller-7",
    }
