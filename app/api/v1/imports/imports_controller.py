from typing import Any
import csv
import codecs

from fastapi import UploadFile, HTTPException

from core.imports.init_inventory.model.product_import import ProductImport
from core.imports.init_inventory.process_init_import import (
    process_init_import,
    process_inventory_import,
)


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


imports_controller = ImportsController()
