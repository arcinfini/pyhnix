from typing import Self


class SingletonBase:
    """A base class to implement singleton behavior."""

    _instance: Self | None = None

    def __new__(cls) -> Self:
        """Create or return, if existing, an object."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance
