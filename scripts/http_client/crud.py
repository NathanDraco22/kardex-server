import asyncio
from httpx import AsyncClient


URL = "http://localhost:8000/api/v1"

created_ids = []
branch_id = ""


async def create_branch():
    json_data = {"name": "test", "description": "test"}

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/branches", json=json_data)
        assert response.status_code == 200
        global branch_id
        branch_id = response.json()["id"]


async def create_account():
    json_data = {"name": "crema", "description": "test"}

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/accounts", json=json_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])

    json_data = {"name": "queso", "description": "test"}

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/accounts", json=json_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])

    json_data = {"name": "leche", "description": "test"}

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/accounts", json=json_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])


async def create_entries():
    json_data = {
        "branchId": branch_id,
        "accountId": created_ids[0],
        "quantity": 100,
        "type": "ENTRY",
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/entries", json=json_data)
        assert response.status_code == 200

    json_data = {
        "branchId": branch_id,
        "accountId": created_ids[1],
        "quantity": 150,
        "type": "ENTRY",
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/entries", json=json_data)
        assert response.status_code == 200

    json_data = {
        "branchId": branch_id,
        "accountId": created_ids[2],
        "quantity": 200,
        "type": "ENTRY",
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/entries", json=json_data)
        assert response.status_code == 200


async def create_exits():
    json_data = {
        "branchId": branch_id,
        "accountId": created_ids[0],
        "quantity": -50,
        "type": "EXIT",
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/exits", json=json_data)
        assert response.status_code == 200

    json_data = {
        "branchId": branch_id,
        "accountId": created_ids[1],
        "quantity": -100,
        "type": "EXIT",
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/exits", json=json_data)
        assert response.status_code == 200

    json_data = {
        "branchId": branch_id,
        "accountId": created_ids[2],
        "quantity": -150,
        "type": "EXIT",
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/exits", json=json_data)
        assert response.status_code == 200


async def create_entry_batch():
    json_data = {
        "branchId": branch_id,
        "type": "ENTRY",
        "items": [
            {"accountId": created_ids[0], "quantity": 10},
            {"accountId": created_ids[1], "quantity": 20},
            {"accountId": created_ids[2], "quantity": 30},
        ],
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/entries/batch", json=json_data)
        assert response.status_code == 200


async def create_exit_batch():
    json_data = {
        "branchId": branch_id,
        "type": "EXIT",
        "items": [
            {"accountId": created_ids[0], "quantity": -10},
            {"accountId": created_ids[1], "quantity": -20},
            {"accountId": created_ids[2], "quantity": -30},
        ],
    }

    async with AsyncClient() as client:
        response = await client.post(f"{URL}/exits/batch", json=json_data)
        assert response.status_code == 200


async def main():
    await create_branch()
    await create_account()
    await create_entries()
    await create_exits()
    await create_entry_batch()
    await create_exit_batch()


asyncio.run(main())
