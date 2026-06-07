import asyncio
import os
import sys
from datetime import datetime

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
from kardex.services.mongo_collections.v1.expenses_collection import ExpensesCollection
from kardex.core.report_manager.report_manager import ReportManager
from kardex.tools import TimeTools, UuidTool

async def test_flow():
    print("[INFO] Iniciando prueba de integracion de gastos en resumen ejecutivo (por sucursal)...")
    
    # 1. Inicializar servicio de MongoDB
    mongo = MongoService()
    await mongo.init_service()
    
    expenses_col = ExpensesCollection.get_instance()
    
    # Rango de tiempo para la prueba (última hora)
    now_ms = TimeTools.get_now_in_milliseconds()
    start_date = now_ms - (1000 * 60 * 60) # Hace 1 hora
    end_date = now_ms + (1000 * 60 * 60)   # Dentro de 1 hora
    
    # 2. Crear gastos de prueba en la sucursal test_branch_1
    gasto_paid_id = UuidTool.generate_uuid()
    gasto_open_id = UuidTool.generate_uuid()
    
    gasto_paid = {
        "id": gasto_paid_id,
        "type": "operative",
        "branchId": "test_branch_1",
        "docNumber": "GP-TEST-001",
        "amount": 50000, # 500.00
        "category": "services",
        "description": "Test Paid Expense",
        "date": start_date,
        "dateId": datetime.fromtimestamp(start_date/1000).strftime("%Y-%m-%d"),
        "amountPaid": 50000,
        "status": "paid",
        "isActive": True,
        "isDeleted": False,
        "createdBy": {"id": "test_user_1", "username": "tester", "displayName": "Tester"},
        "createdAt": now_ms,
        "updatedAt": None
    }
    
    gasto_open = {
        "id": gasto_open_id,
        "type": "tax",
        "branchId": "test_branch_1",
        "docNumber": "GO-TEST-002",
        "amount": 30000, # 300.00
        "category": "taxes",
        "description": "Test Open Expense",
        "date": start_date,
        "dateId": datetime.fromtimestamp(start_date/1000).strftime("%Y-%m-%d"),
        "amountPaid": 0,
        "status": "open",
        "isActive": True,
        "isDeleted": False,
        "createdBy": {"id": "test_user_1", "username": "tester", "displayName": "Tester"},
        "createdAt": now_ms,
        "updatedAt": None
    }
    
    print("[INFO] Insertando gastos de prueba...")
    await expenses_col._collection.insert_many([gasto_paid, gasto_open])
    
    try:
        # 3. Invocar al ReportManager para calcular el resumen de gastos
        print("[INFO] Consultando resumen de gastos en el periodo...")
        report_mgr = ReportManager()
        summary = await report_mgr.get_expenses_summary_in_range(start_date, end_date)
        
        print(f"Resultado Obtenido: {summary}")
        
        # 4. Validar resultados globales esperados
        # Total debe ser: 50000 + 30000 = 80000
        # Pagado debe ser: 50000 (sólo el de estado paid)
        expected_total = 80000
        expected_paid = 50000
        
        assert summary["expensesTotal"] >= expected_total, f"Total esperado al menos {expected_total}, obtenido: {summary['expensesTotal']}"
        assert summary["expensesPaid"] >= expected_paid, f"Paid esperado al menos {expected_paid}, obtenido: {summary['expensesPaid']}"
        
        # Validar resultados por sucursal
        assert "test_branch_1" in summary["branches"], "La sucursal test_branch_1 deberia estar en el desglose de sucursales"
        branch_summary = summary["branches"]["test_branch_1"]
        
        assert branch_summary["expensesTotal"] == expected_total, f"Total de sucursal esperado {expected_total}, obtenido: {branch_summary['expensesTotal']}"
        assert branch_summary["expensesPaid"] == expected_paid, f"Paid de sucursal esperado {expected_paid}, obtenido: {branch_summary['expensesPaid']}"
        
        # Imprimimos de manera limpia:
        total_decimal = summary["expensesTotal"] / 100
        paid_decimal = summary["expensesPaid"] / 100
        owed_decimal = (summary["expensesTotal"] - summary["expensesPaid"]) / 100
        
        print(f"[OK] Exito! Totales validados globalmente:")
        print(f"   - Gastos Totales: ${total_decimal:,.2f}")
        print(f"   - Pagado: ${paid_decimal:,.2f}")
        print(f"   - Pendiente (Por Pagar): ${owed_decimal:,.2f}")
        print(f"[OK] Exito! Desglose de sucursal validado:")
        print(f"   - Sucursal 'test_branch_1' - Total: ${branch_summary['expensesTotal']/100:,.2f}, Pagado: ${branch_summary['expensesPaid']/100:,.2f}")
        
    finally:
        # 5. Limpieza de base de datos
        print("[INFO] Limpiando gastos de prueba...")
        await expenses_col._collection.delete_many({"id": {"$in": [gasto_paid_id, gasto_open_id]}})
        print("[INFO] Limpieza completada.")

if __name__ == "__main__":
    asyncio.run(test_flow())
