from discord import TextStyle
from discord import ui as dui
from discord.utils import MISSING


class DateInput(dui.TextInput):
    """A TextInput specifically for dates."""

    def __init__(
        self, *, label: str, custom_id: str = MISSING, required: bool = True
    ) -> None:
        super().__init__(
            label=label,
            custom_id=custom_id,
            required=required,
            style=TextStyle.short,
            placeholder="DOTW MM-DD(-YY) HH:MM AM/PM",
            default="Tuesday 12-01 10:00 PM",
        )
