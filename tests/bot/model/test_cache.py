from collections import OrderedDict

from bot.model.cache import Cache


def test_cache_initialization() -> None:
    cache = Cache[int, str](limit=5)
    assert cache._Cache__limit == 5  # type: ignore [attr-defined]
    assert isinstance(cache._Cache__cache, OrderedDict)  # type: ignore [attr-defined]

    cache = Cache[int, str]()
    assert cache._Cache__limit == 128  # type: ignore [attr-defined]
    assert isinstance(cache._Cache__cache, OrderedDict)  # type: ignore [attr-defined]


def test_put_and_get() -> None:
    """Test insertion and removal of cache values."""
    cache = Cache[int, str](limit=2)
    cache.put(1, "one")
    assert cache.get(1) == "one"

    cache.put(2, "two")
    assert cache.get(2) == "two"

    # Test that getting updates the LRU order
    cache.get(1)
    cache.put(3, "three")
    assert cache.get(1) == "one"
    assert cache.get(2) is None  # 2 should be evicted


def test_cache_eviction() -> None:
    """Test deletion of oldest record once cache fills."""
    cache = Cache[int, str](limit=2)
    cache.put(1, "one")
    cache.put(2, "two")
    cache.put(3, "three")
    assert cache.get(1) is None  # 1 should be evicted
    assert cache.get(2) == "two"
    assert cache.get(3) == "three"


def test_cache_miss() -> None:
    """Test missing entry with `cache.get`."""
    cache = Cache[int, str](limit=2)
    assert cache.get(1) is None  # No entry yet

    cache.put(1, "one")
    assert cache.get(1) == "one"
    assert cache.get(2) is None  # No entry for key 2
