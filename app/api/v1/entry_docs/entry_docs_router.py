from fastapi import APIRouter

from repos.v1.entry_docs import CreateEntryDoc, EntryDocInDb

from .entry_docs_controller import entry_docs_controller


entry_docs_router = APIRouter(tags=["entry_docsV1"])


@entry_docs_router.post("")
async def create_entry_doc(body: CreateEntryDoc) -> EntryDocInDb:
    return await entry_docs_controller.create_entry_doc(body)


@entry_docs_router.get("")
async def get_all_entry_docs() -> list[EntryDocInDb]:
    return await entry_docs_controller.get_all_entry_docs()


@entry_docs_router.get("/{entry_doc_id}")
async def get_entry_doc_by_id(entry_doc_id: str) -> EntryDocInDb:
    return await entry_docs_controller.get_entry_doc_by_id(entry_doc_id)
