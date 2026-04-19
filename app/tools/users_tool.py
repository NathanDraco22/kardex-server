from repos.v1.users import UsersRepository, UsersDataSource, UserInDb


class UsersTool:
    _instance: "UsersTool|None" = None
    __users_repo = UsersRepository(UsersDataSource())

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsersTool, cls).__new__(cls)
        return cls._instance

    _inactive_users: list[UserInDb] = []

    async def refresh_inactive_users(self) -> None:
        res = await self.__users_repo.get_all_inactive_users()
        self._inactive_users = res

    def get_inactive_user_by_id(self, user_id: str) -> UserInDb | None:
        for user in self._inactive_users:
            if user.id == user_id:
                return user
