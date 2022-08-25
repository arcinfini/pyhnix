
import typing, logging
from discord.ext import commands
from discord import app_commands, Interaction
import discord.ui as dui
import discord

from internal.client import Phoenix
from internal import utils, app_errors

logger = logging.getLogger(__name__)

_interfaces = []

"""
roleb create
roleb edit
roleb manage

TODO: deletion, name editing
TODO: no updates causes all buttons to disappear !!!!!

"""

"""role_button_interfaces
guildid bigint
name text

messageid bigint # the id of the message
channelid bigint # the id of the channel

customfmt text # a python str meant to have format called on to create the custom id for a button

roles bigint[]

"""

class RoleButtonForm(dui.Modal):
    """
    The form sent to users for inputing name and content on creation and edit
    editing the name is currently not supported
    """
    
    __content = dui.TextInput(
        label="Text Content", 
        style=discord.TextStyle.long,
        required=True,
        max_length=2000
    )
    __name = dui.TextInput(
        label="Name Identifier", 
        placeholder="CAN NOT BE EDITED",
        style=discord.TextStyle.short,
        required=True,
        max_length=50
    )

    def __init__(self, author: int, *, name:str=None, content:str=None):
        super().__init__(title="Role Button Form", timeout=15*60)

        self.author = author

        self.__content.default = content
        self.__name.default = name

    @property
    def content(self):
        return self.__content.value

    @property
    def name(self):
        return self.__name.value


    async def interaction_check(self, interaction: Interaction):
        return interaction.user.id == self.author

    async def on_submit(self, interaction: Interaction):
        await interaction.response.defer(thinking=False)


class RoleButton(dui.Button):
    """
    The button that listens for interactions to assign roles
    """

    def __init__(self, role:discord.Role, *, custom_fmt:str):
        super().__init__(
            style=discord.ButtonStyle.blurple, 
            label=role.name,
            custom_id=custom_fmt % role.id
        )
        logger.info(custom_fmt, role.id)

        self.custom_fmt = custom_fmt
        self.role = role

    async def callback(self, interaction: Interaction):

        if self.role.id in [r.id for r in interaction.user.roles]:

            await interaction.user.remove_roles(
                self.role, 
                reason="self assigned role"
            )

        else:

            await interaction.user.add_roles(
                self.role, 
                reason="self assigned role"
            )
        
        await interaction.response.send_message(
            f"{interaction.user.mention}, your roles have been updated",
            ephemeral=True
        )


class RoleButtonInterface(dui.View):
    """
    Hosts the buttons that assign a role on interaction. Can hold up to 25
    buttons
    """

    def __init__(
        self, 
        client: Phoenix,
        *,
        name:str,
        guild:discord.Guild,
        message:discord.Message,
        custom_fmt:str,
        roles:typing.List[discord.Role]=[]
    ):
        super().__init__(timeout=None)

        self.__bot = client

        self.name = name
        self.guild = guild

        self.message = message
        self.roles = []
        self.custom_fmt = custom_fmt

        for role in roles:
            self.add_button(role)

    @classmethod
    async def from_record(cls, client:Phoenix, *, record):
        """
        Creates a RoleButtonInterface from the given record
        """

        channel = await utils.get_or_fetch_channel(client, record['channelid'])

        if channel is None:
            return None

        message = await utils.get_or_fetch_message(channel, record['messageid'])

        if message is None:
            return None

        guild = await client.fetch_guild(channel.guild.id)
        roles = await guild.fetch_roles()
        active = list(filter(lambda x: x.id in record['roles'], roles))
        active.sort(key=lambda x: x.position, reverse=True)

        return cls(
            client,
            name=record['name'],
            guild=channel.guild,
            message=message, 
            roles=active, 
            custom_fmt=record['customfmt']
        )

    def add_button(self, role: discord.Role):
        # TODO: Find a way to control insertion position
        self.roles.append(role)
        self.add_item(RoleButton(role, custom_fmt=self.custom_fmt))

    def clear_items(self):
        super().clear_items()

        self.roles.clear()
        return self

    def sort_buttons(self):
        """
        Sorts the view buttons in order of decreasing position
        """

        buttons = self.children
        buttons.sort(key=lambda x: x.role.position, reverse=True)

        self.clear_items()

        for button in buttons:
            self.add_item(button)

    async def send(self):
        """
        Sends the updated view to the stored message
        """
        await self.update()
        await self.message.edit(view=self)

    async def save(self):
        """
        Saves the view to the database

        Throws asyncpg UniqueViolationError if an interface with the same
        identifier exists. Therefore this method is not used to update instances
        of an interface
        """
        
        logger.debug("initial save of %s interface in %d", self.name, self.guild.id)

        async with self.__bot.database.acquire() as conn:
            await conn.execute(
            """
            INSERT INTO role_button_interfaces
            (name, guildid, messageid, channelid, customfmt, roles)
            VALUES ($1, $2, $3, $4, $5, $6)
            """, 
            self.name, 
            self.guild.id, 
            self.message.id, 
            self.message.channel.id, 
            self.custom_fmt, 
            [r.id for r in self.roles]
        )

    async def update(self):
        """
        Updates the internally stored roles in the view to be recaptured on cog
        load
        """

        logger.debug("update of %s interface in %d", self.name, self.guild.id)

        async with self.__bot.database.acquire() as conn:
            await conn.execute("""
            UPDATE role_button_interfaces SET
            roles=$1
            WHERE name=$2 and guildid=$3
            """, [r.id for r in self.roles], self.name, self.guild.id)


class RoleSelectView(dui.View):
    """
    Hosts the roles that can be managed by the bot to be added to the role
    button view
    
    """

    def __init__(self, author:int, role_buttons: RoleButtonInterface, *, roles: typing.List[discord.Role]=[]):
        super().__init__(timeout=60*15)

        self.author = author

        self.__submitted = False
        self.__role_buttons = role_buttons
        self.__selections = []
        self.__editable_roles = roles
        self.__build(roles)

    def __slice_builder(self, items, length):
        """
        Returns an iterator that splits the contents of the list provided into
        smaller lists of the indicated length
        """

        for i in range(0, len(items), length):
            yield items[i:i + length]

    async def interaction_check(self, interaction: Interaction):
        return interaction.user.id == self.author

    async def __select_callback(self, interaction):
        """
        Handles individual interactions
        """

        if self.__submitted:
            await interaction.response.send_message(
                "this view has already been submited",
                ephemeral=True
            )

        await interaction.response.defer(thinking=False)

    def __build(self, roles:typing.List[discord.Role]):
        """
        Adds selections to the view to allow selecting the roles of the guild

        The roles should be positioned from top to bottom (accurate to the
        discord hierarchy) and can have no more than 4 due to the extra content
        field. This allows up to 15*4 roles to be supported through this method
        """
        _roles = roles.copy()
        _roles.sort(key=lambda x: x.position, reverse=True)
        
        for i, items in enumerate(list(self.__slice_builder(_roles, 15))):
            if i == 4: break

            select = discord.ui.Select(
                placeholder="Roles selected will be added to the self assigner",
                min_values=0, 
                max_values=len(items)
            )

            for role in items:
                select.add_option(
                    label=role.name, 
                    value=str(role.id),
                    default=role in self.__role_buttons.roles
                )
                select._values = [o.name for o in select.options]

            select.callback = self.__select_callback

            self.__selections.append(select)
            self.add_item(select)

    @dui.button(label="Submit", style=discord.ButtonStyle.green)
    async def _submit(self, interaction: Interaction, button: dui.Button):
        """
        Submits the select changes and disables the view.
        """

        self.__submitted = True

        await interaction.response.edit_message(
            content="submission recorded", 
            view=None
        )

        merged = []
        for selector in self.__selections:
            merged += selector.values
            logger.debug("selected role buttons: %s", selector.values)

        roles = list([discord.utils.get(self.__editable_roles, id=int(id)) for id in merged])
        roles = list(filter(lambda x: x is not None, roles))
        roles.sort(key=lambda x: x.position, reverse=True)

        self.__role_buttons.clear_items()
        for role in roles:
            self.__role_buttons.add_button(role)

        await self.__role_buttons.send()
        logger.debug("is persistent: %s", str(self.__role_buttons.is_persistent()))


class RoleInterfaceTransformer(app_commands.Transformer):

    async def transform(self, interaction: Interaction, value: str):
        """
        Transforms the value provided into an interface instance stored in the
        _interfaces list
        """

        result = discord.utils.get(
            _interfaces, 
            name=value, 
            guild__id=interaction.guild.id
        )

        if result is None:
            raise app_errors.TransformationError(
                f'{value} is not a valid role button interface'
                )

        return result

    async def autocomplete(self, interaction: Interaction, value: str):
        """
        Returns the list of role button interfaces within the guild that match
        the value
        """

        _filter = lambda x: x.guild.id == interaction.guild.id and value in x.name
        interfaces = filter(_filter, _interfaces)

        return [app_commands.Choice(name=i.name, value=i.name) for i in interfaces]

@app_commands.default_permissions(manage_roles=True)
class RoleButtonsCommand(app_commands.Group):

    def __init__(self, bot, cog):
        super().__init__(name="roleb")

        self.bot = bot
        self.cog = cog
        

    @app_commands.command(name="create")
    async def _create(
        self, 
        interaction: Interaction
    ):
        """
        Sends a modal form to retrieve the text content of the message that has
        the role buttons
        """

        form = RoleButtonForm(interaction.user.id)
        await interaction.response.send_modal(form)

        failed = await form.wait()

        if failed: return
        
        message = await interaction.channel.send(form.content)

        # Creates a new rolebutton interface
        role_buttons = RoleButtonInterface(
            interaction.client,
            name=form.name,
            guild=interaction.guild,
            message=message,
            custom_fmt=f"{interaction.id}-%d"
        )
        await role_buttons.save() # raises a postgres conflict error if one with name at guild already exists
        # TODO: handle unique errors and inform user

        # now that unique errors are out of the way
        _interfaces.append(role_buttons)

        # Begin sending the role selection
        top_role = interaction.guild.me.top_role
        roles = await interaction.guild.fetch_roles()
        editable_roles = list(filter(lambda x: x < top_role, roles))
        
        role_select = RoleSelectView(interaction.user.id, role_buttons, roles=editable_roles)

        await interaction.followup.send(
            "Select the roles to add to the list",
            ephemeral=True, view=role_select
        )

    @app_commands.command(name="manage")
    async def _manage(
        self, 
        interaction: Interaction,
        interface: RoleInterfaceTransformer
    ):
        """
        Sends a view that allows the selection of roles to be changed
        """

        # Begin sending the role selection
        top_role = interaction.guild.me.top_role
        roles = await interaction.guild.fetch_roles()
        editable_roles = list(filter(lambda x: x < top_role, roles))
        
        role_select = RoleSelectView(interaction.user.id, interface, roles=editable_roles)

        await interaction.response.send_message(
            "Select the roles to add to the list",
            ephemeral=True, view=role_select
        )

    @app_commands.command(name="refresh")
    async def _refresh(
        self, 
        interaction: Interaction, 
        interface: RoleInterfaceTransformer
    ):
        """
        Refreshes the view to reorder or rename buttons
        """

        interface.sort_buttons()
        await interface.send()

        await interaction.response.send_message(
            "Interface refreshed", 
            ephemeral=True
        )

    @app_commands.command(name="edit")
    async def _edit(
        self, 
        interaction: Interaction,
        interface: RoleInterfaceTransformer
    ):
        """
        Retrieves a message with the role buttons and sends a modal to edit the
        text content
        """

        form = RoleButtonForm(
            interaction.user.id, 
            name=interface.name,
            content=interface.message.content
        )

        await interaction.response.send_modal(form)

        failed = await form.wait()
        if failed: return

        await interface.message.edit(content=form.content)

# If problems arise with views disabling, add a task to check the view consistency
class Main(commands.Cog):
    """
    A cog tasked with loading and maintaining the different role button
    interfaces used throughout the bot's servers.
    """

    def __init__(self, bot):

        self.bot: Phoenix = bot
        self.role_button_command = RoleButtonsCommand(bot, self)

        bot.tree.add_command(self.role_button_command)

    async def cog_load(self):
        logger.debug("reading database to enable role button interfaces")

        async with self.bot.database.acquire() as conn:
            records = await conn.fetch("""
            select * from role_button_interfaces
            """)

        logger.debug("loading role button interfaces")

        # This should never be the case but just in that off chance
        for interface in _interfaces:
            interface.stop()
        
        _interfaces.clear()
        to_remove = []

        for record in records:
            view = await RoleButtonInterface.from_record(self.bot, record=record)
            if view is None:
                to_remove.append(record)
                continue

            # logger.debug("adding view to dispatch: %s", {**record})
            self.bot.add_view(view)
            _interfaces.append(view)

        logger.info("role button interfaces loaded")

        if (length := len(to_remove)) > 0:
            logger.info("removing %d unresolved role button interfaces", length)

            async with self.bot.database.acquire() as conn:
                await conn.executemany(
                    """
                    DELETE FROM role_button_interfaces
                    WHERE name=$1 and guildid=$2
                    """, 
                    [(record['name'], record['guildid']) for record in to_remove]
                )

    
async def setup(bot):
    await bot.add_cog(Main(bot))

    logger.info("%s initialized", __name__)
