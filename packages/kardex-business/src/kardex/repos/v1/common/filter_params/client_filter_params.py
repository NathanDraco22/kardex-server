from .base_filter_params import BaseFilterParams

class ClientFilterParams(BaseFilterParams):
    group: str | None = None
    hasMovements: bool | None = None
