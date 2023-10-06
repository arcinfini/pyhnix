import logging
import traceback
from io import BytesIO
from re import RegexFlag
from re import compile as re_compile

import discord
import discord.ui as dui
from discord import Interaction
from discord.ext import commands

from internal import client

logger = logging.getLogger(__name__)

import internal.errors as errors
from internal import checks
from internal.utils import is_bot_admin

CODESTRING = r".*(eval|aexec)\s+?(?P<markdown>`{3})?(?P<language>postgresql|sql|python|py)?\n?(?P<code>[\s\S]*)(?(markdown)`{3}|)\n?\s*(?P<content>[\s\S]*)"
CODEPATTERN = re_compile(CODESTRING, RegexFlag.IGNORECASE)


class ExecuteView(dui.View):
    def __init__(self, *, execute_id, delete_id):
        super().__init__(timeout=None)

        self._execute.custom_id = execute_id
        self._delete.custom_id = delete_id

    def format_dt(self, result="No Result"):
        """
        Returns the result formatted within a code block in discord markdown
        """

        return "```py\n%s```" % (result)

    def __source(self, to_eval):
        """
        Defines the source of the code being evaluated
        """

        return f"async def __ex(message, interaction): " + "".join(
            f"\n\t{l}" for l in to_eval.split("\n")
        )

    async def interaction_check(self, interaction: Interaction) -> bool:
        """
        Checks
            - the interaction message exists
            - the channel provided exists
            - the message reference exists
            - the channel is a text channel
            - if the user has clearance for code execution
            - the user running the interaction is the author of the code
        """

        if (
            (result_message := interaction.message) is None
            or (channel := interaction.channel) is None
            or (message_reference := result_message.reference) is None
        ):
            return False

        if not isinstance(channel, discord.TextChannel):
            return False

        # Gets the message that contains the code

        ref_id = message_reference.message_id
        if ref_id is None:
            return False
        code_message = await channel.fetch_message(ref_id)

        # Check if user has clearance for command usage
        # if they do not then inform and then run the delete action
        if not is_bot_admin(interaction.user):
            await self._delete.callback(interaction)
            raise errors.ClearanceError(
                content="You do not have clearance to use this"
            )

        if code_message is None:
            await result_message.delete()
            await interaction.response.send_message(
                "The originating eval has been deleted. Cleaning",
                ephemeral=True,
            )
            return False

        valid = code_message.author.id == interaction.user.id

        if valid:
            interaction.extras["eval_message"] = code_message
            return True

        return False

    @dui.button(label="execute", style=discord.ButtonStyle.green)
    async def _execute(self, interaction: Interaction, button: dui.Button):
        """
        Extracts the code defined within the replied-to message connected to the
        view's message. Then runs the code and edits the interaction message
        with the updated result.
        """

        message = interaction.extras["eval_message"]

        match = CODEPATTERN.match(message.content)

        if match is None:
            await interaction.response.edit_message(
                content="```\nInput not formatted correctly\n```"
            )
            return

        language = match.group("language")
        to_eval = match.group("code")
        content = match.group("content")

        if language.lower() in ["postgresql", "sql"]:
            to_eval = (
                "\tasync with interaction.client.database.acquire() as conn:\n"
                + f"\t\treturn await conn.fetch('''{to_eval}''')"
            )

        await interaction.response.defer()

        result = ""
        try:
            exec(
                f"async def __ex(message, interaction, content, local): "
                + "".join(f"\n {l}" for l in to_eval.split("\n"))
            )

            result = str(
                await locals()["__ex"](message, interaction, content, locals())
            )
        except Exception as e:
            result = self.__source(to_eval) + "\n\n" + traceback.format_exc()
        finally:
            formatted = self.format_dt(result)
            file = None
            if len(formatted) > 2000:
                file = discord.File(
                    BytesIO(bytes(result, "utf=8")), filename="result.txt"
                )
                formatted = self.format_dt(
                    "result contents too large, sending as file"
                )

            await interaction.edit_original_response(
                content=formatted,
                allowed_mentions=discord.AllowedMentions.none(),
                attachments=[file] if file is not None else [],
            )

    @dui.button(label="delete", style=discord.ButtonStyle.red)
    async def _delete(self, interaction: Interaction, button: dui.Button):
        """
        Deletes the eval result message
        """

        if (message := interaction.message) is None:
            return

        await message.delete()


class Main(commands.Cog, name="code"):
    """
    allows for code to be ran externally
    """

    def __init__(self, bot: client.Phoenix):
        self.bot = bot

        logger.info("%s initialized" % __name__)

    async def cog_load(self):
        """
        Defines the view to be used as the handler for eval functions
        """

        bot_user = self.bot.user
        if bot_user is None:
            raise errors.InitializationError(
                content="The bot should be logged in but is not."
            )

        self.EVAL_DELETE = f"EVAL-DELETE-{bot_user.id}"
        self.EVAL_EXECUTE = f"EVAL-EXECUTE-{bot_user.id}"

        self.EVAL_VIEW = ExecuteView(
            execute_id=self.EVAL_EXECUTE, delete_id=self.EVAL_DELETE
        )
        logger.debug("eval view: %s", self.EVAL_VIEW)

        self.bot.add_view(self.EVAL_VIEW)

    async def cog_unload(self):
        """
        Unloads the EVAL_VIEW listener
        """

        self.EVAL_VIEW.stop()

    @commands.command(aliases=["aexec"])
    @checks.is_bot_admin()
    async def eval(self, ctx: commands.Context, *, code: str | None = None):
        """
        Enables an eval view
        """

        if self.EVAL_VIEW is None:
            raise errors.InitializationError(
                content="self.EVAL_VIEW should be defined but is not"
            )

        await ctx.reply("```...```", mention_author=False, view=self.EVAL_VIEW)

    @commands.command(name="lambda")
    async def _lambda(self, ctx: commands.Context, *, code: str):
        result = ""
        try:
            result = eval(code)
        except Exception as e:
            result = str(e)
        finally:
            await ctx.reply(result or "success", mention_author=False)


async def setup(bot):
    await bot.add_cog(Main(bot))
