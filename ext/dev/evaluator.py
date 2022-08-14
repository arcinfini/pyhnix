import logging, datetime, traceback
from re import RegexFlag, compile as re_compile
from io import BytesIO
from typing import Optional

from discord.ext import commands
from discord import Interaction
import discord

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# from utils.checks import is_botadmin

CODESTRING = r".*(eval|aexec)\s+?`{3}(py)?\n?(?P<code>[\s\S]*?)`{3}\n?\s*(?P<content>[\s\S]*)"
CODEPATTERN = re_compile(CODESTRING, RegexFlag.IGNORECASE)

class DeleteButton(discord.ui.Button):
    """
    A button that deletes the message it is attached to.
    """

    def __init__(self, *, label='delete', custom_id=None):
        custom_id = f'{custom_id}-{label}' if custom_id is not None else custom_id

        super().__init__(label=label, style=discord.ButtonStyle.red, custom_id=custom_id)

    async def callback(self, interaction: Interaction):
        message = interaction.message
        await message.delete()

class ExecuteButton(discord.ui.Button):

    def __init__(self, *, label='execute', timeout_at, custom_id=None):
        custom_id = f'{custom_id}-{label}' if custom_id is not None else custom_id
        
        super().__init__(label=label, style=discord.ButtonStyle.green, custom_id=custom_id)

        self.timeout_at = timeout_at

    def format_dt(self, result="No Result"):
        
        return '```py\n%s```' % (result)

    def __source(self, to_eval):
        return f'async def __ex(message, interaction): ' + \
        ''.join(f'\n\t{l}' for l in to_eval.split('\n'))

    async def callback(self, interaction: Interaction):

        message_reference = interaction.message.reference
        message = await interaction.channel.fetch_message(message_reference.message_id)
        if message is None:
            # Initial message is deleted remove button.
            await interaction.message.edit(view=None)
            return

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

class ExecuteView(discord.ui.View):

    def __init__(self, *, message:discord.Message, timeout, constant, custom_id=None):
        super().__init__(timeout=timeout)

        timeout_at = message.created_at + datetime.timedelta(seconds=timeout)

        self.add_item(ExecuteButton(timeout_at=timeout_at, custom_id=custom_id))
        self.add_item(DeleteButton(custom_id=custom_id))

        self.__author = message.author.id

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.__author


class Main(commands.Cog, name='code'):
    """
    allows for code to be ran externally
    """
    class EvalConverter(commands.FlagConverter, prefix='-', delimiter=' '):
        timeout: Optional[int] = commands.Flag(aliases=['t'], default=3600)
        constant: Optional[bool] = commands.Flag(aliases=['b'], default=False)
    
    def __init__(self, bot):
        self.bot:commands.Bot = bot
        

        logger.info("%s initialized" % __name__)

    @commands.command(aliases=['aexec'])
    # @is_botadmin()
    async def eval(self, ctx:commands.Context, *, flags:EvalConverter):
        timeout = flags.timeout if not flags.constant else None
        
        view = ExecuteView(message=ctx.message, timeout=timeout, constant=flags.constant, custom_id=None)
        
        await ctx.reply("```...```",mention_author=False, view=view)
            

    @commands.command(name='lambda')
    async def _lambda(self, ctx:commands.Context, *, code:str):
        try: result = eval(code)
        except Exception as e: result = str(e)
        finally:
            await ctx.reply(result or "success", mention_author=False)

async def setup(bot):
    await bot.add_cog(Main(bot))