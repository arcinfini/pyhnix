import typing
from collections import OrderedDict


T = typing.TypeVar("T")


class LRUCache(typing.Generic[T]):
    """
    A least recently used cache implemented to lower the database calls with the
    team commands
    """

    def __init__(self, *, limit: int = 128):
        self.__limit = limit
        self.__cache = OrderedDict()

    def put(self, key, value: T):
        self.__cache[key] = value
        self.__cache.move_to_end(key)

        if len(self.__cache) > self.__limit:
            self.__cache.popitem(last=False)

    def get(self, key) -> typing.Optional[T]:
        value = self.__cache.get(key, None)
        if value is None:
            return None

        self.__cache.move_to_end(key)
        return value
