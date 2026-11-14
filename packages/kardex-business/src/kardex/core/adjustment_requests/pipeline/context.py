from dataclasses import dataclass, field
from typing import Any

from kardex.core.inventory import EntryBatchResult, ExitBatchResult
from kardex.repos.v1.adjust_entries import AdjustEntryInDb
from kardex.repos.v1.adjust_exits import AdjustExitInDb
from kardex.repos.v1.adjustment_requests import (
    AdjustmentRequestInDb,
    AdjustmentRequestItem,
)
from kardex.repos.v1.branches import BranchInDb
from kardex.repos.v1.common.models import EntryItem, ExitItem, UserInfo
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.tools import TimeTools


@dataclass
class AdjustmentRequestPipelineResult:
    """Resultado final del pipeline de aprobación de una solicitud."""

    request: AdjustmentRequestInDb
    adjust_entry: AdjustEntryInDb | None = None
    adjust_exit: AdjustExitInDb | None = None


@dataclass
class AdjustmentRequestContext:
    """Contexto compartido entre los pasos del pipeline.

    Solo contiene datos y parámetros. Las dependencias de infraestructura
    (colecciones, repositorios) se inyectan en cada step por constructor.
    """

    request: AdjustmentRequestInDb
    approved_by: UserInfo
    approver_role: str
    session: Any

    now: int = field(default_factory=TimeTools.get_now_in_milliseconds)
    branch: BranchInDb | None = None

    entry_items: list[AdjustmentRequestItem] = field(default_factory=list)
    exit_items: list[AdjustmentRequestItem] = field(default_factory=list)
    product_ids: list[str] = field(default_factory=list)
    accounts: dict[str, ProductAccountInDb] = field(default_factory=dict)

    exit_doc_id: str | None = None
    exit_doc_number: str | None = None
    exit_batch: ExitBatchResult | None = None
    exit_doc_items: list[ExitItem] = field(default_factory=list)
    exit_doc_data: dict[str, Any] | None = None
    exit_doc: AdjustExitInDb | None = None

    entry_doc_id: str | None = None
    entry_doc_number: str | None = None
    entry_batch: EntryBatchResult | None = None
    entry_doc_items: list[EntryItem] = field(default_factory=list)
    entry_doc_data: dict[str, Any] | None = None
    entry_doc: AdjustEntryInDb | None = None

    updated_request: AdjustmentRequestInDb | None = None
    result: AdjustmentRequestPipelineResult | None = None
