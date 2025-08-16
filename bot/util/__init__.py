from enum import Enum
from typing import Self

from .singleton import SingletonBase as SingletonBase


class Mode(Enum):
    """The modes the program can be ran in."""

    DEV = 0
    PROD = 10

    @classmethod
    def from_str(cls, label: str) -> Self:
        """Transform a string into an enum value."""
        return cls[label.upper()]
