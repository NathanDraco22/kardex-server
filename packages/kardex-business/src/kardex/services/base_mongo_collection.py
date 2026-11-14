from typing import Any, TypeVar, Type

from pymongo.asynchronous.collection import AsyncCollection


T = TypeVar("T", bound="BaseMongoCollection")


class BaseMongoCollection:
    """Base de las colecciones Mongo.

    La instancia por defecto (``get_instance()`` sin nickname) queda con
    ``nickname=""`` y resuelve la base de datos en cada acceso a ``_collection``
    a partir de ``kardexCtx``. Asi ninguna referencia guardada durante un
    import, un arranque o un script queda anclada a una base fija.

    Las instancias explicitas (``get_instance(nickname)``) si fijan el tenant y
    se usan en el runner de migraciones, el aprovisionamiento y las pruebas.
    """

    collection_name: str = ""
    _default_instance: Any = None
    _instances: dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._default_instance = None
        cls._instances = {}

    def __init__(self, nickname: str = "") -> None:
        self.nickname = nickname

    @property
    def _collection(self) -> AsyncCollection[dict[str, Any]]:
        # Imports locales para evitar ciclos kardex_config <-> mongo_service.
        from kardex.kardex_config import kardexCtx
        from kardex.services import MongoService

        target = self.nickname or kardexCtx.get().businessNickname
        return MongoService().get_collection(
            self.collection_name, database_name=target
        )

    @classmethod
    def get_instance(cls: Type[T], nickname: str | None = None) -> T:
        if not nickname:
            if cls._default_instance is None:
                cls._default_instance = cls(nickname="")
            return cls._default_instance  # type: ignore[no-any-return]

        if nickname not in cls._instances:
            cls._instances[nickname] = cls(nickname=nickname)

        return cls._instances[nickname]  # type: ignore[no-any-return]

    async def create_indexes(self) -> None:
        """Define los indices de la coleccion. Las subclases lo sobreescriben."""

        return None
