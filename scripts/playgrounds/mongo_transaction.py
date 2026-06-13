import asyncio
from typing import Any
from pymongo import AsyncMongoClient, errors

# Configuración (Requiere Replica Set o MongoDB Atlas)
URI = ""
client = AsyncMongoClient[dict[Any, Any]](URI)
db = client["test_db"]
collection = db["productos"]


async def preparar_datos():
    await collection.drop()
    await collection.insert_one(
        {
            "_id": "refresco_1",
            "nombre": "Coca-Cola",
            "stock": 10,
            "costo": 1.50,  # Nuevo campo: Costo inicial
        }
    )
    print("--- Datos inicializados: Stock = 10, Costo = 1.50 ---\n")


async def transaccion_lenta_t1(nuevo_costo):
    """T1: Lee, espera 3s, resta 1 al stock y actualiza el costo."""
    async with client.start_session() as session:
        try:
            async with await session.start_transaction():
                doc = await collection.find_one({"_id": "refresco_1"}, session=session)
                if doc is None:
                    print(
                        "[T1] ERROR: No se pudo encontrar el producto en la base de datos."
                    )
                    return
                print(f"[T1] Leído -> Stock: {doc['stock']}, Costo: {doc['costo']}")

                print(
                    f"[T1] Simulando proceso pesado. Objetivo: Poner costo en {nuevo_costo}..."
                )
                await asyncio.sleep(3)

                print("[T1] Intentando actualizar stock (-1) y costo...")
                # Intentamos actualizar dos campos a la vez
                await collection.update_one(
                    {"_id": "refresco_1"},
                    {"$inc": {"stock": -1}, "$set": {"costo": nuevo_costo}},
                    session=session,
                )
                print("[T1] Commit exitoso.")
        except errors.PyMongoError as e:
            print(f"[T1] ERROR: {type(e).__name__} - {e}")


async def transaccion_rapida_t2():
    """T2: Modifica stock y costo rápidamente mientras T1 duerme."""
    await asyncio.sleep(1)
    async with client.start_session() as session:
        try:
            async with await session.start_transaction():
                print("[T2] Iniciando rápida...")
                await collection.update_one(
                    {"_id": "refresco_1"},
                    {
                        "$inc": {"stock": -2},
                        # "$set": {"costo": 1.75},  # T2 cambia el costo a 1.75
                    },
                    session=session,
                )
                print("[T2] Commit exitoso (T2 puso stock en 8 y costo en 1.75).")
        except errors.PyMongoError as e:
            print(f"[T2] ERROR: {e}")


async def main():
    await preparar_datos()

    # T1 quiere poner el costo en 2.00 después de 3 segundos
    await asyncio.gather(
        transaccion_lenta_t1(nuevo_costo=2.00), transaccion_rapida_t2()
    )

    final_doc = await collection.find_one({"_id": "refresco_1"})
    if final_doc is None:
        print("No se pudo encontrar el producto en la base de datos.")
        return
    print("\n--- ESTADO FINAL EN DB ---")
    print(f"Stock: {final_doc['stock']}")
    print(f"Costo: {final_doc['costo']}")


if __name__ == "__main__":
    asyncio.run(main())
