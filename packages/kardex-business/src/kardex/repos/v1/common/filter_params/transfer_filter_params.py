from .base_filter_params import BaseFilterParams

class TransferFilterParams(BaseFilterParams):
    status: str | None = None
    origin: str | None = None
    destination: str | None = None
