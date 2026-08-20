from fastapi import HTTPException, status

from kardex.core.devolution_register.devolution_register import DevolutionRegister
from kardex.repos.v1.branches import BranchesRepository, BranchesDataSource
from kardex.repos.v1.clients import ClientsRepository, ClientsDataSource
from kardex.repos.v1.invoices import InvoicesRepository, InvoicesDataSource
from kardex.repos.v1.products import ProductsRepository, ProductsDataSource
from kardex.repos.v1.common.models.history_params import HistoryClientParams
from kardex.repos.v1.devolutions import (
    CreateDevolution,
    UpdateDevolution,
    DevolutionInDb,
    DevolutionsRepository,
    DevolutionsDataSource,
)

from responses.v1 import ListResponse

from kardex.repos.v1.common.filter_params import DevolutionFilterParams


class DevolutionsController:
    def __init__(self, devolutions_repo: DevolutionsRepository) -> None:
        self.devolutions_repo = devolutions_repo
        self.devolution_register = DevolutionRegister(
            devolutions_repo=devolutions_repo,
            branches_repo=BranchesRepository(BranchesDataSource()),
            products_repo=ProductsRepository(ProductsDataSource()),
            clients_repo=ClientsRepository(ClientsDataSource()),
            invoices_repo=InvoicesRepository(InvoicesDataSource()),
        )

    async def create_devolution(self, body: CreateDevolution) -> DevolutionInDb:
        return await self.devolutions_repo.create_devolution(body)

    async def get_all_devolutions(
        self, params: DevolutionFilterParams
    ) -> ListResponse[DevolutionInDb]:
        devolutions = await self.devolutions_repo.get_all_devolutions(params)
        return ListResponse(count=len(devolutions), data=devolutions)

    async def get_all_active_devolutions(
        self, params: DevolutionFilterParams
    ) -> ListResponse[DevolutionInDb]:
        devolutions = await self.devolutions_repo.get_all_active_devolutions(params)
        return ListResponse(count=len(devolutions), data=devolutions)

    async def get_devolution_by_id(self, devolution_id: str) -> DevolutionInDb:
        devolution = await self.devolutions_repo.get_devolution_by_id(devolution_id)
        if devolution is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Devolution not found",
            )
        return devolution

    async def confirm_develution(self, devolution_id: str) -> DevolutionInDb:
        devolution = await self.devolution_register.confirm_devolution(
            devolution_id,
        )

        return devolution

    async def confirm_anon_devolution(self, devolution_id: str) -> DevolutionInDb:
        devolution, _ = await self.devolution_register.confirm_anon_devolution(
            devolution_id,
        )

        return devolution

    async def cancel_devolution_by_id(self, devolution_id: str) -> DevolutionInDb:
        update_devolution = UpdateDevolution(status="cancelled")

        devolution = await self.devolutions_repo.update_devolution_by_id(
            devolution_id,
            update_devolution,
        )
        if devolution is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Devolution not found",
            )
        return devolution

    async def delete_devolution_by_id(self, devolution_id: str) -> DevolutionInDb:
        deleted_devolution = await self.devolutions_repo.delete_devolution_by_id(
            devolution_id
        )
        if deleted_devolution is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Devolution not found",
            )
        return deleted_devolution

    async def get_history_devolutions(
        self, params: HistoryClientParams
    ) -> ListResponse[DevolutionInDb]:
        devolutions = await self.devolutions_repo.get_devolution_history(params)
        return ListResponse(count=len(devolutions), data=devolutions)

    async def get_devolution_by_doc_number(self, doc_number: str) -> DevolutionInDb:
        devolution = await self.devolutions_repo.get_devolution_by_doc_number(
            doc_number
        )
        if devolution is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Devolution not found",
            )
        return devolution


devolutions_controller = DevolutionsController(
    devolutions_repo=DevolutionsRepository(
        devolutions_ds=DevolutionsDataSource(),
    ),
)
