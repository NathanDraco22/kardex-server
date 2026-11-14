import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kardex.kardex_config import KardexConfig
from kardex.services import MongoService


@asynccontextmanager
async def lifespan(app: FastAPI):
    is_lite = os.getenv("LITE_MODE", "false").lower() == "true"

    if is_lite:
        KardexConfig().letInvoiceWithNegative = True
        KardexConfig().followTransaction = False
        KardexConfig().createFullProductProfile = True
    else:
        KardexConfig().letInvoiceWithNegative = False
        KardexConfig().followTransaction = True
        KardexConfig().createFullProductProfile = False

    let_negative = os.getenv("LET_NEGATIVE")
    if let_negative is not None:
        let_negative_value = let_negative.lower() == "true"
        KardexConfig().letInvoiceWithNegative = let_negative_value

    # Solo el cliente Mongo: indices y datos semilla son por tenant y se
    # aprovisionan con ``provision_tenant`` / ``migrate_tenants``.
    await MongoService().init_client()

    yield
