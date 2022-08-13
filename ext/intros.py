
from discord.ext import commands
from discord import app_commands, Interaction

import discord

"""
An intro embed consists of multiple components. Most of these components are
automatically defined and maintained. The rest are editable by the owner of
the intro.

bio: user defined
footer: user defined
image: user defined

author: auto generated f"{user.name}#{user.discriminator} | {user.displayname}"
author.icon_url: auto generated f"{user.avatar.url}
title: auto generated f"{user.top_role.name}"
"""

class Intro:
    """

    a database representation of a users intro

    {
        bio_text: str,
        footer_text: str,
        image_url: str,

        owner_id: int,
        role_id: int,

        embed_message_id: int,
    }

    """

    def __init__(self, owner_id, /, bio_text="Write bio here", footer_text="", image_url=""):
        self.bio = bio_text
        self.footer = footer_text
        self.image_url = image_url

        self.owner_id = owner_id

    @classmethod
    def new(cls, owner_id):

        return cls(owner_id)

    @classmethod
    def from_data(cls, data):

        return cls(data.pop("owner_id"), **data)

    @classmethod
    async def fetch(cls, owner_id):
        """fetches the intro from the database"""

        return cls(owner_id)

class Intr:

    """
    Intro is a type of object to be stored in the mongodb
    
    {
        bio: str,
        footer: str,
        url: str,

        owner_id: int,
        role_id: int,

        meta: {
            embed_id: int
        }
    }

    """

    def __init__(self, owner_id, role_id, bio="Write bio here", footer="", url="", meta={}):

        self.bio = bio
        self.footer = footer
        self.url = url

        self.owner_id = owner_id
        self.role_id = role_id

        self.meta = meta

    async def edit(self, bio=None, footer=None, url=None):

        """Edit internal properties and save to database"""

        pass

class Form(discord.ui.Modal, title="Intro Form"):
    """Basic modal for editing the intro"""

    def __init__(self, intro:Intro, interaction: Interaction):
        super().__init__(timeout=600)
        
        self.interaction = interaction
        self.intro = intro

        self.bio = discord.ui.TextInput(
            label="Bio Text", 
            default=intro.bio, 
            style=discord.TextStyle.long, 
            required=True, 
            placeholder="This field is required"
        )
        self.add_item(self.bio)

        self.image = discord.ui.TextInput(
            label="Picture",
            default=intro.image_url,
            style=discord.TextStyle.short,
            required=False,
            placeholder="A url to an image (must begin with http)"
        )
        self.add_item(self.image)

        self.footer = discord.ui.TextInput(
            label="Footer Text", 
            default=intro.footer,
            required=False,
            placeholder="This field can be left empty"
        )
        self.add_item(self.footer)

    async def on_submit(self, interaction):
        """Update the embed and database"""
        user = interaction.user

        # during testing just send the embed as the response
        embed = discord.Embed(
            title=f"{user.top_role.name}",
            description=self.bio.value,
            color=user.color
        )

        embed.set_author(name=f"{user.name}#{user.discriminator} | {user.display_name}")
        
        if self.footer.value is not None and self.footer.value != "":
            embed.set_footer(text=self.footer.value)

        if self.image is not None and self.image.value != "":
            embed.set_image(url=self.image.value)
        
        await interaction.response.send_message(embed=embed)

    async def interaction_check(self, interaction: Interaction):
        """Currently checks for the owner id being accurate"""
        # future should check for role validation as the user will change with time
        
        return self.interaction.user.id == interaction.user.id

    async def on_error(self, interaction: Interaction, error):
        """inform user of failure either for permission or an actual error"""

        pass

class Listener(commands.Cog, name="intro_listener"):
    """Listens for user changes on selected users to update their intro"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        """Update intro embed if user is a subject of an embed"""

class Main(app_commands.Group):
    """Manages intros for exec members"""

    def __init__(self, bot):
        super().__init__(name="intro")
        self.bot = bot

        self.intro_channel_id = 848264106069721108

    @app_commands.command(name="create")
    async def _create(self, interaction: Interaction):
        """Creates a new intro for the user"""

        intro = Intro.new(interaction.user.id)
        
        form = Form(intro, interaction)

        await interaction.response.send_modal(form)

    @app_commands.command(name="edit")
    async def _edit(self, interaction: Interaction):
        """Edits the user's current intro"""

        # validation for the intro requires the user to have a role
        # IE someone with the Treasurer role can edit the treasurer intro
        # the last person to edit the intro is considered the ower of the intro

    @app_commands.command(name="refresh")
    async def _refresh(self, interaction: Interaction):
        """Refreshes all the user's intros from the database"""



async def setup(bot):
    await bot.add_cog(Listener(bot))
    bot.tree.add_command(Main(bot))

