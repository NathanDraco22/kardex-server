from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.models import UserInfo
from kardex.repos.v1.expenses import (
    ExpenseInDb,
    ExpensePayment,
    ExpensesStatus,
)
from kardex.repos.v1.suppliers import SupplierInDb
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    ExpensesCollection,
    SuppliersCollection,
)
from kardex.tools import TimeTools, UuidTool

from .model.account_payable_import import AccountPayableImport

_MS_PER_DAY = 86_400_000


async def process_accounts_payable_import(
    branch_id: str,
    items: list[AccountPayableImport],
    created_by: UserInfo | None = None,
) -> int:
    if not items:
        return 0

    creator = created_by or UserInfo(id="system", name="Importación CSV")
    now_ms = TimeTools.get_now_in_milliseconds()

    supplier_col = SuppliersCollection.get_instance()
    expenses_col = ExpensesCollection.get_instance()

    mongo_client = MongoService().client
    counter_manager = CounterManager()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            existing_docs = await supplier_col.fetch_all_suppliers()
            by_id: dict[str, SupplierInDb] = {}
            by_name: dict[str, SupplierInDb] = {}
            for doc in existing_docs:
                supplier = SupplierInDb.model_validate(doc)
                by_id[supplier.id] = supplier
                norm_name = supplier.name.strip().lower()
                if norm_name and norm_name not in by_name:
                    by_name[norm_name] = supplier

            missing_names: dict[str, str] = {}
            for item in items:
                if item.supplierId and item.supplierId in by_id:
                    continue
                norm = item.supplierName.strip().lower()
                if norm and norm not in by_name and norm not in missing_names:
                    missing_names[norm] = item.supplierName.strip()

            if missing_names:
                start_sup = await counter_manager.next_supplier_number(session=session)
                raw_sup = int(start_sup)
                new_suppliers: list[SupplierInDb] = []
                for norm, display_name in missing_names.items():
                    sup_id = str(raw_sup).zfill(4)
                    supplier = SupplierInDb(
                        id=sup_id,
                        name=display_name,
                        createdAt=now_ms,
                    )
                    new_suppliers.append(supplier)
                    by_id[sup_id] = supplier
                    by_name[norm] = supplier
                    raw_sup += 1

                await supplier_col.create_many_suppliers_with_session(
                    [s.model_dump() for s in new_suppliers],
                    session=session,
                )
                await counter_manager.set_supplier_number(raw_sup - 1, session=session)

            explicit_docs = {
                item.docNumber.strip()
                for item in items
                if item.docNumber and item.docNumber.strip()
            }
            auto_count = sum(
                1 for item in items if not (item.docNumber and item.docNumber.strip())
            )
            raw_exp = 0
            used_docs = set(explicit_docs)
            if auto_count > 0:
                start_exp = await counter_manager.next_expense_number(session=session)
                raw_exp = int(start_exp)
                candidate_docs = [
                    str(raw_exp + offset).zfill(4)
                    for offset in range(auto_count + len(explicit_docs) + 10)
                ]
                existing_auto = await expenses_col.fetch_existing_doc_numbers(
                    candidate_docs
                )
                used_docs |= existing_auto

            new_expenses: list[ExpenseInDb] = []
            for item in items:
                supplier = (
                    by_id.get(item.supplierId)
                    if item.supplierId
                    else None
                ) or by_name[item.supplierName.strip().lower()]

                if item.docNumber and item.docNumber.strip():
                    doc_number = item.docNumber.strip()
                else:
                    while str(raw_exp).zfill(4) in used_docs:
                        raw_exp += 1
                    doc_number = str(raw_exp).zfill(4)
                    used_docs.add(doc_number)
                    raw_exp += 1

                doc_date_ms = item.date if item.date is not None else now_ms
                created_at_ms = item.date if item.date is not None else now_ms
                date_id = TimeTools.timestamp_to_date_id(doc_date_ms)

                if item.expirationDate is not None:
                    exp_date_ms: int | None = item.expirationDate
                elif supplier.creditDays > 0:
                    exp_date_ms = doc_date_ms + supplier.creditDays * _MS_PER_DAY
                else:
                    exp_date_ms = None

                amount_paid = max(0, min(item.amountPaid, item.amount))
                status: ExpensesStatus
                if amount_paid >= item.amount:
                    status = "paid"
                elif amount_paid > 0:
                    status = "partiallyPaid"
                else:
                    status = "open"

                paid_at = doc_date_ms if status == "paid" else None
                payments = (
                    [
                        ExpensePayment(
                            id=UuidTool.generate_uuid(),
                            amount=amount_paid,
                            paymentMethod="other",
                            note="Saldo abonado en importación",
                            paidAt=doc_date_ms,
                            createdBy=creator,
                            createdAt=now_ms,
                        )
                    ]
                    if amount_paid > 0
                    else []
                )

                expense = ExpenseInDb(
                    id=UuidTool.generate_uuid(),
                    type="supplier",
                    branchId=branch_id,
                    docNumber=doc_number,
                    amount=item.amount,
                    amountPaid=amount_paid,
                    payments=payments,
                    category="",
                    description=item.description or "Cuenta por pagar importada",
                    date=doc_date_ms,
                    dateId=date_id,
                    supplierId=supplier.id,
                    supplierName=supplier.name,
                    status=status,
                    isActive=True,
                    expirationDate=exp_date_ms,
                    createdBy=creator,
                    paidAt=paid_at,
                    shiftId=None,
                    createdAt=created_at_ms,
                    updatedAt=None,
                    isDeleted=False,
                )
                new_expenses.append(expense)

            if new_expenses:
                await expenses_col.create_many_expenses_with_session(
                    [e.model_dump() for e in new_expenses],
                    session=session,
                )

            if auto_count > 0:
                await counter_manager.set_expense_number(raw_exp - 1, session=session)

    return len(new_expenses)
