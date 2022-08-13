
import typing, logging
from discord import app_commands, Interaction
import discord, discord.ui as dui

logger = logging.getLogger(__name__)

"""
embedb build [,m_id[, index]]
embedb edit m_id
"""

class Form(dui.Modal):

    def __init__(self, /, **items: typing.Dict[str, dui.Item]):
        super().__init__(title="Embed Builder", timeout=60*15)

        self.items = items

        for _, item in items.items():
            self.add_item(item)

    async def interaction_check(self, interaction: Interaction):
        return True # TODO check for same author

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()

    async def on_error(self, interaction:Interaction, error):
        """"""
        raise error

class EmbedBuilderView(dui.View):

    def __init__(self, embed):
        super().__init__(timeout=60*15)

        self.embed:discord.Embed = embed

    async def prompt(self, interaction: Interaction, button: dui.Button, **kwargs):
        """
        Prompts the user to input content based on the interaction
        """
        required = kwargs.pop('required', False)

        content_in = dui.TextInput(
            label=f"{button.label.title()}{' (OPTIONAL)' if required else ''}",
            required=required,
            **kwargs
        )

        form = Form(**{button.label: content_in})

        await interaction.response.send_modal(form)
        failed = await form.wait()
        if failed: return None

        return form.items[button.label].value

    async def update(self, interaction: Interaction):
        """
        Updates the embed being built
        """

        await interaction.followup.edit_message(
            embed=self.embed, 
            message_id=interaction.message.id
        )

    @dui.button(label="Title", style=discord.ButtonStyle.blurple, row=0)
    async def _title(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input title text
        """

        response = await self.prompt(
            interaction, button, 
            default=self.embed.title, 
            style=discord.TextStyle.short
        )

        self.embed.title = response

        await self.update(interaction)

    @dui.button(label="Description", style=discord.ButtonStyle.blurple, row=0)
    async def _description(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input description text
        """

        response = await self.prompt(
            interaction, button, 
            default=self.embed.description, 
            style=discord.TextStyle.long,
            max_length=2000
        )

        self.embed.description = response

        await self.update(interaction)

    @dui.button(label="Color", style=discord.ButtonStyle.blurple, row=0)
    async def _color(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input color
        """

        response = await self.prompt(
            interaction, button, 
            default=str(self.embed.color), 
            style=discord.TextStyle.short,
            required=True
        )

        self.embed.color = discord.Color.from_str(response)

        await self.update(interaction)

    @dui.button(label="Url", style=discord.ButtonStyle.blurple, row=0)
    async def _url(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input a url
        """

        response = await self.prompt(
            interaction, button, 
            default=self.embed.url,
            style=discord.TextStyle.short
        )

        self.embed.url = response

        await self.update(interaction)

    # TODO: Implement
    # @dui.button(label="timestamp", style=discord.ButtonStyle.blurple, row=0)
    # async def _timestamp(self, interaction: Interaction):
    #     """
    #     Sends a modal to input a timestamp
    #     """

    # @dui.button(label="image", style=discord.ButtonStyle.blurple, row=1)
    # async def _image(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="thumbnail", style=discord.ButtonStyle.blurple, row=1)
    # async def _thumbnail(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="author", style=discord.ButtonStyle.gray, row=1)
    # async def _author(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="footer", style=discord.ButtonStyle.gray, row=1)
    # async def _footer(self, interaction: Interaction):
    #     """"""

    # @dui.select(placeholder="field index", options=[discord.SelectOption(label="null")], row=2)
    # async def _field_index(self, interaction: Interaction, select: dui.Select):
    #     """"""

    # @dui.button(label="edit field", style=discord.ButtonStyle.gray, row=3)
    # async def _edit_field(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="remove field", style=discord.ButtonStyle.gray, row=3)
    # async def _remove_field(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="clear fields", style=discord.ButtonStyle.red, row=4)
    # async def _clear_fields(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="import", style=discord.ButtonStyle.green, row=4)
    # async def _import(self, interaction: Interaction):
    #     """"""

    # @dui.button(label="export", style=discord.ButtonStyle.green, row=4)
    # async def _export(self, interaction: Interaction):
    #     """"""

    async def on_error(self, interaction: Interaction, error, element: dui.Item):
        """"""
        # inform user of any errors within embed sending (most should be user caused)
        print("error")
        logger.error("an error occurred, %s", error)

        if isinstance(error, discord.HTTPException):
            embed = discord.Embed(
                title="An error occurred", 
                color=discord.Color.dark_orange(),
                description=f"```fix\n[ {str(error)} ]```"
            )

            await interaction.followup.send(
                embed=embed, ephemeral=True
            )
            return

        raise error

class Main(app_commands.Group):

    def __init__(self, bot):
        super().__init__(name="embedb")

        self.bot = bot

    @app_commands.command(name="build")
    async def _build(
        self, 
        interaction: Interaction # , 
        # m_id: typing.Optional[str], 
        # index: typing.Optional[int]
    ):
        """
        Sends an embed builder
        """
        # TODO: Allow editing of existing embeds by message-id search

        embed = discord.Embed(title="Embed Builder")
        builder = EmbedBuilderView(embed)

        await interaction.response.send_message(
            embed=embed,
            view=builder,
            ephemeral=True
        )




async def setup(bot):
    bot.tree.add_command(Main(bot))