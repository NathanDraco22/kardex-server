from typing import Any
import csv
import codecs

from fastapi import UploadFile, HTTPException

from core.imports.init_inventory.model.product_import import ProductImport
from core.imports.init_inventory.process_init_import import (
    process_init_import,
    process_inventory_import,
)
from core.imports.clients.model.client_import import ClientImport
from core.imports.clients.process_clients_import import process_clients_import
from core.imports.suppliers.model.supplier_import import SupplierImport
from core.imports.suppliers.process_suppliers_import import process_suppliers_import

class ImportsController:
    async def create_import(self, branch_id: str, file: UploadFile) -> Any:
        filename = file.filename
        if not filename:
            raise HTTPException(
                status_code=400, detail="No se ha proporcionado un archivo"
            )
        if not filename.endswith(".csv"):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser de formato .csv"
            )
        csv_reader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))

        parsed_data = self.parse_dict(csv_reader)

        product_imports = [
            ProductImport.model_validate(product) for product in parsed_data
        ]

        await process_init_import(branch_id, product_imports)

        return {
            "status": "success",
            "message": "Importación exitosa",
        }

    async def create_inventory_import(self, branch_id: str, file: UploadFile) -> Any:
        filename = file.filename
        if not filename:
            raise HTTPException(
                status_code=400, detail="No se ha proporcionado un archivo"
            )
        if not filename.endswith(".csv"):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser de formato .csv"
            )
        csv_reader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))

        parsed_data = self.parse_dict(csv_reader)

        product_imports = [
            ProductImport.model_validate(product) for product in parsed_data
        ]

        await process_inventory_import(branch_id, product_imports)

        return {
            "status": "success",
            "message": "Importación exitosa",
        }

    def parse_dict(self, csv_reader: csv.DictReader) -> list:
        parsed_data = []
        for row in csv_reader:
            current_price: str = str(row["price"])
            current_price2: str = str(row.get("price2", "0"))
            current_price3: str = str(row.get("price3", "0"))
            current_cost: str = str(row["cost"])

            current_price = current_price.replace(",", ".")
            current_price2 = current_price2.replace(",", ".")
            current_price3 = current_price3.replace(",", ".")
            current_cost = current_cost.replace(",", ".")

            float_price = float(current_price)
            float_price2 = float(current_price2)
            float_price3 = float(current_price3)
            float_cost = float(current_cost)

            row["price"] = int(float_price * 100)
            row["price2"] = int(float_price2 * 100)
            row["price3"] = int(float_price3 * 100)
            row["cost"] = int(float_cost * 100)

            raw_code = row.get("code") or ""

            clean_code = str(raw_code).strip()

            if clean_code:
                row["code"] = clean_code

            parsed_data.append(row)

        return parsed_data

    async def create_clients_import(self, branch_id: str, file: UploadFile) -> Any:
        filename = file.filename
        if not filename:
            raise HTTPException(
                status_code=400, detail="No se ha proporcionado un archivo"
            )
        if not filename.endswith(".csv"):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser de formato .csv"
            )
        csv_reader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))

        parsed_data = self.parse_clients_dict(csv_reader)

        client_imports = [
            ClientImport.model_validate(client) for client in parsed_data
        ]

        await process_clients_import(branch_id, client_imports)

        return {
            "status": "success",
            "message": "Importación de clientes exitosa",
        }

    def parse_clients_dict(self, csv_reader: csv.DictReader) -> list:
        parsed_data = []
        for row in csv_reader:
            current_credit_limit: str = str(row.get("creditLimit", "0"))
            current_initial_balance: str = str(row.get("initialBalance", "0"))

            current_credit_limit = current_credit_limit.replace(",", ".")
            current_initial_balance = current_initial_balance.replace(",", ".")

            float_credit_limit = float(current_credit_limit) if current_credit_limit else 0.0
            float_initial_balance = float(current_initial_balance) if current_initial_balance else 0.0

            row["creditLimit"] = int(float_credit_limit * 100)
            row["initialBalance"] = int(float_initial_balance * 100)

            parsed_data.append(row)

        return parsed_data

    async def create_suppliers_import(self, file: UploadFile) -> Any:
        filename = file.filename
        if not filename:
            raise HTTPException(
                status_code=400, detail="No se ha proporcionado un archivo"
            )
        if not filename.endswith(".csv"):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser de formato .csv"
            )
        csv_reader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))

        parsed_data = self.parse_suppliers_dict(csv_reader)

        supplier_imports = [
            SupplierImport.model_validate(supplier) for supplier in parsed_data
        ]

        await process_suppliers_import(supplier_imports)

        return {
            "status": "success",
            "message": "Importación de proveedores exitosa",
        }

    def parse_suppliers_dict(self, csv_reader: csv.DictReader) -> list:
        parsed_data = []
        for row in csv_reader:
            # Proveedores solo manejan strings para name, cardId, email, phone.
            # No hay necesidad de limpieza matemática, solo trim de espacios si es necesario.
            parsed_data.append(row)

        return parsed_data

imports_controller = ImportsController()
