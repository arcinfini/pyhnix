import logging, datetime, traceback
from re import RegexFlag, compile as re_compile
from io import BytesIO
from typing import Optional

from discord.ext import commands
from discord import Interaction
import discord.ui as dui
import discord

logger = logging.getLogger(__name__)

# from utils.checks import is_botadmin

"""
Reimplement timeout portion
remove view on timeout
re-add is botadmin check
"""

CODESTRING = r".*(eval|aexec)\s+?`{3}(py)?\n?(?P<code>[\s\S]*?)`{3}\n?\s*(?P<content>[\s\S]*)"
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

        return '```py\n%s```' % (result)

    def __source(self, to_eval):
        """
        Defines the source of the code being evaluated
        """
        
        return f'async def __ex(message, interaction): ' + \
        ''.join(f'\n\t{l}' for l in to_eval.split('\n'))

    async def interaction_check(self, interaction: Interaction) -> bool:
        message_reference = interaction.message.reference
        eval_message = await interaction.channel.fetch_message(message_reference.message_id)

        # TODO: CHeck if user has clearance for command usage
        # if they do not then inform and then run the delete action

        if eval_message is None:
            interaction.message.delete()
            await interaction.response.send_message(
                "The originating eval has been deleted. Cleaning"
            )
            return False

        valid = eval_message.author.id == interaction.user.id

        if valid:
            interaction.extras['eval_message'] = eval_message
            return True

        return False

    @dui.button(label="execute", style=discord.ButtonStyle.green)
    async def _execute(self, interaction: Interaction, button: dui.Button):

        message = interaction.extras['eval_message']

        match = CODEPATTERN.match(message.content)
        to_eval = match.group('code')
        content = match.group('content')

        await interaction.response.defer()

        try:
            
            exec(
                f'async def __ex(message, interaction, content, local): ' +
                ''.join(f'\n {l}' for l in to_eval.split('\n'))
            )

            result = str(await locals()['__ex'](message, interaction, content, locals()))
        except Exception as e:
            result = self.__source(to_eval) + '\n\n' + traceback.format_exc()
        finally:
            formatted = self.format_dt(result)
            file = None
            if len(formatted) > 2000:
                file= discord.File(BytesIO(bytes(result, "utf=8")), filename="result.txt")
                formatted = self.format_dt("result contents too large, sending fine")
            
            await interaction.message.edit(
                content=formatted, allowed_mentions=discord.AllowedMentions.none(),
                attachments=[file] if file is not None else []
            )

    @dui.button(label="delete", style=discord.ButtonStyle.red)
    async def _delete(self, interaction: Interaction, button: dui.Button):
        
        message = interaction.message
        await message.delete()

class Main(commands.Cog, name='code'):
    """
    allows for code to be ran externally
    """
    class EvalConverter(commands.FlagConverter, prefix='-', delimiter=' '):
        timeout: Optional[int] = commands.Flag(aliases=['t'], default=3600)
        constant: Optional[bool] = commands.Flag(aliases=['b'], default=False)
    
    def __init__(self, bot):
        self.bot:commands.Bot = bot
        
        self.EVAL_VIEW = None

        logger.info("%s initialized" % __name__)

    async def cog_load(self):
        """
        Defines the view to be used as the handler for eval functions
        """
        
        self.EVAL_DELETE = f"EVAL-DELETE-{self.bot.user.id}"
        self.EVAL_EXECUTE = f"EVAL-EXECUTE-{self.bot.user.id}"

        self.EVAL_VIEW = ExecuteView(
            execute_id=self.EVAL_EXECUTE,
            delete_id=self.EVAL_DELETE
        )
        logger.debug("eval view: %s", self.EVAL_VIEW)

        self.bot.add_view(self.EVAL_VIEW)

    async def cog_unload(self):
        # to consider reloads
        self.EVAL_VIEW.stop()

    @commands.command(aliases=['aexec'])
    # @is_botadmin()
    async def eval(self, ctx:commands.Context, *, code:str):
        """
        Enables an eval view
        """

        await ctx.reply("```...```",mention_author=False, view=self.EVAL_VIEW)
            

    @commands.command(name='lambda')
    async def _lambda(self, ctx:commands.Context, *, code:str):
        try: result = eval(code)
        except Exception as e: result = str(e)
        finally:
            await ctx.reply(result or "success", mention_author=False)

async def setup(bot):
    await bot.add_cog(Main(bot))