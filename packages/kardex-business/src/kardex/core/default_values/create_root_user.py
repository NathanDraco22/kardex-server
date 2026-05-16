from kardex.repos.v1.users.models.user_model import UserInDb
from kardex.services.mongo_collections.v1 import UsersCollection
from kardex.core.security import SysPasswordHasher
from kardex.tools import TimeTools


async def create_root_user():
    hashed_password = SysPasswordHasher.hash_password("NeptunoRoot")
    root_user = UserInDb(
        id="root",
        username="Neptuno",
        password=hashed_password,
        isActive=True,
        isInternal=True,
        role="Admin",
        createdAt=TimeTools.get_now_in_milliseconds(),
    )

    await UsersCollection().create_user_if_absent(
        root_user.id,
        root_user.model_dump(),
    )
