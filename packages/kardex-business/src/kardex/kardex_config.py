import contextvars
from dataclasses import dataclass


class KardexConfig:
    _instance = None
    letInvoiceWithNegative: bool = False
    followTransaction: bool = True
    createFullProductProfile: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KardexConfig, cls).__new__(cls)
        return cls._instance


@dataclass
class KardexContext:
    businessNickname: str = ""
    branchId: str = ""


kardexCtx = contextvars.ContextVar("kardexCtx", default=KardexContext())
