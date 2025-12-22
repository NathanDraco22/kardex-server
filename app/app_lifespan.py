from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.services_initializer import init_services
from core.scheduler.app_scheduler import AppScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await AppScheduler().start_task()
    await init_services()
    yield
