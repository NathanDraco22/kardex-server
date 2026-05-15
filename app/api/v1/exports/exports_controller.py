from fastapi.responses import FileResponse
from repos.v1.products import ProductsRepository, ProductsDataSource
from services.excel_service import PriceListService, PriceListSheet, PriceListRow

class ExportsController:
    def __init__(self, products_repo: ProductsRepository):
        self.products_repo = products_repo
        self.price_list_service = PriceListService()

    async def export_price_list(self, branch_id: str) -> FileResponse:
        rows = []
        async for product in self.products_repo.get_all_product_in_branch_streamed(branchId=branch_id):
            row = PriceListRow(
                code=product.code,
                productName=product.name,
                brandName=product.brandName,
                unitName=product.unitName,
                salePrice=product.saleProfile.salePrice / 100,
                salePrice2=product.saleProfile.salePrice2 / 100,
                salePrice3=product.saleProfile.salePrice3 / 100,
            )
            rows.append(row)
        
        sheet = PriceListSheet(
            name="Lista de Precios",
            title="Lista de Precios",
            subtitle="Generado automáticamente",
            rows=rows
        )

        file_path = self.price_list_service.create_price_list_xslx([sheet])

        return FileResponse(
            path=file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="lista_de_precios.xlsx",
        )

exports_controller = ExportsController(
    products_repo=ProductsRepository(ProductsDataSource())
)
