import asyncio
from typing import Any, Callable, Coroutine, List, Tuple, cast

from pymongo.errors import OperationFailure

from kardex.core.credit_note_register.process_credit_note import (
    sum_previously_returned_from_devolutions,
    sum_previously_returned_quantities,
)
from kardex.core.policies import DevolutionPolicy, PolicyDecision
from kardex.repos.v1.devolutions import (
    CreateDevolution,
    DevolutionInDb,
    DevolutionsRepository,
)
from kardex.repos.v1.clients import ClientsRepository
from kardex.repos.v1.invoices import InvoicesRepository
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.branches import BranchesRepository
from kardex.repos.v1.products import ProductsRepository
from kardex.services.mongo_collections.v1 import (
    CreditNotesCollection,
    DevolutionsCollection,
)
from kardex.core.default_values import SALE_CLIENT_ID
from kardex.core.shift_register.validate_shift_link import validate_shift_link
from kardex.tools import InvalidOperation, BranchNotFound, ClientNotFound, ProductNotFound


from .process_devolution import process_devolution, process_anon_devolution


def _ensure_allowed(decision: PolicyDecision) -> None:
    if decision.allowed:
        return
    raise InvalidOperation(cast(str, decision.reason))


class DevolutionRegister:
    def __init__(
        self,
        devolutions_repo: DevolutionsRepository,
        branches_repo: BranchesRepository,
        products_repo: ProductsRepository,
        clients_repo: ClientsRepository,
        invoices_repo: InvoicesRepository,
        credit_notes_col: Any = None,
        devolutions_col: Any = None,
    ) -> None:
        """
        Inicializa la clase con sus dependencias (Inyección de Dependencias).
        """
        self.devolutions_repo = devolutions_repo
        self.branches_repo = branches_repo
        self.products_repo = products_repo
        self.clients_repo = clients_repo
        self.invoices_repo = invoices_repo
        self._credit_notes_col = credit_notes_col
        self._devolutions_col = devolutions_col

    async def _register_transaction(
        self,
        devolution: DevolutionInDb,
        process_function: Callable[[DevolutionInDb], Coroutine],
    ):
        """
        Método privado que maneja la lógica común de validación, registro y reintentos.
        """

        await self._validate_document(devolution)

        max_retries = 3
        for _ in range(max_retries):
            try:
                # Llama a la función de proceso específica (process_devolution o process_anon_devolution)
                return await process_function(devolution)
            except OperationFailure as e:
                if e.code == 112:  # WriteConflict
                    await asyncio.sleep(0.3)
                else:
                    raise InvalidOperation(f"Database error: {e}")
            except InvalidOperation:
                raise
            except Exception as e:
                raise InvalidOperation(f"An unexpected error occurred: {e}")

        raise InvalidOperation("Server is too busy, please try again later")

    async def create_devolution(self, body: CreateDevolution) -> DevolutionInDb:
        """Valida y crea una nueva devolución en estado open."""
        await validate_shift_link(body.shiftId, body.branchId)
        payment_type = await self._validate_invoice_and_items(
            branch_id=body.branchId,
            client_id=body.clientId,
            original_invoice_id=body.originalInvoiceId,
            returned_items=body.returnedItems,
        )
        if payment_type is not None:
            body.originalInvoicePaymentType = payment_type
        return await self.devolutions_repo.create_devolution(body)

    async def confirm_devolution(self, devolution_id: str) -> DevolutionInDb:
        """Procesa una devolución para un cliente específico."""

        devolution = await self.devolutions_repo.get_devolution_by_id(devolution_id)
        if devolution is None:
            raise InvalidOperation("Devolution not found")

        _ensure_allowed(
            DevolutionPolicy().confirmation_client_decision(
                devolution, anonymous=False, sale_client_id=SALE_CLIENT_ID
            )
        )

        return await self._register_transaction(devolution, process_devolution)

    async def confirm_anon_devolution(
        self, devolution_id: str
    ) -> Tuple[DevolutionInDb, List[ProductAccountInDb]]:
        """Procesa una devolución anónima (sin cliente)."""

        devolution = await self.devolutions_repo.get_devolution_by_id(devolution_id)
        if devolution is None:
            raise InvalidOperation("Devolution not found")

        _ensure_allowed(
            DevolutionPolicy().confirmation_client_decision(
                devolution, anonymous=True, sale_client_id=SALE_CLIENT_ID
            )
        )

        return await self._register_transaction(devolution, process_anon_devolution)

    async def _validate_returned_quantities(
        self,
        *,
        invoice: Any,
        returned_items: list[Any],
        exclude_devolution_id: str | None = None,
    ) -> None:
        sale_items = getattr(invoice, "saleItems", None)
        if not sale_items:
            return

        devolutions_col = self._devolutions_col or DevolutionsCollection.get_instance()
        credit_notes_col = self._credit_notes_col or CreditNotesCollection.get_instance()

        prev_devs = await devolutions_col.fetch_devolutions_by_invoice_id(
            invoice.id, None
        )
        prev_cns = await credit_notes_col.fetch_credit_notes_by_invoice_id(invoice.id)

        remaining_by_index = [
            max(
                0,
                int(line.quantity)
                - sum_previously_returned_quantities(prev_cns, idx, line.product.id)
                - sum_previously_returned_from_devolutions(
                    sale_items,
                    prev_devs,
                    idx,
                    exclude_devolution_id=exclude_devolution_id,
                ),
            )
            for idx, line in enumerate(sale_items)
        ]

        for item in returned_items:
            qty = abs(int(getattr(item, "quantity", 0) or 0))
            if qty <= 0:
                raise InvalidOperation("La cantidad a devolver debe ser mayor a 0.")

            idx = getattr(item, "invoiceItemIndex", None)
            if idx is not None:
                if idx < 0 or idx >= len(sale_items):
                    raise InvalidOperation(
                        f"invoiceItemIndex {idx} está fuera de rango para la factura."
                    )
                if item.product.id != sale_items[idx].product.id:
                    raise InvalidOperation(
                        f"El producto {item.product.id} no coincide con la línea {idx} de la factura."
                    )
                if qty > remaining_by_index[idx]:
                    raise InvalidOperation(
                        "La cantidad a devolver supera el saldo disponible de productos en la factura."
                    )
                remaining_by_index[idx] -= qty
            else:
                matching_indices = [
                    i for i, line in enumerate(sale_items) if line.product.id == item.product.id
                ]
                if not matching_indices:
                    raise InvalidOperation(
                        f"El producto {item.product.name} no pertenece a la factura original."
                    )
                qty_left = qty
                for i in matching_indices:
                    if qty_left <= 0:
                        break
                    take = min(qty_left, remaining_by_index[i])
                    remaining_by_index[i] -= take
                    qty_left -= take
                if qty_left > 0:
                    raise InvalidOperation(
                        "La cantidad a devolver supera el saldo disponible de productos en la factura."
                    )

    async def _validate_invoice_and_items(
        self,
        *,
        branch_id: str,
        client_id: str,
        original_invoice_id: str,
        returned_items: list[Any],
        exclude_devolution_id: str | None = None,
    ) -> str | None:
        branch = await self.branches_repo.get_branch_by_id(branch_id)
        if branch is None:
            raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=branch_id)

        if client_id != SALE_CLIENT_ID:
            client = await self.clients_repo.get_client_by_id(client_id)
            if client is None:
                raise ClientNotFound("CLIENT_NOT_FOUND", client_id=client_id)

        policy = DevolutionPolicy()

        _ensure_allowed(policy.items_decision(returned_items))

        product_ids = list(set(item.product.id for item in returned_items))
        products = await self.products_repo.get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise ProductNotFound("PRODUCT_NOT_FOUND")

        if not original_invoice_id:
            return None

        invoice = await self.invoices_repo.get_invoice_by_id(original_invoice_id)
        if invoice is None:
            raise InvalidOperation(
                f"Original invoice {original_invoice_id} not found."
            )
        _ensure_allowed(policy.invoice_decision(invoice))

        await self._validate_returned_quantities(
            invoice=invoice,
            returned_items=returned_items,
            exclude_devolution_id=exclude_devolution_id,
        )

        return invoice.paymentType

    async def _validate_document(self, doc: DevolutionInDb):
        """Valida los datos relacionados antes de la transacción."""
        payment_type = await self._validate_invoice_and_items(
            branch_id=doc.branchId,
            client_id=doc.clientId,
            original_invoice_id=doc.originalInvoiceId,
            returned_items=doc.returnedItems,
            exclude_devolution_id=doc.id,
        )
        if doc.originalInvoicePaymentType is None and payment_type is not None:
            doc.originalInvoicePaymentType = payment_type

        _ensure_allowed(DevolutionPolicy().status_decision(doc))

        # La validacion estricta del turno ocurre al crear la devolucion.
        # Al confirmar se tolera un turno ya cerrado para no dejar devoluciones
        # irresolubles; el consolidado del turno cerrado no se recalcula.
        await validate_shift_link(doc.shiftId, doc.branchId, require_open=False)
