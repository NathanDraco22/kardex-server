import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.services_initializer import init_services
from core.scheduler.app_scheduler import AppScheduler
from kardex.kardex_config import KardexConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    KardexConfig().letInvoiceWithNegative = True
    await init_services()
    if os.getenv("MODE") != "DEV":
        await AppScheduler().start_task()
    yield
