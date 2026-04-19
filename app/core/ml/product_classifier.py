from dataclasses import dataclass
from services import ProductClassifierService


@dataclass
class ProductDataStat:
    productId: str
    branchId: str
    productAverage: float
    transactionFrequency: float


@dataclass
class ProductEstimationResult:
    productId: str
    branchId: str
    classification: int


class ProductClassifier:
    _instance: "ProductClassifier|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def estimate_classification(
        self, products_stat: list[ProductDataStat]
    ) -> list[ProductEstimationResult]:
        data = [
            [stat.productAverage, stat.transactionFrequency] for stat in products_stat
        ]
        estimations = ProductClassifierService().process_batch(data)

        results = []
        for index, estimation in enumerate(estimations):
            results.append(
                ProductEstimationResult(
                    productId=products_stat[index].productId,
                    branchId=products_stat[index].branchId,
                    classification=estimation,
                )
            )

        return results
