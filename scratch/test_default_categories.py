import asyncio
import os
import sys

# Asegurar que el path incluya app y kardex-business
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "kardex-business", "src")))

def load_env():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", ".env"))
    if os.path.exists(env_path):
        print("[INFO] Cargando variables desde app/.env...")
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().strip('"').strip("'")
                    os.environ[key] = val

load_env()

from kardex.services.mongo_service import MongoService
from kardex.services.mongo_collections.v1.expense_categories_collection import ExpenseCategoriesCollection
from kardex.core.default_values.create_default_expense_categories import create_default_expense_categories

async def test_categories():
    print("[INFO] Inicializando conexion a MongoDB...")
    mongo = MongoService()
    await mongo.init_service()
    
    col = ExpenseCategoriesCollection.get_instance()
    
    # 1. Obtener categorias actuales
    initial_categories = await col.fetch_all_expense_categories()
    initial_count = len(initial_categories)
    print(f"[INFO] Categorias iniciales en base de datos: {initial_count}")
    
    # 2. Ejecutar creacion de por defecto
    print("[INFO] Ejecutando create_default_expense_categories()...")
    await create_default_expense_categories()
    
    # 3. Obtener categorias después de ejecutar
    final_categories = await col.fetch_all_expense_categories()
    final_count = len(final_categories)
    print(f"[INFO] Categorias finales en base de datos: {final_count}")
    
    # 4. Volver a ejecutar para validar idempotencia (no deben duplicarse)
    print("[INFO] Volviendo a ejecutar para validar idempotencia...")
    await create_default_expense_categories()
    
    idempotent_categories = await col.fetch_all_expense_categories()
    idempotent_count = len(idempotent_categories)
    print(f"[INFO] Categorias despues de segunda ejecucion: {idempotent_count}")
    
    assert final_count == idempotent_count, f"Error: No es idempotente. Cuentas difieren: {final_count} vs {idempotent_count}"
    assert final_count >= 17, f"Error: Deberia haber al menos 17 categorias cargadas, obtenido {final_count}"
    
    print("[OK] Prueba de categorias finalizada con exito!")

if __name__ == "__main__":
    asyncio.run(test_categories())
