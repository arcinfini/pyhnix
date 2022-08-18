
from dataclasses import fields
import json, io

from collections import namedtuple
import typing, logging
from discord import app_commands, Interaction
import discord, discord.ui as dui

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO, FIX BREAKING BUGS

"""
embedb build [,m_id[, index]]
embedb edit m_id

enables the building and editing of all embeds sent by the bot.
"""

class Form(dui.Modal):
    """
    A default modal to display text inputs to a user.

    Input handling is done externally and this form sends a defer to record a
    response
    """

    def __init__(self, author, /, **items: typing.Dict[str, dui.Item]):
        super().__init__(title="Embed Builder Prompt", timeout=60*15)

        self.__items = items
        self.author = author

        for _, item in items.items():
            self.add_item(item)

    @property
    def items(self):
        items = namedtuple('Items', self.__items.keys())
        return items(*[item.value for item in self.__items.values()])

    async def interaction_check(self, interaction: Interaction):
        return interaction.user.id==self.author

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer()

    async def on_error(self, interaction:Interaction, error):
        """"""
        raise error

class EmbedBuilderView(dui.View):
    """
    The view that hosts the buttons and other controls for creating or editing
    an embed.

    Makes use of the default Form modal to build promts
    """

    def __init__(self, author, embed, *, post=None):
        super().__init__(timeout=60*15)

        self.embed:discord.Embed = embed
        self.original_embed = discord.Embed.from_dict(embed.to_dict())
        self.author = author

        self.callback = post

    def update_field_select(self):
        """
        Called when the fields are are altered and the field selection needs to
        be updated
        """

        options=[
            discord.SelectOption(
                label=field.name, 
                description=index,
                value=index
            )
            for index, field in enumerate(self.embed.fields)
        ]
        if len(options) == 0:
            options.append(discord.SelectOption(
                label="Null"
            ))

        self._field_index.options = options


    def input(self, label, **kwargs):
        """
        Defines a TextInput with standardized properties and behavior
        """
        required = kwargs.pop('required', False)

        content_in = dui.TextInput(
            label=f"{label.title()}{' (OPTIONAL)' if not required else ''}",
            required=required,
            **kwargs
        )

        return content_in


    async def prompt(self, interaction: Interaction, button: dui.Button, **kwargs):
        """
        Prompts the user to input content based on the interaction
        """
        
        form = Form(interaction.user.id, **kwargs)

        await interaction.response.send_modal(form)
        failed = await form.wait()

        return form.items

    async def update(self, interaction: Interaction, /, with_view=False):
        """
        Refreshes the embed in the original interaction with the current embed
        stored within the view classes
        """

        if not interaction.response.is_done():
            await interaction.response.edit_message(
                embed=self.embed,
                view=self if with_view else discord.utils.MISSING,
            )
            return

        await interaction.followup.edit_message(
            embed=self.embed,
            view=self if with_view else discord.utils.MISSING,
            message_id=interaction.message.id
        )

    async def interaction_check(self, interaction: Interaction):
        return interaction.user.id == self.author

    async def on_error(self, interaction: Interaction, error, element: dui.Item):
        """
        inform user of any errors within embed sending (most should be user caused)
        """
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

    @dui.button(label="Title", style=discord.ButtonStyle.blurple, row=0)
    async def _title(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input title text
        """

        response = await self.prompt(
            interaction, button, 
            title=self.input(button.label,
                default=self.embed.title, 
                style=discord.TextStyle.short
            )
        )

        self.embed.title = response.title

        await self.update(interaction)

    @dui.button(label="Description", style=discord.ButtonStyle.blurple, row=0)
    async def _description(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input description text
        """

        response = await self.prompt(
            interaction, button, 
            description=self.input(button.label,
                default=self.embed.description, 
                style=discord.TextStyle.long,
                max_length=2000
            )
        )

        self.embed.description = response.description

        await self.update(interaction)

    @dui.button(label="Color", style=discord.ButtonStyle.blurple, row=0)
    async def _color(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input color
        """

        # TODO: Inform user of color formatting

        response = await self.prompt(
            interaction, button, 
            color=self.input(button.label,
                default=str(self.embed.color), 
                style=discord.TextStyle.short,
                required=True
            )
        )

        self.embed.color = discord.Color.from_str(response.color)

        await self.update(interaction)

    @dui.button(label="Url", style=discord.ButtonStyle.blurple, row=0)
    async def _url(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to input a url
        """

        # TODO: Inform user of url formatting

        response = await self.prompt(
            interaction, button, 
            url=self.input(button.label,
                default=self.embed.url,
                style=discord.TextStyle.short
            )
        )

        self.embed.url = response.url

        await self.update(interaction)

    # TODO: Implement
    # @dui.button(label="timestamp", style=discord.ButtonStyle.blurple, row=0)
    # async def _timestamp(self, interaction: Interaction):
    #     """
    #     Sends a modal to input a timestamp
    #     """

    @dui.button(label="image", style=discord.ButtonStyle.blurple, row=1)
    async def _image(self, interaction: Interaction, button: dui.Button):
        """
        Sends a modal to accept input for an image
        """

        response = await self.prompt(
            interaction, button, 
            url=self.input(button.label,
                default=self.embed.image.url,
                style=discord.TextStyle.short
            )
        )

        self.embed.set_image(url=response.url)

        await self.update(interaction)

    @dui.button(label="thumbnail", style=discord.ButtonStyle.blurple, row=1)
    async def _thumbnail(self, interaction: Interaction, button: dui.Button):
        """
        """

        response = await self.prompt(
            interaction, button, 
            url=self.input(button.label,
                default=self.embed.thumbnail.url,
                style=discord.TextStyle.short
            )
        )

        self.embed.set_thumbnail(url=response.url)

        await self.update(interaction)

    @dui.button(label="author", style=discord.ButtonStyle.blurple, row=1)
    async def _author(self, interaction: Interaction, button: dui.Button):
        """
        """

        response = await self.prompt(
            interaction, button, 
            name=self.input("name",
                default=self.embed.author.name,
                style=discord.TextStyle.short,
                max_length=256
            ),
            url=self.input("url",
                default=self.embed.author.url,
                style=discord.TextStyle.short
            ),
            icon_url=self.input("icon url", 
                default=self.embed.author.icon_url,
                style=discord.TextStyle.short
            )
        )

        self.embed.set_author(
            name=response.name,
            url=response.url,
            icon_url=response.icon_url
        )

        await self.update(interaction)

    @dui.button(label="footer", style=discord.ButtonStyle.blurple, row=1)
    async def _footer(self, interaction: Interaction, button: dui.Button):
        """
        """

        response = await self.prompt(
            interaction, button, 
            text=self.input("text",
                default=self.embed.footer.text,
                style=discord.TextStyle.long,
                max_length=2048
            ),
            icon_url=self.input("icon url", 
                default=self.embed.footer.icon_url,
                style=discord.TextStyle.short
            )
        )

        self.embed.set_footer(
            text=response.text,
            icon_url=response.icon_url
        )

        await self.update(interaction)

    @dui.select(placeholder="Field Index", options=[discord.SelectOption(label="null")], row=2, min_values=0, max_values=1)
    async def _field_index(self, interaction: Interaction, select: dui.Select):
        """
        Disables the edit and remove field buttons if no item is selected
        """

        # TODO: if item is selected then resend list with it selected
        # send it not selected if not
        # TODO: CHeck if null field is selected, do nothing if so
        
        selected = len(select.values)==0

        self._edit_field.disabled=selected
        self._remove_field.disabled=selected

        await self.update(interaction, with_view=True)

    @dui.button(label="Create Field", style=discord.ButtonStyle.green, row=3)
    async def _create_field(self, interaction: Interaction, button: dui.Button):
        """
        Allows the user to  create a new field
        """

        response = await self.prompt(
            interaction, button,
            index=self.input("index: enter a positive number",
                default=len(self.embed.fields),
                style=discord.TextStyle.short,
                max_length=2,
            ),
            name=self.input("name",
                required=True,
                style=discord.TextStyle.short,
                max_length=256
            ),
            value=self.input("value",
                required=True,
                style=discord.TextStyle.long,
                max_length=1024
            ),
            inline=self.input("inline: 0 for false and 1 for true",
                default=int(False),
                required=True,
                style=discord.TextStyle.short,
                max_length=1
            )
        )

        self.embed.insert_field_at(int(response.index if response.index != '' else None), 
            name=response.name, 
            value=response.value, 
            inline=bool(response.inline)
        )
        
        self.update_field_select()
        await self.update(interaction, with_view=True)

    @dui.button(label="Edit Field", style=discord.ButtonStyle.blurple, row=3, disabled=True)
    async def _edit_field(self, interaction: Interaction, button: dui.Button):
        """
        Captures the current field to be edited
        """

        index = int(self._field_index.values[0])

        field = self.embed.fields[index]

        response = await self.prompt(
            interaction, button,
            index=self.input("index: enter a positive number",
                default=index,
                style=discord.TextStyle.short,
                max_length=2,
            ),
            name=self.input("name",
                default=field.name,
                required=True,
                style=discord.TextStyle.short,
                max_length=256
            ),
            value=self.input("value",
                default=field.value,
                required=True,
                style=discord.TextStyle.long,
                max_length=1024
            ),
            inline=self.input("inline: 0 for false and 1 for true",
                default=int(field.inline),
                required=True,
                style=discord.TextStyle.short,
                max_length=1
            )
        )

        new_index = int(response.index if response.index != '' else None)
        if new_index != index:
            # TODO: Fix the logic behind this. It doesn't always work as planned when moving a field forward
            self.embed.insert_field_at(new_index, 
                name=response.name,
                value=response.value,
                inline=response.inline
            )
            self.embed.remove_field(index)

            self.update_field_select()
        else:
            self.embed.set_field_at(new_index, 
                name=response.name,
                value=response.value,
                inline=response.inline
            )

        await self.update(interaction, with_view=new_index!=index)

    @dui.button(label="Remove Field", style=discord.ButtonStyle.red, row=3, disabled=True)
    async def _remove_field(self, interaction: Interaction, button: dui.Button):
        """
        Removes the selected field
        """

        # TODO: Prompt for confirmation
        # TODO: Remove select option

        index = int(self._field_index.values[0])

        self.embed.remove_field(index)
        
        self.update_field_select()
        await self.update(interaction, with_view=True)


    @dui.button(label="Clear Fields", style=discord.ButtonStyle.red, row=3)
    async def _clear_fields(self, interaction: Interaction, button: dui.Button):
        """
        Clears all the fields
        """

        # TODO: Prompt for confirmation

        self.embed.clear_fields()

        self.update_field_select()
        await self.update(interaction, with_view=True)

    @dui.button(label="Restart", style=discord.ButtonStyle.red, row=4)
    async def _restart(self, interaction: Interaction, button: dui.Button):
        """
        """

        # TODO: Prompt for confirmation

        self.embed = discord.Embed.from_dict(self.original_embed.to_dict())

        await self.update(interaction)

    @dui.button(label="import", style=discord.ButtonStyle.green, row=4)
    async def _import(self, interaction: Interaction, button: dui.Button):
        """
        Imports the provided text as an embed to overwrite the current state
        """

        response = await self.prompt(
            interaction, button,
            content=self.input("embed json",
                required=True,
                style=discord.TextStyle.long
            )
        )

        embed = discord.Embed.from_dict(json.loads(response.content))
        self.embed = embed

        await self.update(interaction)

    @dui.button(label="export", style=discord.ButtonStyle.green, row=4)
    async def _export(self, interaction: Interaction, button: dui.Button):
        """
        Exports the current state of the embed and sends its json representation
        as a file to the user.
        """

        string = io.BytesIO(bytes(json.dumps(self.embed.to_dict(), indent=4), encoding="utf-8"))

        file = discord.File(string, filename="export.json")

        await interaction.response.send_message(file=file, ephemeral=True)

    @dui.button(label="Post", style=discord.ButtonStyle.green, row=4)
    async def _post(self, interaction: Interaction, button: dui.Button):
        """
        Posts the embed either as a new message or updated embed in an existing
        message
        """

        await self.callback(self)
        await interaction.response.defer()

class Main(app_commands.Group):

    def __init__(self, bot):
        super().__init__(name="embedb")

        self.bot = bot

        logger.info("%s initialized" % __name__)

    @app_commands.command(name="build")
    async def _build(
        self, 
        interaction: Interaction
    ):
        """
        Sends an embed builder
        """
        # TODO: Allow editing of existing embeds by message-id search

        embed = discord.Embed(title="Embed Builder")
        
        async def callback(build_view):

            await interaction.channel.send(embed=build_view.embed)
        
        
        builder = EmbedBuilderView(interaction.user.id, embed, post=callback)

        await interaction.response.send_message(
            embed=embed,
            view=builder,
            ephemeral=True
        )

    # TODO: Allow editing an embed in an existing message



async def setup(bot):
    bot.tree.add_command(Main(bot))