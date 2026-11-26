import csv
import io
import json
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from fastapi import HTTPException, UploadFile

from kardex.core.imports.accounts_payable.model.account_payable_import import (
    AccountPayableImport,
)
from kardex.core.imports.accounts_payable.process_accounts_payable_import import (
    process_accounts_payable_import,
)
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
from kardex.core.inventory import calculate_line_amount
from kardex.repos.v1.unit_scales import UnitScaleInDb
from kardex.services.mongo_collections.v1 import (
    AdjustEntriesCollection,
    ExpensesCollection,
    SuppliersCollection,
    UnitScalesCollection,
)
from kardex.tools import BranchesTool, TimeTools

from .responses import ImportPreviewError, ImportPreviewResponse, ImportResponse

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_ROWS = 10_000

PRODUCT_REQUIRED_COLUMNS = {
    "name",
    "brandName",
    "quantity",
    "cost",
    "price",
}
CLIENT_REQUIRED_COLUMNS = {"name"}
SUPPLIER_REQUIRED_COLUMNS = {"name"}
ACCOUNTS_PAYABLE_REQUIRED_COLUMNS = {"supplierName", "amount"}

TRUE_VALUES = {"1", "true", "yes", "y", "si", "sí", "on"}
FALSE_VALUES = {"0", "false", "no", "n", "off"}


class ImportsController:
    async def create_import(self, branch_id: str, file: UploadFile) -> ImportResponse:
        self._validate_branch(branch_id)
        await self._ensure_initial_inventory_is_new(branch_id)

        rows, headers = await self._read_csv(file)
        self._ensure_product_columns(headers)
        scales_lookup = await self._load_unit_scales_lookup(headers)

        product_imports = self._build_product_imports(rows, scales_lookup)
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
        self._ensure_product_columns(headers)
        scales_lookup = await self._load_unit_scales_lookup(headers)

        product_imports = self._build_product_imports(rows, scales_lookup)
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

    async def create_accounts_payable_import(
        self, branch_id: str, file: UploadFile
    ) -> ImportResponse:
        self._validate_branch(branch_id)

        rows, headers = await self._read_csv(file)
        self._ensure_columns(headers, ACCOUNTS_PAYABLE_REQUIRED_COLUMNS)

        payable_imports = self._build_accounts_payable_imports(rows)
        seen_docs: dict[str, int] = {}
        for row, item in zip(rows, payable_imports, strict=True):
            doc_num = (item.docNumber or "").strip()
            if not doc_num:
                continue
            row_num = row.get("__row_number__", "?")
            if doc_num in seen_docs:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Fila {row_num}: 'docNumber' duplicado en el archivo ('{doc_num}')"
                    ),
                )
            seen_docs[doc_num] = int(row_num) if row_num.isdigit() else 0

        if seen_docs:
            existing_docs = await ExpensesCollection.get_instance().fetch_existing_doc_numbers(
                list(seen_docs.keys())
            )
            if existing_docs:
                first_dup = sorted(existing_docs)[0]
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"El número de documento '{first_dup}' ya existe registrado en el sistema"
                    ),
                )

        try:
            imported_count = await process_accounts_payable_import(
                branch_id, payable_imports
            )
        except Exception as ex:
            err_msg = str(ex)
            if "E11000" in err_msg or "duplicate key" in err_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail="Uno o más números de documento ya existen registrados en el sistema",
                ) from ex
            raise

        return ImportResponse(
            status="success",
            message="Importación de cuentas por pagar exitosa",
            importedCount=imported_count,
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
            "accountspayable": "accountsPayable",
            "accounts-payable": "accountsPayable",
            "accounts_payable": "accountsPayable",
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
                            "Opciones: initialInventory, inventory, clients, suppliers, accountsPayable."
                        ),
                    )
                ],
            )

        errors: list[ImportPreviewError] = []

        if canonical_type in {"initialInventory", "inventory", "clients", "accountsPayable"}:
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
        elif canonical_type == "accountsPayable":
            required_cols = ACCOUNTS_PAYABLE_REQUIRED_COLUMNS
        else:
            required_cols = SUPPLIER_REQUIRED_COLUMNS

        missing_cols = sorted(required_cols.difference(headers))
        if (
            canonical_type in {"initialInventory", "inventory"}
            and "unitName" not in headers
            and "unitScale" not in headers
        ):
            missing_cols = sorted([*missing_cols, "unitName (o unitScale)"])

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

        scales_lookup = (
            await self._load_unit_scales_lookup(headers)
            if canonical_type in {"initialInventory", "inventory"}
            else {}
        )

        total_quantity = 0
        total_cost = 0
        total_price = 0
        total_credit_limit = 0
        total_initial_balance = 0
        total_payable_amount = 0
        total_payable_paid = 0
        total_payable_pending = 0
        new_suppliers_count = 0
        seen_payable_docs: dict[str, int] = {}
        payable_supplier_refs: list[tuple[str | None, str]] = []
        max_errors_to_collect = 50

        for row in rows:
            row_num_str = row.get("__row_number__", "0")
            row_num = int(row_num_str) if row_num_str.isdigit() else 0

            try:
                if canonical_type in {"initialInventory", "inventory"}:
                    product = self._build_single_product_import(row, scales_lookup)
                    total_quantity += product.quantity
                    total_cost += calculate_line_amount(
                        product.cost, product.quantity, product.priceUnitFactor
                    )
                    total_price += calculate_line_amount(
                        product.price, product.quantity, product.priceUnitFactor
                    )
                elif canonical_type == "clients":
                    client = self._build_single_client_import(row)
                    total_credit_limit += client.creditLimit
                    total_initial_balance += client.initialBalance
                elif canonical_type == "suppliers":
                    self._build_single_supplier_import(row)
                elif canonical_type == "accountsPayable":
                    payable = self._build_single_account_payable_import(row)
                    total_payable_amount += payable.amount
                    total_payable_paid += payable.amountPaid
                    total_payable_pending += payable.amount - payable.amountPaid
                    payable_supplier_refs.append(
                        (payable.supplierId, payable.supplierName)
                    )
                    doc_num = (payable.docNumber or "").strip()
                    if doc_num:
                        if doc_num in seen_payable_docs:
                            if len(errors) < max_errors_to_collect:
                                errors.append(
                                    ImportPreviewError(
                                        row=row_num,
                                        field="docNumber",
                                        message=(
                                            f"Número de documento duplicado en el CSV ('{doc_num}')"
                                        ),
                                    )
                                )
                        else:
                            seen_payable_docs[doc_num] = row_num
            except HTTPException as ex:
                if len(errors) < max_errors_to_collect:
                    errors.append(
                        ImportPreviewError(
                            row=row_num,
                            message=str(ex.detail),
                        )
                    )

        if canonical_type == "accountsPayable":
            if seen_payable_docs:
                existing_docs = (
                    await ExpensesCollection.get_instance().fetch_existing_doc_numbers(
                        list(seen_payable_docs.keys())
                    )
                )
                for dup_doc in sorted(existing_docs):
                    if len(errors) >= max_errors_to_collect:
                        break
                    errors.append(
                        ImportPreviewError(
                            row=seen_payable_docs[dup_doc],
                            field="docNumber",
                            message=(
                                f"El número de documento '{dup_doc}' ya existe en el sistema"
                            ),
                        )
                    )

            if payable_supplier_refs:
                raw_suppliers = (
                    await SuppliersCollection.get_instance().fetch_all_suppliers()
                )
                existing_ids = {
                    s.get("id", "") for s in raw_suppliers if s.get("id")
                }
                existing_names = {
                    str(s.get("name", "")).strip().lower()
                    for s in raw_suppliers
                    if s.get("name")
                }
                missing_names: set[str] = set()
                for sup_id, sup_name in payable_supplier_refs:
                    if sup_id and sup_id in existing_ids:
                        continue
                    norm_name = sup_name.strip().lower()
                    if norm_name and norm_name not in existing_names:
                        missing_names.add(norm_name)
                new_suppliers_count = len(missing_names)

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
            totalPayableAmount=total_payable_amount,
            totalPayablePaid=total_payable_paid,
            totalPayablePending=total_payable_pending,
            newSuppliersCount=new_suppliers_count,
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

    def _ensure_product_columns(self, headers: list[str]) -> None:
        missing = sorted(PRODUCT_REQUIRED_COLUMNS.difference(headers))
        if "unitName" not in headers and "unitScale" not in headers:
            missing = sorted([*missing, "unitName (o unitScale)"])
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan columnas obligatorias: {', '.join(missing)}",
            )

    async def _load_unit_scales_lookup(
        self, headers: list[str]
    ) -> dict[str, UnitScaleInDb]:
        if "unitScale" not in headers:
            return {}
        raw_scales = await UnitScalesCollection.get_instance().fetch_all_unit_scales()
        lookup: dict[str, UnitScaleInDb] = {}
        for doc in raw_scales:
            scale = UnitScaleInDb.model_validate(doc)
            lookup[scale.id] = scale
            normalized_name = scale.name.strip().lower()
            if normalized_name:
                lookup[normalized_name] = scale
        return lookup

    def _resolve_scale_default_factor(self, scale: UnitScaleInDb) -> int:
        if scale.defaultUnitIndex == 0 or not scale.units:
            return 1
        idx = scale.defaultUnitIndex - 1
        if 0 <= idx < len(scale.units):
            return max(scale.units[idx].conversionFactor, 1)
        return 1

    def _convert_commercial_cents_to_stored(
        self,
        commercial_cents: int,
        commercial_factor: int,
        price_unit_factor: int,
    ) -> int:
        safe_comm = max(commercial_factor, 1)
        safe_price = max(price_unit_factor, 1)
        if safe_comm == safe_price:
            return commercial_cents
        numerator = commercial_cents * safe_price
        if numerator >= 0:
            return (numerator + safe_comm // 2) // safe_comm
        return -((abs(numerator) + safe_comm // 2) // safe_comm)

    def _parse_scaled_quantity(
        self,
        value: str | None,
        field: str,
        row_number: str,
        scale: UnitScaleInDb | None,
    ) -> int:
        if scale is None:
            return self._parse_int(value, field, row_number)

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

        if number < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: '{field}' no puede ser negativo",
            )

        factor = self._resolve_scale_default_factor(scale)
        base_qty = number * Decimal(factor)
        if base_qty != base_qty.to_integral_value():
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Fila {row_number}: '{field}' ('{value}') no es un múltiplo "
                    f"válido para la escala '{scale.name}'"
                ),
            )

        return int(base_qty)

    def _build_single_product_import(
        self,
        row: dict[str, str],
        scales_lookup: dict[str, UnitScaleInDb] | None = None,
    ) -> ProductImport:
        row_number = row.get("__row_number__", "?")
        scale_ref = self._optional_text(row, "unitScale")
        resolved_scale: UnitScaleInDb | None = None
        if scale_ref is not None:
            lookup = scales_lookup or {}
            resolved_scale = lookup.get(scale_ref) or lookup.get(scale_ref.lower())
            if resolved_scale is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Fila {row_number}: 'unitScale' no corresponde a ninguna "
                        f"escala registrada ('{scale_ref}')"
                    ),
                )

        if resolved_scale is not None:
            unit_name = resolved_scale.baseUnit
            extra_units = list(resolved_scale.units)
            default_unit_index = resolved_scale.defaultUnitIndex
            wholesale_unit_index = resolved_scale.wholesaleUnitIndex
            price_unit_factor = max(resolved_scale.priceUnitFactor, 1)
            commercial_factor = self._resolve_scale_default_factor(resolved_scale)
        else:
            unit_name = self._required_text(row, "unitName", row_number)
            extra_units = []
            default_unit_index = 0
            wholesale_unit_index = 0
            price_unit_factor = 1
            commercial_factor = 1

        raw_cost = self._parse_money(row.get("cost"), "cost", row_number)
        raw_price = self._parse_money(row.get("price"), "price", row_number)
        raw_price2 = self._parse_money(row.get("price2"), "price2", row_number)
        raw_price3 = self._parse_money(row.get("price3"), "price3", row_number)
        raw_price4 = self._parse_money(row.get("price4"), "price4", row_number)

        return ProductImport(
            name=self._required_text(row, "name", row_number),
            description=self._optional_text(row, "description"),
            code=self._optional_text(row, "code") or "",
            brandName=self._required_text(row, "brandName", row_number),
            unitName=unit_name,
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
            extraUnits=extra_units,
            defaultUnitIndex=default_unit_index,
            wholesaleUnitIndex=wholesale_unit_index,
            priceUnitFactor=price_unit_factor,
            quantity=self._parse_scaled_quantity(
                row.get("quantity"), "quantity", row_number, resolved_scale
            ),
            cost=self._convert_commercial_cents_to_stored(
                raw_cost, commercial_factor, price_unit_factor
            ),
            price=self._convert_commercial_cents_to_stored(
                raw_price, commercial_factor, price_unit_factor
            ),
            price2=self._convert_commercial_cents_to_stored(
                raw_price2, commercial_factor, price_unit_factor
            ),
            price3=self._convert_commercial_cents_to_stored(
                raw_price3, commercial_factor, price_unit_factor
            ),
            price4=self._convert_commercial_cents_to_stored(
                raw_price4, commercial_factor, price_unit_factor
            ),
        )

    def _build_product_imports(
        self,
        rows: list[dict[str, str]],
        scales_lookup: dict[str, UnitScaleInDb] | None = None,
    ) -> list[ProductImport]:
        return [
            self._build_single_product_import(row, scales_lookup) for row in rows
        ]

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

    def _build_single_account_payable_import(
        self, row: dict[str, str]
    ) -> AccountPayableImport:
        row_number = row.get("__row_number__", "?")
        supplier_name = self._required_text(row, "supplierName", row_number)
        amount = self._parse_money(row.get("amount"), "amount", row_number)
        if amount <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: 'amount' debe ser mayor a cero",
            )

        amount_paid = self._parse_money(
            row.get("amountPaid"), "amountPaid", row_number, default=0
        )
        if amount_paid < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Fila {row_number}: 'amountPaid' no puede ser negativo",
            )
        if amount_paid > amount:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Fila {row_number}: 'amountPaid' no puede ser mayor que 'amount'"
                ),
            )

        return AccountPayableImport(
            supplierId=self._optional_text(row, "supplierId"),
            supplierName=supplier_name,
            docNumber=self._optional_text(row, "docNumber"),
            date=self._parse_optional_date(row.get("date"), "date", row_number),
            expirationDate=self._parse_optional_date(
                row.get("expirationDate"), "expirationDate", row_number
            ),
            amount=amount,
            amountPaid=amount_paid,
            description=self._optional_text(row, "description"),
        )

    def _build_accounts_payable_imports(
        self, rows: list[dict[str, str]]
    ) -> list[AccountPayableImport]:
        return [self._build_single_account_payable_import(row) for row in rows]

    def _parse_optional_date(
        self, value: str | None, field: str, row_number: str
    ) -> int | None:
        text = (value or "").strip()
        if not text:
            return None

        if text.lstrip("-").isdigit() and text != "-":
            ts = int(text)
            if abs(ts) < 10_000_000_000:
                ts *= 1000
            return ts

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(text, fmt)
                localized = TimeTools.default_timezone.localize(parsed)
                return int(localized.timestamp() * 1000)
            except ValueError:
                continue

        raise HTTPException(
            status_code=400,
            detail=(
                f"Fila {row_number}: '{field}' no es una fecha válida ('{value}'). "
                "Usa Unix timestamp, YYYY-MM-DD o DD/MM/YYYY"
            ),
        )

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
