import asyncio
import random
from httpx import AsyncClient

URL = "http://localhost:8000/api/v1"

# IDs from scripts/http_client/crud.py
BRANCH_ID = "ORIGIN_BRANCH"
CLIENT_ID = "SALE_CLIENT"

PRODUCT_ID_1 = "8d9700a8-f1ba-4f0f-9845-aa75feef9b2c" #ambroxol jarabe
PRODUCT_ID_2 = "524ecef4-905a-4d63-a1a7-3dd37ad54285" #loratadina jarabe

async def create_anon_invoice(index: int):
    # Randomize quantities slightly for variety
    qty1 = random.randint(1, 5)
    qty2 = random.randint(1, 5)
    
    # Calculate totals (prices based on crud.py values)
    price1 = 5500
    cost1 = 4723

    price2 = 5000
    cost2 = 3713
    
    total1 = qty1 * price1
    total2 = qty2 * price2
    
    total_cost = (qty1 * cost1) + (qty2 * cost2)
    total_amount = total1 + total2

    json_data = {
        "branchId": BRANCH_ID,
        "clientId": CLIENT_ID,
        "saleItems": [
            {
                "product": {
                    "id": PRODUCT_ID_1,
                    "name": "Ambroxol Jarabe",
                    "unitName": "Frasco",
                    "brandName": "Ramos",
                    "code": "",
                    "categoryName": None,
                    "tags": [""],
                },
                "quantity": qty1,
                "bonQuantity": 0,
                "cost": cost1,
                "price": price1,
                "priceName": "precio1",
                "discount": 0,
                "subTotal": total1,
                "total": total1
            },
            {
                "product": {
                    "id": PRODUCT_ID_2,
                    "name": "Loratadina Jarabe",
                    "unitName": "Frasco",
                    "brandName": "Ramos",
                    "code": "",
                    "categoryName": None,
                    "tags": [""],
                },
                "quantity": qty2,
                "bonQuantity": 0,
                "cost": cost2,
                "price": price2,
                "priceName": "precio1",
                "discount": 0,
                "subTotal": total2,
                "total": total2
            },
        ],
        "description": f"Anonymous Invoice {index}",
        "amountPaid": total_amount, # Paid in full
        "status": "paid", # Usually anon invoices are paid immediately
        "paymentType": "cash",
        "totalCost": total_cost,
        "total": total_amount,
        "clientInfo": {
            "name": "Cliente Contado",
            "address": "Ciudad",
            "phone": "00000000",
            "email": ""
        },
        "createdBy": {
            "id": "0001",
            "name": "Admin"
        }
    }

    async with AsyncClient() as client:
        try:
            response = await client.post(f"{URL}/invoices/anon", json=json_data)
            if response.status_code == 200:
                print(f"✅ Invoice {index} created successfully. ID: {response.json().get('id')}")
            else:
                print(f"❌ Failed to create invoice {index}. Status: {response.status_code}")
                print(response.text)
        except Exception as e:
            print(f"❌ Error creating invoice {index}: {e}")

async def main():
    print("🚀 Starting anonymous invoice creation script...")
    for i in range(100): # Create 5 invoices
        await create_anon_invoice(i)
    
    print("✨ Script finished.")

if __name__ == "__main__":
    asyncio.run(main())
