import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.services_initializer import init_services
from core.scheduler.app_scheduler import AppScheduler
from kardex.kardex_config import KardexConfig


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

    await init_services()
    if os.getenv("MODE") != "DEV":
        await AppScheduler().start_task()
    yield
