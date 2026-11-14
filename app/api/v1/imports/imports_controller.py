import csv
import io
import json
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from fastapi import HTTPException, UploadFile

from kardex.core.imports.clients.model.client_import import ClientImport
from kardex.core.imports.clients.process_clients_import import process_clients_import
from kardex.core.imports.init_inventory.model.product_import import ProductImport
from kardex.core.imports.init_inventory.process_init_import import (
    process_init_import,
    process_inventory_import,
)
from kardex.core.imports.suppliers.model.supplier_import import SupplierImport
from kardex.core.imports.suppliers.process_suppliers_import import (
    process_suppliers_import,
)
from kardex.services.mongo_collections.v1 import AdjustEntriesCollection
from kardex.tools import BranchesTool

from .responses import ImportPreviewError, ImportPreviewResponse, ImportResponse

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 10_000

PRODUCT_REQUIRED_COLUMNS = {
    "name",
    "brandName",
    "unitName",
    "quantity",
    "cost",
    "price",
}
CLIENT_REQUIRED_COLUMNS = {"name"}
SUPPLIER_REQUIRED_COLUMNS = {"name"}

TRUE_VALUES = {"1", "true", "yes", "y", "si", "sí", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off"}


class ImportsController:
    async def create_import(self, branch_id: str, file: UploadFile) -> ImportResponse:
        self._validate_branch(branch_id)
        await self._ensure_initial_inventory_is_new(branch_id)

        rows, headers = await self._read_csv(file)
        self._ensure_columns(headers, PRODUCT_REQUIRED_COLUMNS)

        product_imports = self._build_product_imports(rows)
        await process_init_import(branch_id, product_imports)

        return ImportResponse(
            status="success",
            message="Importación de inventario inicial exitosa",
            importedCount=len(product_imports),
        )

    async def create_inventory_import(
        self, branch_id: str, file: UploadFile
    ) -> ImportResponse:
        self._validate_branch(branch_id)

        rows, headers = await self._read_csv(file)
        self._ensure_columns(headers, PRODUCT_REQUIRED_COLUMNS)

        product_imports = self._build_product_imports(rows)
        await process_inventory_import(branch_id, product_imports)

        return ImportResponse(
            status="success",
            message="Importación de inventario exitosa",
            importedCount=len(product_imports),
        )

    async def create_clients_import(
        self, branch_id: str, file: UploadFile
    ) -> ImportResponse:
        self._validate_branch(branch_id)

        rows, headers = await self._read_csv(file)
        self._ensure_columns(headers, CLIENT_REQUIRED_COLUMNS)

        client_imports = self._build_client_imports(rows)
        await process_clients_import(branch_id, client_imports)

        return ImportResponse(
            status="success",
            message="Importación de clientes exitosa",
            importedCount=len(client_imports),
        )

    async def create_suppliers_import(self, file: UploadFile) -> ImportResponse:
        rows, headers = await self._read_csv(file)
        self._ensure_columns(headers, SUPPLIER_REQUIRED_COLUMNS)

        supplier_imports = self._build_supplier_imports(rows)
        await process_suppliers_import(supplier_imports)

        return ImportResponse(
            status="success",
            message="Importación de proveedores exitosa",
            importedCount=len(supplier_imports),
        )

    async def preview_import(
        self, import_type: str, branch_id: str | None, file: UploadFile
    ) -> ImportPreviewResponse:
        normalized_type = import_type.strip()
        type_mapping = {
            "initialinventory": "initialInventory",
            "init-inventory": "initialInventory",
            "init_inventory": "initialInventory",
            "inventory": "inventory",
            "clients": "clients",
            "client": "clients",
            "suppliers": "suppliers",
            "supplier": "suppliers",
        }
        canonical_type = type_mapping.get(normalized_type.lower())
        if not canonical_type:
            return ImportPreviewResponse(
                status="error",
                isValid=False,
                importType=import_type,
                totalRows=0,
                errors=[
                    ImportPreviewError(
                        row=0,
                        message=(
                            f"Tipo de importación no válido: '{import_type}'. "
                            "Opciones: initialInventory, inventory, clients, suppliers."
                        ),
                    )
                ],
            )

        errors: list[ImportPreviewError] = []

        if canonical_type in {"initialInventory", "inventory", "clients"}:
            if not branch_id:
                errors.append(
                    ImportPreviewError(
                        row=0,
                        message="La sucursal es obligatoria para este tipo de importación",
                    )
                )
            else:
                try:
                    self._validate_branch(branch_id)
                except HTTPException as ex:
                    errors.append(ImportPreviewError(row=0, message=str(ex.detail)))

        if canonical_type == "initialInventory" and branch_id and not errors:
            try:
                await self._ensure_initial_inventory_is_new(branch_id)
            except HTTPException as ex:
                errors.append(ImportPreviewError(row=0, message=str(ex.detail)))

        try:
            rows, headers = await self._read_csv(file)
        except HTTPException as ex:
            errors.append(ImportPreviewError(row=0, message=str(ex.detail)))
            return ImportPreviewResponse(
                status="error",
                isValid=False,
                importType=canonical_type,
                totalRows=0,
                errors=errors,
            )

        if canonical_type in {"initialInventory", "inventory"}:
            required_cols = PRODUCT_REQUIRED_COLUMNS
        elif canonical_type == "clients":
            required_cols = CLIENT_REQUIRED_COLUMNS
        else:
            required_cols = SUPPLIER_REQUIRED_COLUMNS

        missing_cols = sorted(required_cols.difference(headers))
        if missing_cols:
            errors.append(
                ImportPreviewError(
                    row=0,
                    message=f"Faltan columnas obligatorias: {', '.join(missing_cols)}",
                )
            )
            return ImportPreviewResponse(
                status="error",
                isValid=False,
                importType=canonical_type,
                totalRows=len(rows),
                errors=errors,
            )

        total_quantity = 0
        total_cost = 0
        total_price = 0
        total_credit_limit = 0
        total_initial_balance = 0
        max_errors_to_collect = 50

        for row in rows:
            row_num_str = row.get("__row_number__", "0")
            row_num = int(row_num_str) if row_num_str.isdigit() else 0

            try:
                if canonical_type in {"initialInventory", "inventory"}:
                    product = self._build_single_product_import(row)
                    total_quantity += product.quantity
                    total_cost += product.quantity * product.cost
                    total_price += product.quantity * product.price
                elif canonical_type == "clients":
                    client = self._build_single_client_import(row)
                    total_credit_limit += client.creditLimit
                    total_initial_balance += client.initialBalance
                elif canonical_type == "suppliers":
                    self._build_single_supplier_import(row)
            except HTTPException as ex:
                if len(errors) < max_errors_to_collect:
                    errors.append(
                        ImportPreviewError(
                            row=row_num,
                            message=str(ex.detail),
                        )
                    )

        is_valid = len(errors) == 0

        return ImportPreviewResponse(
            status="success" if is_valid else "error",
            isValid=is_valid,
            importType=canonical_type,
            totalRows=len(rows),
            totalQuantity=total_quantity,
            totalCost=total_cost,
            totalPrice=total_price,
            totalCreditLimit=total_credit_limit,
            totalInitialBalance=total_initial_balance,
            errors=errors,
        )

    def _validate_branch(self, branch_id: str) -> None:
        if BranchesTool().get_branch_by_id(branch_id) is None:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada")

    async def _ensure_initial_inventory_is_new(self, branch_id: str) -> None:
        collection = AdjustEntriesCollection.get_instance()
        existing = await collection.fetch_adjust_entry_by_doc_number(
            doc_number="0000",
            branch_id=branch_id,
        )
        if existing is not None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El inventario inicial ya fue importado para esta sucursal. "
                    "Usa la importación de inventario para agregar nuevas existencias."
                ),
            )

    async def _read_csv(
        self, file: UploadFile
    ) -> tuple[list[dict[str, str]], list[str]]:
        filename = file.filename or ""
        if not filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400, detail="El archivo debe ser de formato .csv"
            )

        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="El archivo CSV está vacío")

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="El archivo supera el tamaño máximo permitido de 10 MB",
            )

        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise HTTPException(
                status_code=400,
                detail="El archivo debe estar codificado en UTF-8",
            ) from error

        lines = text.splitlines()
        while lines and not lines[0].strip():
            lines.pop(0)
        text = "\n".join(lines)

        first_line = next(
            (line for line in lines if line.strip()),
            "",
        )
        delimiter = ";" if first_line.count(";") > first_line.count(",") else ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        headers = [
            header.strip()
            for header in (reader.fieldnames or [])
            if header is not None and header.strip()
        ]

        if not headers:
            raise HTTPException(
                status_code=400,
                detail="El CSV no contiene una fila de encabezados válida",
            )

        rows: list[dict[str, str]] = []
        for index, raw_row in enumerate(reader, start=2):
            normalized_row: dict[str, str] = {}
            for key, value in raw_row.items():
                if key is None:
                    continue
                normalized_row[key.strip()] = (
                    value.strip() if isinstance(value, str) else ""
                )

            if not any(normalized_row.values()):
                continue

            normalized_row["__row_number__"] = str(index)
            rows.append(normalized_row)

        if not rows:
            raise HTTPException(
                status_code=400,
                detail="El archivo CSV no contiene filas para importar",
            )

        if len(rows) > MAX_ROWS:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo contiene más de {MAX_ROWS} filas",
            )

        return rows, headers

    def _ensure_columns(self, headers: list[str], required: set[str]) -> None:
        missing = sorted(required.difference(headers))
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan columnas obligatorias: {', '.join(missing)}",
            )

    def _build_single_product_import(self, row: dict[str, str]) -> ProductImport:
        row_number = row.get("__row_number__", "?")
        return ProductImport(
            name=self._required_text(row, "name", row_number),
            description=self._optional_text(row, "description"),
            code=self._optional_text(row, "code") or "",
            brandName=self._required_text(row, "brandName", row_number),
            unitName=self._required_text(row, "unitName", row_number),
            categoryName=self._optional_text(row, "categoryName"),
            tags=self._parse_tags(row.get("tags"), row_number),
            hasIva=self._parse_bool(
                row.get("hasIva"),
                default=False,
                field="hasIva",
                row_number=row_number,
            ),
            isActive=self._parse_bool(
                row.get("isActive"),
                default=True,
                field="isActive",
                row_number=row_number,
            ),
            quantity=self._parse_int(
                row.get("quantity"), "quantity", row_number
            ),
            cost=self._parse_money(row.get("cost"), "cost", row_number),
            price=self._parse_money(row.get("price"), "price", row_number),
            price2=self._parse_money(row.get("price2"), "price2", row_number),
            price3=self._parse_money(row.get("price3"), "price3", row_number),
            price4=self._parse_money(row.get("price4"), "price4", row_number),
        )

    def _build_product_imports(self, rows: list[dict[str, str]]) -> list[ProductImport]:
        return [self._build_single_product_import(row) for row in rows]

    def _build_single_client_import(self, row: dict[str, str]) -> ClientImport:
        row_number = row.get("__row_number__", "?")
        return ClientImport(
            name=self._required_text(row, "name", row_number),
            cardId=self._optional_text(row, "cardId"),
            phone=self._optional_text(row, "phone"),
            address=self._optional_text(row, "address"),
            location=self._optional_text(row, "location"),
            email=self._optional_text(row, "email"),
            group=self._optional_text(row, "group"),
            creditLimit=self._parse_money(
                row.get("creditLimit"),
                "creditLimit",
                row_number,
            ),
            initialBalance=self._parse_money(
                row.get("initialBalance"),
                "initialBalance",
                row_number,
            ),
        )

    def _build_client_imports(self, rows: list[dict[str, str]]) -> list[ClientImport]:
        return [self._build_single_client_import(row) for row in rows]

    def _build_single_supplier_import(self, row: dict[str, str]) -> SupplierImport:
        row_number = row.get("__row_number__", "?")
        return SupplierImport(
            name=self._required_text(row, "name", row_number),
            cardId=self._optional_text(row, "cardId"),
            email=self._optional_text(row, "email"),
            phone=self._optional_text(row, "phone"),
        )

    def _build_supplier_imports(
        self, rows: list[dict[str, str]]
    ) -> list[SupplierImport]:
        return [self._build_single_supplier_import(row) for row in rows]

    def _required_text(self, row: dict[str, str], field: str, row_number: str) -> str:
        value = (row.get(field) or "").strip()
        if not value:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' es obligatorio",
            )
        return value

    def _optional_text(self, row: dict[str, str], field: str) -> str | None:
        value = (row.get(field) or "").strip()
        return value or None

    def _parse_money(
        self,
        value: str | None,
        field: str,
        row_number: str,
        default: int = 0,
    ) -> int:
        text = (value or "").strip().replace(" ", "")
        if not text:
            return default

        if "," in text and "." in text:
            if text.rfind(",") > text.rfind("."):
                text = text.replace(".", "").replace(",", ".")
            else:
                text = text.replace(",", "")
        else:
            text = text.replace(",", ".")

        try:
            amount = Decimal(text)
        except InvalidOperation as error:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' no es un número válido ('{value}')",
            ) from error

        cents = (amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(cents)

    def _parse_int(self, value: str | None, field: str, row_number: str) -> int:
        text = (value or "").strip()
        if not text:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' es obligatorio",
            )

        try:
            number = Decimal(text.replace(",", "."))
        except InvalidOperation as error:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' no es un número válido ('{value}')",
            ) from error

        if number != number.to_integral_value():
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' debe ser un número entero",
            )

        if number < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' no puede ser negativo",
            )

        return int(number)

    def _parse_bool(
        self,
        value: str | None,
        *,
        default: bool,
        field: str,
        row_number: str,
    ) -> bool:
        text = (value or "").strip().lower()
        if not text:
            return default

        if text in TRUE_VALUES:
            return True

        if text in FALSE_VALUES:
            return False

        raise HTTPException(
            status_code=400,
            detail=(
                f"Fila {row_number}: '{field}' debe ser un valor booleano "
                "(true/false, si/no, 1/0)"
            ),
        )

    def _parse_tags(self, value: str | None, row_number: str) -> list[str]:
        text = (value or "").strip()
        if not text:
            return []

        if text.startswith("["):
            try:
                parsed_tags = json.loads(text)
            except json.JSONDecodeError as error:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Fila {row_number}: 'tags' debe ser una lista JSON "
                        "o valores separados por ';'"
                    ),
                ) from error

            if not isinstance(parsed_tags, list) or any(
                not isinstance(tag, str) for tag in parsed_tags
            ):
                raise HTTPException(
                    status_code=400,
                    detail=f"Fila {row_number}: 'tags' debe ser una lista de textos",
                )

            return [tag.strip() for tag in parsed_tags if tag.strip()]

        return [tag.strip() for tag in text.split(";") if tag.strip()]


imports_controller = ImportsController()
