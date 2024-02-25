import inspect

from typing import Union
from types import FunctionType, LambdaType

Filter = Union[LambdaType, FunctionType]


class Permission:
    def __init__(self, _filter: Filter):
        if not callable(_filter):
            raise TypeError("Filter must be function")

        self.filter = _filter

    async def check(self, message) -> bool:
        if inspect.iscoroutine(self.filter):
            return await self.filter(message)

        return self.filter(message)


OWNER = Permission(lambda message: message.out)
ALL = Permission(lambda message: True)


def perm(func, permission: Permission):
    previous = getattr(func, "permissions", [])
    func.permissions = previous + [permission]
    return func


def owner(func):
    return perm(func, OWNER)


def unrestricted(func):
    return perm(func, ALL)


class Security:
    def __init__(self, db):
        self.db = db

    def approved_user(self, message) -> bool:
        return message.from_id in self.db.get("teagram.loader", "users", [])

    async def check_permissions(self, func: FunctionType, message) -> bool:
        permissions = getattr(func, "permissions", [])

        _approved_user = self.approved_user(message)
        _owner = OWNER in permissions

        if _owner and not _approved_user:
            return False

        return True
