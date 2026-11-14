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
from kardex.tools import (
    TenantIndexBuildError,
    is_valid_tenant_nickname,
    normalize_nickname,
)

SYSTEM_DATABASES = {"admin", "local", "config"}

CORE_SETTINGS_COLLECTION = "CoreSettings"
PRODUCTS_COLLECTION = "Products"


class AdoptTenantError(ValueError):
    """La base legacy no se puede adoptar sin intervencion manual."""


def validate_adoptable_nickname(nickname: str) -> str:
    """Valida que el nombre fisico de una base legacy sea adoptable.

    El servidor resuelve siempre el nickname normalizado, asi que una base con
    mayusculas/espacios no se puede adoptar: habria que renombrarla de forma
    fisica con ``mongodump``/``mongorestore``.
    """

    normalized = normalize_nickname(nickname)

    if not is_valid_tenant_nickname(normalized):
        raise AdoptTenantError(
            f"nickname invalido o reservado: {nickname!r}"
        )

    if normalized != nickname:
        raise AdoptTenantError(
            f"la base {nickname!r} no esta normalizada; renombrala antes de "
            f'adoptar: mongodump --db "{nickname}" ... && '
            f'mongorestore --nsFrom "{nickname}.*" '
            f'--nsTo "{normalized}.*"'
        )

    return normalized


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

        # Cualquier Meta (aunque sea de otro producto) descarta la base: no
        # sobrescribimos metadata ajena.
        if meta is not None:
            continue

        collections = await client[name].list_collection_names()
        if not (
            CORE_SETTINGS_COLLECTION in collections
            or PRODUCTS_COLLECTION in collections
        ):
            continue

        candidates.append(name)

    return sorted(candidates)


async def deduplicate_core_settings(
    client: AsyncMongoClient[dict[str, Any]],
    nickname: str,
    dry_run: bool,
) -> list[str]:
    """Conserva el ``CoreSettings`` mas antiguo y elimina el resto.

    El indice unico de ``CoreSettings.nickname`` falla si una base legacy tiene
    mas de un documento (o si colisionan al normalizar el nickname). La
    adopcion unifica todos al nickname de la base, asi que solo puede quedar
    uno.
    """

    collection = client[nickname][CORE_SETTINGS_COLLECTION]
    documents = await collection.find({}).sort(
        [("createdAt", 1), ("_id", 1)]
    ).to_list(length=None)

    if len(documents) <= 1:
        return []

    keeper = documents[0]
    duplicates = documents[1:]
    duplicate_ids = [str(document["_id"]) for document in duplicates]
    label = "se eliminarian" if dry_run else "eliminados"

    print(
        f"  CoreSettings duplicados ({label}): {duplicate_ids}; "
        f"se conserva {keeper['_id']!r}"
    )

    if not dry_run:
        await collection.delete_many(
            {"_id": {"$in": [document["_id"] for document in duplicates]}}
        )

    return duplicate_ids


async def adopt_tenant(
    client: AsyncMongoClient[dict[str, Any]],
    nickname: str,
    dry_run: bool = False,
) -> list[str]:
    """Escribe ``Meta`` y alinea nicknames en una base legacy.

    No renombra la base fisica: si el nombre no esta normalizado lanza
    ``AdoptTenantError`` para que se renombre con mongodump/mongorestore.
    Devuelve los ids de ``CoreSettings`` duplicados detectados.
    """

    normalized = validate_adoptable_nickname(nickname)
    collection = client[nickname][CORE_SETTINGS_COLLECTION]

    removed_ids = await deduplicate_core_settings(client, nickname, dry_run)

    if dry_run:
        return removed_ids

    # El nickname guardado debe ser siempre el de la base (el que resuelve el
    # header normalizado y por el que filtra PATCH), no el valor viejo.
    await collection.update_many(
        {"nickname": {"$ne": normalized}},
        {"$set": {"nickname": normalized}},
    )

    # Meta nace incompleta: ``ensure_indexes_for_tenant`` la cerrara con
    # isProvisioned=True e indexesVersion=target. Si el proceso muere a mitad,
    # el runner la detecta y la repara.
    meta_collection = MetaCollection.get_instance(nickname)
    await meta_collection.write_tenant_meta(
        build_tenant_meta(
            normalized,
            is_provisioned=False,
            indexes_version=0,
        )
    )

    return removed_ids


async def migrate_alt_code(nickname: str, dry_run: bool) -> int:
    """Backfill de ``altCode`` (antes ``set_new_values`` del arranque)."""

    collection = ProductsCollection.get_instance(nickname)._collection
    query = {"altCode": {"$exists": False}}

    if dry_run:
        return await collection.count_documents(query)

    result = await collection.update_many(query, {"$set": {"altCode": ""}})
    return result.modified_count


async def run(args: argparse.Namespace) -> int:
    # El nombre fisico de la base es sensible a mayusculas: no se normaliza el
    # filtro para poder reportar bases legacy mal nombradas.
    only = args.tenant.strip() if args.tenant else None

    # Adoptar implica reconstruir indices: la ficha nace con indexesVersion=0.
    run_indexes = args.indexes or args.adopt or not args.data
    run_data = args.data or not args.indexes

    # El runner usa el mismo MongoService que las colecciones: MetaCollection y
    # ProductsCollection resuelven ``self.client`` desde este singleton. Si ya
    # habia un cliente (proceso embebido / pruebas), se reutiliza y NO se cierra.
    service = MongoService()
    previous_client = getattr(service, "client", None)
    owns_client = previous_client is None

    if owns_client:
        await service.init_client()

    client = service.client

    summary = {
        "reviewed": 0,
        "adopted": 0,
        "deduped": 0,
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

            adoptable: list[str] = []

            for nickname in candidates:
                try:
                    validate_adoptable_nickname(nickname)
                except AdoptTenantError as error:
                    summary["failed"] += 1
                    print(
                        f"  ERROR adopt tenant={nickname}: {error}",
                        file=sys.stderr,
                    )
                    continue

                if args.dry_run:
                    removed_ids = await adopt_tenant(
                        client, nickname, dry_run=True
                    )
                    summary["deduped"] += len(removed_ids)
                    print(f"tenant={nickname} adopt: would-adopt")
                    adoptable.append(nickname)
                    continue

                try:
                    removed_ids = await adopt_tenant(client, nickname)
                except PyMongoError as error:
                    summary["failed"] += 1
                    print(
                        f"  ERROR adopt tenant={nickname}: {error}",
                        file=sys.stderr,
                    )
                    continue

                summary["adopted"] += 1
                summary["deduped"] += len(removed_ids)
                print(f"tenant={nickname} adopt: adopted")
                adoptable.append(nickname)

            tenants = sorted(set(tenants) | set(adoptable))

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
                if run_data:
                    # Deduplicar antes de construir indices: el unico de
                    # CoreSettings.nickname fallaria con datos legacy repetidos.
                    removed_ids = await deduplicate_core_settings(
                        client, nickname, args.dry_run
                    )
                    summary["deduped"] += len(removed_ids)

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
            except (PyMongoError, TenantIndexBuildError) as error:
                summary["failed"] += 1
                print(f"  ERROR tenant={nickname}: {error}", file=sys.stderr)
    finally:
        if owns_client:
            await client.close()
            if hasattr(service, "client"):
                del service.client

    print("Resumen:")
    print(f"  tenants revisados : {summary['reviewed']}")
    print(f"  adoptados         : {summary['adopted']}")
    print(f"  CoreSettings dedup: {summary['deduped']}")
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
            "(escribe Meta y normaliza nicknames). La base debe llamarse ya "
            "como el nickname normalizado."
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
