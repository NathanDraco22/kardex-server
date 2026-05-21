import asyncio
from typing import Callable, Coroutine, List, Tuple
from pymongo.errors import OperationFailure

from kardex.repos.v1.devolutions import (
    DevolutionInDb,
    DevolutionsRepository,
)
from kardex.repos.v1.clients import ClientsRepository
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.branches import BranchesRepository
from kardex.repos.v1.products import ProductsRepository
from kardex.core.default_values import SALE_CLIENT_ID
from kardex.tools import InvalidOperation, BranchNotFound, ClientNotFound, ProductNotFound


from .process_devolution import process_devolution, process_anon_devolution


class DevolutionRegister:
    def __init__(
        self,
        devolutions_repo: DevolutionsRepository,
        branches_repo: BranchesRepository,
        products_repo: ProductsRepository,
        clients_repo: ClientsRepository,
    ) -> None:
        """
        Inicializa la clase con sus dependencias (Inyección de Dependencias).
        """
        self.devolutions_repo = devolutions_repo
        self.branches_repo = branches_repo
        self.products_repo = products_repo
        self.clients_repo = clients_repo

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
            except Exception as e:
                raise InvalidOperation(f"An unexpected error occurred: {e}")

        raise InvalidOperation("Server is too busy, please try again later")

    async def confirm_devolution(self, devolution_id: str) -> DevolutionInDb:
        """Procesa una devolución para un cliente específico."""

        devolution = await self.devolutions_repo.get_devolution_by_id(devolution_id)
        if devolution is None:
            raise InvalidOperation("Devolution not found")

        if devolution.clientId == SALE_CLIENT_ID:
            raise InvalidOperation("Use the anonymous devolution endpoint for this client.")

        return await self._register_transaction(devolution, process_devolution)

    async def confirm_anon_devolution(
        self, devolution_id: str
    ) -> Tuple[DevolutionInDb, List[ProductAccountInDb]]:
        """Procesa una devolución anónima (sin cliente)."""

        devolution = await self.devolutions_repo.get_devolution_by_id(devolution_id)
        if devolution is None:
            raise InvalidOperation("Devolution not found")

        if devolution.clientId != SALE_CLIENT_ID:
            raise InvalidOperation("Invalid client ID for anonymous devolution.")

        return await self._register_transaction(devolution, process_anon_devolution)

    async def _validate_document(self, doc: DevolutionInDb):
        """Valida los datos relacionados antes de la transacción."""
        branch = await self.branches_repo.get_branch_by_id(doc.branchId)
        if branch is None:
            raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=doc.branchId)

        # Valida el cliente solo si no es la venta anónima
        if doc.clientId != SALE_CLIENT_ID:
            client = await self.clients_repo.get_client_by_id(doc.clientId)
            if client is None:
                raise ClientNotFound("CLIENT_NOT_FOUND", client_id=doc.clientId)

        product_ids = list(set(item.product.id for item in doc.returnedItems))
        products = await self.products_repo.get_product_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise ProductNotFound("PRODUCT_NOT_FOUND")

        if doc.status != "open":
            raise InvalidOperation("Devolution is not open.")
