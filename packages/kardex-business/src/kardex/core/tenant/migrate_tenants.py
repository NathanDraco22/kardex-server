"""Runner de migraciones por tenant (indices, datos y adopcion de DBs legacy).

Uso (desde la raiz de ``kardex-server`` con ``PYTHONPATH=app``):
    python tools/migrate_tenants.py --dry-run
    python tools/migrate_tenants.py --indexes
    python tools/migrate_tenants.py --indexes --tenant tiendaA
    python tools/migrate_tenants.py --data --tenant tiendaA
    python tools/migrate_tenants.py --adopt --dry-run

Enumera las bases del cluster, exige ``Meta.kind == "kardex-tenant"`` y aplica
solo lo que falte. ``stored > target`` no degrada indices: solo advierte.
``--adopt`` reconoce bases sin ``Meta`` que tengan ``CoreSettings`` o
``Products`` (migracion legacy) y les escribe la ficha tecnica.

La logica vive aqui (paquete de dominio) para poder probarla; el CLI del
repositorio es ``tools/migrate_tenants.py``.
"""

import argparse
import asyncio
import sys
from typing import Any

from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import MetaCollection, ProductsCollection
from kardex.services.mongo_collections.v1.meta_collection import (
    TENANT_META_ID,
    TENANT_META_KIND,
    build_tenant_meta,
)
from kardex.services.mongo_indexes import (
    ensure_indexes_for_tenant,
    get_target_indexes_version,
)
from kardex.tools import normalize_nickname

SYSTEM_DATABASES = {"admin", "local", "config"}

CORE_SETTINGS_COLLECTION = "CoreSettings"
PRODUCTS_COLLECTION = "Products"


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


async def list_adoptable_databases(
    client: AsyncMongoClient[dict[str, Any]],
    only: str | None = None,
) -> list[str]:
    """Bases sin ``Meta`` que parecen tenants (tienen CoreSettings o Products)."""

    names = await client.list_database_names()
    candidates: list[str] = []

    for name in names:
        if name in SYSTEM_DATABASES:
            continue
        if only is not None and name != only:
            continue

        meta = await client[name][MetaCollection.collection_name].find_one(
            {"_id": TENANT_META_ID}
        )

        if meta is not None and meta.get("kind") == TENANT_META_KIND:
            continue

        collections = await client[name].list_collection_names()
        if not (
            CORE_SETTINGS_COLLECTION in collections
            or PRODUCTS_COLLECTION in collections
        ):
            continue

        candidates.append(name)

    return sorted(candidates)


async def adopt_tenant(
    client: AsyncMongoClient[dict[str, Any]],
    nickname: str,
) -> None:
    """Escribe ``Meta`` y normaliza nicknames en una base legacy.

    No renombra la base fisica (fuera de alcance): solo alinea lo almacenado.
    """

    normalized = normalize_nickname(nickname)

    core_settings = client[nickname][CORE_SETTINGS_COLLECTION]
    cursor = core_settings.find({})
    async for document in cursor:
        current = document.get("nickname")
        normalized_current = normalize_nickname(current)
        if current != normalized_current:
            await core_settings.update_one(
                {"_id": document["_id"]},
                {"$set": {"nickname": normalized_current}},
            )

    # indexesVersion=0 obliga a que la fase de indices reconstruya lo que falte.
    # Se escribe en la base fisica (``nickname``), aunque el valor almacenado se
    # normalice: renombrar la base queda fuera de alcance.
    meta_collection = MetaCollection.get_instance(nickname)
    await meta_collection.write_tenant_meta(
        build_tenant_meta(
            normalized,
            is_provisioned=True,
            indexes_version=0,
        )
    )


async def migrate_alt_code(nickname: str, dry_run: bool) -> int:
    """Backfill de ``altCode`` (antes ``set_new_values`` del arranque)."""

    collection = ProductsCollection.get_instance(nickname)._collection
    query = {"altCode": {"$exists": False}}

    if dry_run:
        return await collection.count_documents(query)

    result = await collection.update_many(query, {"$set": {"altCode": ""}})
    return result.modified_count


async def run(args: argparse.Namespace) -> int:
    only = normalize_nickname(args.tenant) if args.tenant else None

    # Adoptar implica reconstruir indices: la ficha nace con indexesVersion=0.
    run_indexes = args.indexes or args.adopt or not args.data
    run_data = args.data or not args.indexes

    # El runner usa el mismo MongoService que las colecciones: MetaCollection y
    # ProductsCollection resuelven ``self.client`` desde este singleton.
    service = MongoService()
    await service.init_client()
    client = service.client

    summary = {
        "reviewed": 0,
        "adopted": 0,
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "altCode": 0,
    }

    try:
        try:
            tenants = await list_tenant_databases(client, only)
        except PyMongoError as error:
            print(f"ERROR: no se pudo leer el cluster: {error}", file=sys.stderr)
            return 1

        if args.adopt:
            try:
                candidates = await list_adoptable_databases(client, only)
            except PyMongoError as error:
                print(
                    f"ERROR: no se pudo enumerar bases a adoptar: {error}",
                    file=sys.stderr,
                )
                return 1

            for nickname in candidates:
                if args.dry_run:
                    print(f"tenant={nickname} adopt: would-adopt")
                    continue

                try:
                    await adopt_tenant(client, nickname)
                except PyMongoError as error:
                    summary["failed"] += 1
                    print(
                        f"  ERROR adopt tenant={nickname}: {error}",
                        file=sys.stderr,
                    )
                    continue

                summary["adopted"] += 1
                print(f"tenant={nickname} adopt: adopted")

            tenants = sorted(set(tenants) | set(candidates))

            if only is not None and only not in tenants:
                print(f"WARN tenant={only}: no existe ni es adoptable")
                return 1
        elif only is not None and only not in tenants:
            print(f"WARN tenant={only}: no existe o no tiene Meta de Kardex")
            return 1

        summary["reviewed"] = len(tenants)
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
    print(f"  adoptados         : {summary['adopted']}")
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
        "--adopt",
        action="store_true",
        help=(
            "Adoptar bases legacy sin Meta que tengan CoreSettings o Products "
            "(escribe Meta y normaliza nicknames)."
        ),
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
