from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class GetExitHistoryParams:
    offset: int
    limit: int
    branch_id: str
    client_id: str | None
    start_date: datetime | None
    end_date: datetime | None

    def to_dict(self) -> dict:
        return asdict(self)
