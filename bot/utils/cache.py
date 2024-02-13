from collections import OrderedDict
from typing import Generic, Optional, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class Cache(Generic[K, V]):
    """A least recently used cache."""

    def __init__(self, *, limit: int = 128) -> None:
        self.__limit = limit
        self.__cache: OrderedDict[K, V] = OrderedDict()

    def put(self, key: K, value: V) -> None:
        """Put an element in the cache."""
        self.__cache[key] = value
        self.__cache.move_to_end(key)

        if len(self.__cache) > self.__limit:
            self.__cache.popitem(last=False)

    def get(self, key: K) -> Optional[V]:
        """Get an element from the cache."""
        value = self.__cache.get(key, None)
        if value is None:
            return None

        self.__cache.move_to_end(key)
        return value
