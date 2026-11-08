"""Script de migración para convertir imágenes de sucursales en Base64 a URLs públicas (imageUrl).

Modo de uso:
    uv run python tools/migrate_branch_images.py --dry-run
    uv run python tools/migrate_branch_images.py --tenant mi_empresa
"""

import argparse
import asyncio
import base64
import importlib
import json
import os
import sys
from typing import Any
from dotenv import load_dotenv
import httpx
from pymongo import AsyncMongoClient

load_dotenv()


def clean_base64(raw_b64: str) -> bytes:
    """Elimina encabezados data:image/...;base64, si existen y decodifica a bytes."""
    if "," in raw_b64:
        raw_b64 = raw_b64.split(",", 1)[1]
    return base64.b64decode(raw_b64.strip())


async def upload_via_http(
    uploader_url: str,
    tenant: str,
    file_bytes: bytes,
    file_name: str,
) -> str:
    """Sube la imagen mediante multipart HTTP al endpoint de service-manager / imágenes."""
    clean_uploader_url = uploader_url.rstrip("/")
    target_url = f"{clean_uploader_url}/{tenant}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        files = {
            "image": (file_name, file_bytes, "image/jpeg"),
        }
        response = await client.post(target_url, files=files)
        response.raise_for_status()
        data = response.json()
        url = data.get("url")
        if not url:
            raise ValueError(f"Respuesta inesperada al subir imagen: {data}")
        return url


def upload_via_gcs_direct(
    bucket_name: str,
    blob_path: str,
    file_bytes: bytes,
) -> str:
    """Sube la imagen directamente a Google Cloud Storage si las credenciales existen."""
    try:
        storage_module = importlib.import_module("google.cloud.storage")
        sa_module = importlib.import_module("google.oauth2.service_account")
    except ImportError as e:
        raise ImportError(
            "Para usar --direct-gcs debes tener instalada la dependencia google-cloud-storage."
        ) from e

    b64_key = os.environ.get("GCS_KEY")
    if not b64_key:
        raise ValueError("Variable de entorno GCS_KEY no configurada.")

    credentials_json = base64.b64decode(b64_key).decode("utf-8")
    credentials_dict = json.loads(credentials_json)
    credentials = sa_module.Credentials.from_service_account_info(credentials_dict)

    client = storage_module.Client(credentials=credentials)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    blob.cache_control = "public, max-age=31536000"
    blob.upload_from_string(file_bytes, content_type="image/jpeg")
    return blob.public_url


async def run_migration(
    mongo_url: str,
    db_name: str,
    tenant: str,
    uploader_url: str,
    gcs_bucket: str,
    use_direct_gcs: bool,
    dry_run: bool,
    force: bool,
):
    print("=" * 60)
    print("Iniciando migración de imágenes de sucursales a imageUrl")
    print(f"MongoDB URL : {mongo_url}")
    print(f"Base de datos: {db_name}")
    print(f"Tenant / App: {tenant}")
    print(f"Modo Dry Run: {'ACTIVADO (No modificará datos)' if dry_run else 'DESACTIVADO'}")
    print(f"Modo Forzar : {force}")
    print("=" * 60)

    client: AsyncMongoClient[dict[str, Any]] = AsyncMongoClient(mongo_url)
    db = client[db_name]
    branches_collection = db["Branches"]

    query: dict[str, Any] = {
        "image": {"$exists": True, "$ne": "", "$type": "string"}
    }
    if not force:
        query["$or"] = [
            {"imageUrl": {"$exists": False}},
            {"imageUrl": None},
            {"imageUrl": ""},
        ]

    cursor = branches_collection.find(query)
    branches = await cursor.to_list(length=500)

    print(f"Sucursales encontradas para migración: {len(branches)}")
    if not branches:
        print("No hay sucursales pendientes de migración.")
        return

    migrated_count = 0
    errors_count = 0

    for branch in branches:
        branch_id = branch.get("id") or str(branch.get("_id"))
        branch_name = branch.get("name", "Sin Nombre")
        raw_b64 = branch.get("image", "")

        print(f"\nProcesando sucursal: '{branch_name}' (ID: {branch_id})")

        try:
            image_bytes = clean_base64(raw_b64)
            file_size_kb = len(image_bytes) / 1024
            print(f"  Tamaño de imagen Base64: {file_size_kb:.2f} KB")

            if dry_run:
                print(f"  [DRY-RUN] Se subiría 'branch_{branch_id}.jpg' y se asignaría imageUrl.")
                migrated_count += 1
                continue

            # Subida
            file_name = f"branch_{branch_id}.jpg"
            if use_direct_gcs and os.environ.get("GCS_KEY"):
                blob_name = f"{tenant}/{file_name}"
                print(f"  Subiendo directamente a GCS bucket '{gcs_bucket}', path: '{blob_name}'...")
                public_url = upload_via_gcs_direct(gcs_bucket, blob_name, image_bytes)
            else:
                print(f"  Subiendo vía servicio HTTP a '{uploader_url}/{tenant}'...")
                public_url = await upload_via_http(uploader_url, tenant, image_bytes, file_name)

            print(f"  URL generada: {public_url}")

            # Actualización en MongoDB conservando 'image'
            await branches_collection.update_one(
                {"_id": branch["_id"]},
                {"$set": {"imageUrl": public_url}},
            )
            print("  Base de datos actualizada con éxito ($set: imageUrl).")
            migrated_count += 1

        except Exception as e:
            print(f"  ERROR al migrar sucursal '{branch_name}': {e}", file=sys.stderr)
            errors_count += 1

    print("\n" + "=" * 60)
    print("Resumen de Migración:")
    print(f"  Total procesadas con éxito: {migrated_count}")
    print(f"  Errores encontrados      : {errors_count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Migrar imágenes Base64 de sucursales a Google Cloud Storage / imageUrl."
    )
    parser.add_argument(
        "--mongo-url",
        default=os.getenv("MONGO_URL", "mongodb://localhost:27017"),
        help="URL de conexión a MongoDB",
    )
    parser.add_argument(
        "--db-name",
        default=os.getenv("DB_NAME", "LedgerDB"),
        help="Nombre de la base de datos",
    )
    parser.add_argument(
        "--tenant",
        default=os.getenv("TENANT_NICKNAME", os.getenv("DB_NAME", "default")),
        help="Identificador del tenant o carpeta en GCS",
    )
    parser.add_argument(
        "--uploader-url",
        default=os.getenv("IMAGE_UPLOAD_URL", "http://localhost:8000/api/v1/images/upload/neptuno"),
        help="URL base del endpoint de subida de imágenes de service-manager",
    )
    parser.add_argument(
        "--gcs-bucket",
        default=os.getenv("GCS_BUCKET", "neptuno_bucket"),
        help="Nombre del bucket de Google Cloud Storage",
    )
    parser.add_argument(
        "--direct-gcs",
        action="store_true",
        help="Usar subida directa a GCS mediante GCS_KEY en lugar de HTTP uploader",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular el proceso sin escribir en la base de datos ni subir archivos",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar migración incluso si la sucursal ya tiene imageUrl",
    )

    args = parser.parse_args()

    asyncio.run(
        run_migration(
            mongo_url=args.mongo_url,
            db_name=args.db_name,
            tenant=args.tenant,
            uploader_url=args.uploader_url,
            gcs_bucket=args.gcs_bucket,
            use_direct_gcs=args.direct_gcs,
            dry_run=args.dry_run,
            force=args.force,
        )
    )


if __name__ == "__main__":
    main()
