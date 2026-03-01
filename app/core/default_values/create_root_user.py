from repos.v1.users.models.user_model import UserInDb
from services.mongo_collections.v1 import UsersCollection

from tools import TimeTools


async def create_root_user():
    root_user = UserInDb(
        id="root",
        username="Neptuno",
        password="NeptunoRoot",
        isActive=True,
        isInternal=True,
        role="Admin",
        createdAt=TimeTools.get_now_in_milliseconds(),
    )

    await UsersCollection().create_user_if_absent(
        root_user.id,
        root_user.model_dump(),
    )
