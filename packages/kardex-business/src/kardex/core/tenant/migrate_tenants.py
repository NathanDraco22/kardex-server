"""Runner de migraciones por tenant (indices y datos).

Uso (desde la raiz de ``kardex-server`` con ``PYTHONPATH=app``):
    python tools/migrate_tenants.py --dry-run
    python tools/migrate_tenants.py --indexes
    python tools/migrate_tenants.py --indexes --tenant tiendaA
    python tools/migrate_tenants.py --data --tenant tiendaA

Enumera las bases del cluster, exige ``Meta.kind == "kardex-tenant"`` y aplica
solo lo que falte. ``stored > target`` no degrada indices: solo advierte.

La logica vive aqui (paquete de dominio) para poder probarla; el CLI del
repositorio es ``tools/migrate_tenants.py``.
"""

import argparse
import asyncio
import os
import sys
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from kardex.services.mongo_collections.v1 import MetaCollection, ProductsCollection
from kardex.services.mongo_collections.v1.meta_collection import (
    TENANT_META_ID,
    TENANT_META_KIND,
)
from kardex.services.mongo_indexes import (
    ensure_indexes_for_tenant,
    get_target_indexes_version,
)
from kardex.tools import normalize_nickname

SYSTEM_DATABASES = {"admin", "local", "config"}


async def list_tenant_databases(
    client: AsyncMongoClient[dict[str, Any]],
    only: str | None = None,
) -> list[str]:
    names = await client.list_database_names()
    tenants: list[str] = []

    for name in names:
        if name in SYSTEM_DATABASES:
            continue
        if only is not None and name != only:
            continue

        meta = await client[name][MetaCollection.collection_name].find_one(
            {"_id": TENANT_META_ID}
        )

        if meta is None or meta.get("kind") != TENANT_META_KIND:
            continue

        tenants.append(name)

    return sorted(tenants)


async def migrate_alt_code(nickname: str, dry_run: bool) -> int:
    """Backfill de ``altCode`` (antes ``set_new_values`` del arranque)."""

    collection = ProductsCollection.get_instance(nickname)._collection
    query = {"altCode": {"$exists": False}}

    if dry_run:
        return await collection.count_documents(query)

    result = await collection.update_many(query, {"$set": {"altCode": ""}})
    return result.modified_count


async def run(args: argparse.Namespace) -> int:
    url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    only = normalize_nickname(args.tenant) if args.tenant else None

    run_indexes = args.indexes or not args.data
    run_data = args.data or not args.indexes

    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(url)
    summary = {
        "reviewed": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "altCode": 0,
    }

    try:
        tenants = await list_tenant_databases(client, only)
        summary["reviewed"] = len(tenants)

        if only is not None and only not in tenants:
            print(f"WARN tenant={only}: no existe o no tiene Meta de Kardex")
            return 1

        target_version = get_target_indexes_version()

        for nickname in tenants:
            meta = await MetaCollection.get_instance(nickname).read_tenant_meta()
            stored = int((meta or {}).get("indexesVersion", 0))

            print(
                f"tenant={nickname} indexes stored={stored} target={target_version}"
            )

            try:
                if run_indexes:
                    if args.dry_run:
                        if stored < target_version:
                            action = "would-update"
                            summary["updated"] += 1
                        elif stored > target_version:
                            action = "skipped-newer"
                            summary["skipped"] += 1
                        else:
                            action = "skipped"
                            summary["skipped"] += 1
                        print(f"  indexes: {action}")
                    else:
                        action = await ensure_indexes_for_tenant(nickname)
                        print(f"  indexes: {action}")
                        if action == "updated":
                            summary["updated"] += 1
                        else:
                            summary["skipped"] += 1

                if run_data:
                    modified = await migrate_alt_code(nickname, args.dry_run)
                    summary["altCode"] += modified
                    label = "altCode pendientes" if args.dry_run else "altCode migrados"
                    print(f"  {label}: {modified}")
            except PyMongoError as error:
                summary["failed"] += 1
                print(f"  ERROR tenant={nickname}: {error}", file=sys.stderr)
    finally:
        await client.close()

    print("Resumen:")
    print(f"  tenants revisados : {summary['reviewed']}")
    print(f"  actualizados      : {summary['updated']}")
    print(f"  omitidos          : {summary['skipped']}")
    print(f"  fallidos          : {summary['failed']}")
    print(f"  altCode procesados: {summary['altCode']}")

    return 0 if summary["failed"] == 0 else 1


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aplica migraciones de indices y datos a los tenants de Kardex."
    )
    parser.add_argument(
        "--indexes",
        action="store_true",
        help="Aplicar migraciones de indices (por defecto si no se indica nada).",
    )
    parser.add_argument(
        "--data",
        action="store_true",
        help="Aplicar migraciones de datos (por defecto si no se indica nada).",
    )
    parser.add_argument(
        "--tenant",
        default=None,
        help="Procesar solo un tenant.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar lo que se haria sin escribir en MongoDB.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(run(parse_args(argv)))


if __name__ == "__main__":
    sys.exit(main())
