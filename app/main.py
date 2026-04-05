import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from api.v1.router import router_v1
from app_lifespan import lifespan
from tools import NotModified, not_modified_exception_handler
from scalar_fastapi import get_scalar_api_reference

load_dotenv()

current_mode = os.getenv("MODE")
open_api_url = "/openapi.json"
if current_mode == "PROD":
    open_api_url = None

app = FastAPI(
    title="Kardex Server Lite",
    openapi_url=open_api_url,
    lifespan=lifespan,
)


@app.get("/sdoc", include_in_schema=False)
async def get_sdoc():
    return get_scalar_api_reference(openapi_url=app.openapi_url)


app.add_exception_handler(NotModified, not_modified_exception_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_v1, prefix="/api/v1")
