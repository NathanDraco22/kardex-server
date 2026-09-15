from kardex.tools import TimeTools, UuidTool
from kardex.repos.v1.common.filter_params import HoldSaleFilterParams

from .data.hold_sales_datasource import HoldSalesDataSource
from .models.hold_sale_model import (
    CreateHoldSale,
    UpdateHoldSale,
    HoldSaleInDb,
    HoldSaleItem,
)


class HoldSalesRepository:
    _instance: "HoldSalesRepository|None" = None

    def __init__(self, hold_sales_ds: HoldSalesDataSource):
        self.hold_sales_ds = hold_sales_ds

    @classmethod
    def get_instance(cls) -> "HoldSalesRepository":
        if cls._instance is None:
            cls._instance = cls(HoldSalesDataSource())
        return cls._instance

    async def create_hold_sale(self, create_hold_sale: CreateHoldSale) -> HoldSaleInDb:
        total_quantity = sum(item.quantity for item in create_hold_sale.items)
        total_amount = 0
        for item in create_hold_sale.items:
            sub_total = item.quantity * item.newPrice * item.conversionFactor
            discount_percent = (
                item.selectedDiscount.percentValue if item.selectedDiscount else 0
            )
            discount = round(sub_total * (discount_percent / 100))
            total_amount += (sub_total - discount)

        new_hold_sale = HoldSaleInDb(
            **create_hold_sale.model_dump(exclude={"totalQuantity", "totalAmount"}),
            id=UuidTool.generate_uuid(),
            totalQuantity=create_hold_sale.totalQuantity or total_quantity,
            totalAmount=create_hold_sale.totalAmount or total_amount,
            createdAt=TimeTools.get_now_in_milliseconds(),
            updatedAt=None,
        )

        await self.hold_sales_ds.create_hold_sale(new_hold_sale.model_dump())
        return new_hold_sale

    async def get_all_hold_sales(
        self, params: HoldSaleFilterParams | None = None
    ) -> list[HoldSaleInDb]:
        query_params = params.model_dump(exclude_none=True) if params else {}
        results = await self.hold_sales_ds.get_all_hold_sales(**query_params)
        models = [HoldSaleInDb.model_validate(result) for result in results]
        return models

    async def get_hold_sale_by_id(self, hold_sale_id: str) -> HoldSaleInDb | None:
        result = await self.hold_sales_ds.get_hold_sale_by_id(hold_sale_id)
        if result is None:
            return None
        return HoldSaleInDb.model_validate(result)

    async def update_hold_sale_by_id(
        self, hold_sale_id: str, hold_sale: UpdateHoldSale
    ) -> HoldSaleInDb | None:
        update_data = hold_sale.model_dump(exclude_unset=True)

        if "items" in update_data and update_data["items"] is not None:
            items = [HoldSaleItem.model_validate(i) for i in update_data["items"]]
            if "totalQuantity" not in update_data or update_data["totalQuantity"] is None:
                update_data["totalQuantity"] = sum(i.quantity for i in items)
            if "totalAmount" not in update_data or update_data["totalAmount"] is None:
                total_amount = 0
                for item in items:
                    sub_total = item.quantity * item.newPrice * item.conversionFactor
                    discount_percent = (
                        item.selectedDiscount.percentValue if item.selectedDiscount else 0
                    )
                    discount = round(sub_total * (discount_percent / 100))
                    total_amount += (sub_total - discount)
                update_data["totalAmount"] = total_amount

        update_data["updatedAt"] = TimeTools.get_now_in_milliseconds()
        result = await self.hold_sales_ds.update_hold_sale_by_id(
            hold_sale_id, update_data
        )
        if result is None:
            return None
        return HoldSaleInDb.model_validate(result)

    async def delete_hold_sale_by_id(self, hold_sale_id: str) -> HoldSaleInDb | None:
        result = await self.hold_sales_ds.delete_hold_sale_by_id(hold_sale_id)
        if result is None:
            return None
        return HoldSaleInDb.model_validate(result)

    async def delete_all_hold_sales_by_branch(self, branch_id: str) -> int:
        return await self.hold_sales_ds.delete_all_hold_sales_by_branch(branch_id)

