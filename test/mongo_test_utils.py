"""Helpers compartidos por las pruebas que necesitan MongoDB real.

La suite normal del proyecto es unitaria. Las pruebas de integracion se
marcan con ``skipif`` cuando no hay un Mongo alcanzable, para que
``pytest`` siga pasando en cualquier entorno.
"""

import os


def mongo_url() -> str:
    return os.getenv("MONGO_URL", "mongodb://localhost:27017")


def mongo_available() -> bool:
    try:
        from pymongo import MongoClient

        with MongoClient(mongo_url(), serverSelectionTimeoutMS=300) as client:
            client.admin.command("ping")
        return True
    except Exception:
        return False
