from dataclasses import dataclass, asdict


@dataclass
class GetExitHistoryParams:
    offset: int
    limit: int
    branch_id: str
    client_id: str | None
    start_date: int | None
    end_date: int | None

    def to_dict(self) -> dict:
        return asdict(self)
