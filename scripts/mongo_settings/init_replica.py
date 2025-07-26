# init_replica_manual.py
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Importamos el error específico de Timeout
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)

# --- CONFIGURACIÓN PARA EJECUCIÓN MANUAL ---
MONGO_HOST = "localhost"
MONGO_PORT = 27017
REPLICA_SET_NAME = "rs0"
MAX_RETRIES = 10
RETRY_DELAY = 5  # segundos
CONNECTION_TIMEOUT = 30000  # 30 segundos en milisegundos


async def initiate_replica_set():
    """
    Se conecta a MongoDB y intenta iniciar el replica set.
    Usa una conexión directa para evitar el error de "No Primary Found".
    """
    # --- CAMBIO CLAVE ---
    # Para la inicialización, nos conectamos directamente al nodo sin
    # intentar descubrir un replica set. El parámetro `directConnection=true`
    # es la clave para que esto funcione.
    connection_string = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/?directConnection=true"
    client = AsyncIOMotorClient(
        connection_string, serverSelectionTimeoutMS=CONNECTION_TIMEOUT
    )

    # Reintentar la conexión
    for attempt in range(MAX_RETRIES):
        try:
            # Comprueba si el servidor está listo
            await client.admin.command("ping")
            print("✅ Conexión con MongoDB exitosa.")
            break
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(
                f"⏳ No se pudo conectar a MongoDB. Reintentando... (Intento {attempt + 1}/{MAX_RETRIES})"
            )
            print(f"   Error Detallado: {e}\n")
            await asyncio.sleep(RETRY_DELAY)
    else:
        print(
            "❌ No se pudo establecer conexión con MongoDB después de varios intentos."
        )
        client.close()
        return

    # La configuración del host del miembro del replica set.
    config = {
        "_id": REPLICA_SET_NAME,
        "members": [{"_id": 0, "host": f"{MONGO_HOST}:{MONGO_PORT}"}],
    }

    try:
        print("🚀 Intentando iniciar el replica set...")
        await client.admin.command("replSetInitiate", config)
        print("✅ Replica set iniciado correctamente.")
    except OperationFailure as e:
        if "already initialized" in str(e).lower():
            print("ℹ️ El replica set ya estaba inicializado.")
        else:
            print(f"❌ Error al iniciar el replica set: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(initiate_replica_set())
