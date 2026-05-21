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


class DocumentAlreadyExists(KardexException):
    def __init__(self, message: str, doc_number: str | None = None):
        self.doc_number = doc_number
        super().__init__(message)


class ProductNotFound(KardexException):
    def __init__(self, message: str, product_id: str | None = None):
        self.product_id = product_id
        super().__init__(message)


class ClientNotFound(KardexException):
    def __init__(self, message: str, client_id: str | None = None):
        self.client_id = client_id
        super().__init__(message)


class ReceiptNotFound(KardexException):
    def __init__(self, message: str, receipt_id: str | None = None):
        self.receipt_id = receipt_id
        super().__init__(message)


class ReceiptAlreadyDeleted(KardexException):
    pass


class SameBranchTransferError(KardexException):
    def __init__(self, message: str, branch_id: str | None = None):
        self.branch_id = branch_id
        super().__init__(message)


class InvalidOperation(KardexException):
    def __init__(self, message: str, detail: str | None = None):
        self.detail = detail
        super().__init__(message)
