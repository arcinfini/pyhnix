
import io
import json
import logging
import typing
from collections import namedtuple
from datetime import timedelta

import discord
import discord.ui as dui
import discord.utils as dutils
from discord import Interaction, app_commands

logger = logging.getLogger(__name__)

"""
TODO, FIX BREAKING BUGS
leaving the default null value in the index field of the modal causes a casting
error; check other typing issues
(inspect and decide solution later; possible complex system of conversions)

when selecting a field, the view updates and removes the visual cue of what is
being edited
~~(set default to selected index)~~

prevent field index select from being used while there are no fields to edit 
~~(set to disabled)~~

check: if an embed error occurs, rollback to the previous change 
~~(save embed before change and fix on error)~~

"""

class Form(dui.Modal):
    """
    A default modal to display text inputs to a user.

    Input handling is done externally and this form sends a defer to record a
    response
    """

    def __init__(self, author, /, **items: typing.Dict[str, dui.Item]):
        super().__init__(title="Embed Builder Prompt", timeout=60*15)

        self.__items = items.copy()
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
        await interaction.response.defer(thinking=False)

class EmbedBuilderView(dui.View):
    """
    The view that hosts the buttons and other controls for creating or editing
    an embed.

    Makes use of the default Form modal to build promts
    """

    def __init__(self, author, embed, *, post):
        super().__init__(timeout=60*15)

        self.embed:discord.Embed = embed
        self.previous_embed = None
        self.original_embed = self.__copy_embed()
        self.author = author

        self.__selected_field:int = None 

        self.callback = post

    def __copy_embed(self):
        return discord.Embed.from_dict(self.embed.to_dict())

    def update_field_select(self):
        """
        Called when the fields are are altered and the field selection needs to
        be updated
        """

        # disables the select if no fields are present
        is_selected = len(self.embed.fields) > 0
        self._field_index.disabled = not is_selected

        options=[
            discord.SelectOption(
                label=field.name, 
                description=index,
                value=str(index),
                default=index==self.__selected_field
            )
            for index, field in enumerate(self.embed.fields)
        ]

        # if fields are not present, fill options with one null option
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
        logger.debug("updating embed; with view %s", with_view)

        timeout = f"<t:{int((dutils.utcnow() + timedelta(seconds=self.timeout)).timestamp())}>"

        if not interaction.response.is_done():
            await interaction.response.edit_message(
                content=f"This interaction times out at {timeout}",
                embed=self.embed,
                view=self if with_view else discord.utils.MISSING,
            )
            return

        await interaction.followup.edit_message(
            content=f"This interaction times out at {timeout}",
            embed=self.embed,
            view=self if with_view else discord.utils.MISSING,
            message_id=interaction.message.id
        )

    def rollback(self):
        """
        Resets the embed to the last embed checkpoint
        """

        self.embed = self.previous_embed
        self.previous_embed = None

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

        self.previous_embed = self.__copy_embed()
        self.embed.title = response.title

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

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

        self.previous_embed = self.__copy_embed()
        self.embed.description = response.description

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

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

        self.previous_embed = self.__copy_embed()
        self.embed.color = discord.Color.from_str(response.color)

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

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

        self.previous_embed = self.__copy_embed()
        self.embed.url = response.url

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.button(label="Image", style=discord.ButtonStyle.blurple, row=1)
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

        self.previous_embed = self.__copy_embed()
        self.embed.set_image(url=response.url)

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.button(label="Thumbnail", style=discord.ButtonStyle.blurple, row=1)
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

        self.previous_embed = self.__copy_embed()
        self.embed.set_thumbnail(url=response.url)

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.button(label="Author", style=discord.ButtonStyle.blurple, row=1)
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

        self.previous_embed = self.__copy_embed()
        self.embed.set_author(
            name=response.name,
            url=response.url,
            icon_url=response.icon_url
        )

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.button(label="Footer", style=discord.ButtonStyle.blurple, row=1)
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

        self.previous_embed = self.__copy_embed()
        self.embed.set_footer(
            text=response.text,
            icon_url=response.icon_url
        )

        try: await self.update(interaction)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.select(placeholder="Field Index", options=[discord.SelectOption(label="null")], row=2, disabled=True)
    async def _field_index(self, interaction: Interaction, select: dui.Select):
        """
        Disables the edit and remove field buttons if no item is selected
        """
        
        selected = len(select.values)==0

        self._edit_field.disabled=selected
        self._remove_field.disabled=selected

        self.__selected_field = select.values[0] if selected else None

        self.update_field_select()
        await self.update(interaction, with_view=True)

    @dui.button(label="Create Field", style=discord.ButtonStyle.green, row=3)
    async def _create_field(self, interaction: Interaction, button: dui.Button):
        """
        Allows the user to  create a new field
        """

        response = await self.prompt(
            interaction, button,
            index=self.input("index: enter a positive number",
                default=str(len(self.embed.fields)),
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
                default="0",
                required=True,
                style=discord.TextStyle.short,
                max_length=1,
            )
        )

        self.previous_embed = self.__copy_embed()
        self.embed.insert_field_at(int(response.index if response.index != '' else len(self.embed.fields)), 
            name=response.name, 
            value=response.value, 
            inline=bool(response.inline)
        )
        
        self.update_field_select()
        try: await self.update(interaction, with_view=True)
        except Exception as e: 
            self.rollback()
            raise e

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
                default=str(index),
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
                default=str(int(field.inline)),
                required=True,
                style=discord.TextStyle.short,
                max_length=1
            )
        )

        self.previous_embed = self.__copy_embed()
        new_index = int(response.index if response.index != '' else index)
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

        self.__selected_field=new_index
        self.update_field_select()
        try: await self.update(interaction, with_view=True)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.button(label="Remove Field", style=discord.ButtonStyle.red, row=3, disabled=True)
    async def _remove_field(self, interaction: Interaction, button: dui.Button):
        """
        Removes the selected field
        """

        # TODO: Prompt for confirmation
        # TODO: Remove select option

        index = int(self._field_index.values[0])

        self.previous_embed = self.__copy_embed()
        self.embed.remove_field(index)
        
        self.__selected_field=None
        self.update_field_select()
        try: await self.update(interaction, with_view=True)
        except Exception as e: 
            self.rollback()
            raise e


    @dui.button(label="Clear Fields", style=discord.ButtonStyle.red, row=3)
    async def _clear_fields(self, interaction: Interaction, button: dui.Button):
        """
        Clears all the fields
        """

        # TODO: Prompt for confirmation

        self.previous_embed = self.__copy_embed()
        self.embed.clear_fields()

        self.__selected_field=None
        self.update_field_select()
        try: await self.update(interaction, with_view=True)
        except Exception as e: 
            self.rollback()
            raise e

    @dui.button(label="Restart", style=discord.ButtonStyle.red, row=4)
    async def _restart(self, interaction: Interaction, button: dui.Button):
        """
        """

        # TODO: Prompt for confirmation

        self.embed = discord.Embed.from_dict(self.original_embed.to_dict())

        self.__selected_field=None
        self.update_field_select()
        await self.update(interaction, with_view=True)

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

        self.previous_embed = self.__copy_embed()
        embed = discord.Embed.from_dict(json.loads(response.content))
        self.embed = embed

        self.__selected_field=None
        self.update_field_select()
        try: await self.update(interaction, with_view=True)
        except Exception as e: 
            self.rollback()
            raise e

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

        embed = discord.Embed(title="Embed Builder")
        
        async def callback(build_view):

            await interaction.channel.send(embed=build_view.embed)
        
        
        builder = EmbedBuilderView(interaction.user.id, embed, post=callback)

        timeout = f"<t:{int((dutils.utcnow() + timedelta(seconds=builder.timeout)).timestamp())}>"

        await interaction.response.send_message(
            f"This interaction times out at {timeout}",
            embed=embed,
            view=builder,
            ephemeral=True
        )



async def setup(bot):
    bot.tree.add_command(Main(bot))

    @bot.tree.context_menu(name="embedbedit")
    async def edit(interaction: Interaction, message: discord.Message):
        if message.author.id != interaction.client.user.id:
            raise app_commands.CheckFailure("I do not have permission to edit this message")

        if len(message.embeds) < 1:
            raise app_commands.CheckFailure("There are no embeds to edit")

        embed = message.embeds[0]

        async def callback(build_view):

            await message.edit(embed=build_view.embed)

        builder = EmbedBuilderView(interaction.user.id, embed, post=callback)
        builder.update_field_select()

        await interaction.response.send_message(
            embed=embed,
            view=builder,
            ephemeral=True
        )
