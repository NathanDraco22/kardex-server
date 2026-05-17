class KardexException(Exception):
    pass


class InsufficientBalanceError(KardexException):
    def __init__(self, message: str, product_id: str | None = None,
                 product_name: str | None = None):
        self.product_id = product_id
        self.product_name = product_name
        super().__init__(message)


class BranchNotFound(KardexException):
    def __init__(self, message: str, branch_id: str | None = None):
        self.branch_id = branch_id
        super().__init__(message)
