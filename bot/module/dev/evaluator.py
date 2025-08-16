from bot.core import Client, Gear


class Main(Gear, name="Evaluator"):
    """Code Evaluation Commands."""


async def setup(bot: Client) -> None:
    """Initialize the module."""
    await bot.add_cog(Main(bot))
