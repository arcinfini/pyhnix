"""
mbuilder.py
-----------

### command structure
#### mbuilder create -> define content | define embed

creates an interface to begin building a message

- content editor is a form
- embed editor is an ephemeral interaction interface

#### mbuilder edit <mbuilder obj> <content/embed/view>

creates an interface to edit the component specified

#### mbuilder remove <mbuilder obj> <content/embed/view>

creates an interface to accept confirmation to remove a particular component of
a message

#### mbuilder delete <mbuilder obj>

creates an interface to accept confirmation to delete the internalized
documentation of the message as well as the associated message in discord

"""


import logging, typing
from collections import namedtuple

from internal.client import Phoenix

import discord
from discord import (
    app_commands, 
    Interaction,

    utils as dutils,
    ui as dui
)

logger = logging.getLogger(__name__)

class Form(dui.Modal):
    """
    A default modal to display text inputs to a user.

    Input handling is done externally and this form sends a defer to record a
    response
    """

    def __init__(self, author, /, **items: typing.Dict[str, dui.Item]):
        super().__init__(title="Form", timeout=60*15)

        self.__items = items.copy()
        self.author = author

        for _, item in items.items():
            self.add_item(item)

    @property
    def items(self):
        items = namedtuple('Items', self.__items.keys())
        return items(*[item.value for item in self.__items.values()])

    async def interaction_check(self, interaction: Interaction) -> bool:
        """
        Checks if the author's id matches that of the original interaction
        invoker
        """
        
        return interaction.user.id == self.author

    async def on_submit(self, interaction: Interaction):
        """
        A default interaction response to inform discord's servers that it has
        been received and is not thinking
        """

        await interaction.response.defer(thinking=False)

class Builder(dui.View):
    """
    The interface that is created on command initialization. This is the center
    of all other edits
    """

    def __init__(self):
        super().__init__(timeout=15*60)

        # The message that is associated with the customizer
        self.message:typing.Optional[discord.Message] = None

        self.__content = None

    @property
    def content(self):
        if self.__content is not None: return self.__content
        elif self.message is not None: return self.message.content

        return None

    @classmethod
    async def from_record(cls, client: Phoenix, record):
        pass

    @dui.button(label="Edit Content", style=discord.ButtonStyle.grey)
    async def _content_editor(
        self, 
        interaction: Interaction, 
        button: dui.Button
    ):
        """
        Begins the process of editing the content of the message
        """

        form = Form(interaction.user.id, content=dui.TextInput(
            label="Content", style=discord.TextStyle.long,
            placeholder="Message content to appear in the message",
            default=self.content,
            required=False, max_length=2000
        ))

        await interaction.response.send_modal(form)

        failed = await form.wait()

        if failed: return

        self.__content = form.items.content

    @dui.button(label="Edit Embed", style=discord.ButtonStyle.grey)
    async def _embed_editor(
        self, 
        interaction: Interaction, 
        button: dui.Button
    ):
        """
        Begins the process of editing the embed attached to the message
        """

    @dui.button(label="Edit View", style=discord.ButtonStyle.grey)
    async def _view_editor(
        self, 
        interaction: Interaction, 
        button: dui.Button
    ):
        """
        Beginds the process of editing the view attached to the message
        """

        await interaction.response.send_message(
            "currently unimplemented",
            ephemeral=True
        )

    @dui.button(label="Preview", style=discord.ButtonStyle.blurple, row=1)
    async def _preview(
        self, 
        interaction: Interaction, 
        button: dui.Button
    ):
        """
        Makes the bot send an ephemeral message to view a preview of what would
        be the updated version of the message
        """

        await interaction.response.send_message(
            "currently unimplemented",
            ephemeral=True
        )

    @dui.button(label="Submit", style=discord.ButtonStyle.green, row=1)
    async def _submit(
        self, 
        interaction: Interaction, 
        button: dui.Button
    ):
        """
        Submits the changes and updates or sends the message
        """

        await interaction.response.send_message(
            "currently unimplemented",
            ephemeral=True
        )

class Main(app_commands.Group):

    def __init__(self, bot: Phoenix):
        super().__init__(name="mbuilder")

        self.bot = bot

    @app_commands.command(name="create")
    async def _create(self, interaction: Interaction):
        """
        Sends an interface to begin the process of building a message. As a
        message needs either one character or an embed, the message can not be
        sent until one is defined.
        """

async def setup(bot: Phoenix):
    await bot.add_cog(Main(bot))