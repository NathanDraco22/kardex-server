from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

from kardex.tools import NotModified
from kardex.tools.kardex_exceptions import (
    InsufficientBalanceError,
    BranchNotFound,
    DocumentAlreadyExists,
    ProductNotFound,
    ClientNotFound,
    ReceiptNotFound,
    ReceiptAlreadyDeleted,
    SameBranchTransferError,
    InvalidOperation,
    DirectStockAdjustmentBlocked,
)


async def not_modified_handler(request: Request, exc: Exception):
    return Response(status_code=304)


async def handle_insufficient_balance(request: Request, exc: Exception):
    e = exc if isinstance(exc, InsufficientBalanceError) else None
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "productId": e.product_id if e else None, "productName": e.product_name if e else None},
    )


async def handle_branch_not_found(request: Request, exc: Exception):
    e = exc if isinstance(exc, BranchNotFound) else None
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "branchId": e.branch_id if e else None},
    )


async def handle_document_exists(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)},
    )


async def handle_not_found(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def handle_bad_request(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def handle_forbidden(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc)},
    )


_exception_handlers = {
    NotModified: not_modified_handler,
    InsufficientBalanceError: handle_insufficient_balance,
    BranchNotFound: handle_branch_not_found,
    DocumentAlreadyExists: handle_document_exists,
    ProductNotFound: handle_not_found,
    ClientNotFound: handle_not_found,
    ReceiptNotFound: handle_not_found,
    ReceiptAlreadyDeleted: handle_bad_request,
    SameBranchTransferError: handle_bad_request,
    InvalidOperation: handle_bad_request,
    DirectStockAdjustmentBlocked: handle_forbidden,
}


def register_exception_handlers(app: FastAPI):
    for exc_class, handler in _exception_handlers.items():
        app.add_exception_handler(exc_class, handler)
