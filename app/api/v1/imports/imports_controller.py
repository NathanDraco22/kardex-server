from typing import Any
import csv
import codecs

from fastapi import UploadFile, HTTPException

from core.imports.init_inventory.model.product_import import ProductImport
from core.imports.init_inventory.process_init_import import process_init_import


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

        parsed_data = []
        for row in csv_reader:
            current_price: str = str(row["price"])
            current_cost: str = str(row["cost"])

            current_price = current_price.replace(",", "")
            current_price = current_price.replace(".", "")
            current_cost = current_cost.replace(",", "")
            current_cost = current_cost.replace(".", "")

            row["price"] = int(current_price) * 100
            row["cost"] = int(current_cost) * 100

            parsed_data.append(row)

        product_imports = [
            ProductImport.model_validate(product) for product in parsed_data
        ]

        await process_init_import(branch_id, product_imports)

        return {
            "status": "success",
            "message": "Importación exitosa",
        }


imports_controller = ImportsController()
