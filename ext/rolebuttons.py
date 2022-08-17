import sqlite3, json # for testing purposes

import typing, logging
from discord import app_commands, Interaction
import discord.utils as dutils
import discord

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
"""

TODO: Consider errors/circumstances when multiple people are attempting to edit the button view at a time

TODO: Inform the user about the max of 25 roles per self assigner

"""

"""

create table if not exists role_buttons (
    message_id bigint,
    channel_id bigint,
    interaction_id bigint,

    roles bigint[]
)

"""

class RoleButton(discord.ui.Button):
    """
    The button that appears on the role button view
    """
    
    # TODO handle role NotFound exception
    # TODO handle not enough bot clearance
    # TODO handle permission denied exception

    def __init__(self, role:discord.Role, custom:str):
        super().__init__(
            style=discord.ButtonStyle.blurple,
            label=role.name,
            custom_id=custom
        )

        self.role_id = role.id
        self.role = role
        # TODO custom id will be {interaction.id-role.id}

    async def callback(self, interaction: Interaction):
        """
        add or remove the role depending on if the user has it
        """

        logger.debug("role button pressed: %s (%d)", self.role.name, self.role.id)
        if self.role in interaction.user.roles:
            logger.debug("removing role: %s (%d)", self.role.name, self.role.id)

            await interaction.user.remove_roles(self.role, reason="role assigner")
            await interaction.response.send_message(
                f"{self.role.name} has been removed from your roles",
                ephemeral=True
            )
        else:
            logger.debug("adding role: %s (%d)", self.role.name, self.role.id)

            await interaction.user.add_roles(self.role, reason="role assigner")
            await interaction.response.send_message(
                f"{self.role.name} has been added to your roles",
                ephemeral=True
            )            

class RoleButtonForm(discord.ui.Modal, title="Role Buttons"):
    """
    A modal sent to the user to control the content of the message for a self
    assigner

    allows a max of 2000 characters
    """
    
    content = discord.ui.TextInput(
        label="Message Content",
        style=discord.TextStyle.paragraph,
        placeholder="Content written in this field will be displayed to everyone",
        required=True,
        max_length=2000,
    )

    def __init__(self, author, /, content:str=None):
        super().__init__(timeout=1200)
        
        self.author = author
        self.content.default = content

    async def on_submit(self, interaction):
        await interaction.response.send_message("your response has been recorded", ephemeral=True)

    async def interaction_check(self, interaction: Interaction):
        return self.author == interaction.user.id

class RoleButtonView(discord.ui.View):
    """
    The view that enables the behavior of the self assigner
    """

    # new() creates a new role button view representation in the database

    # fetch() finds a role button view representation in the database
    # can return None if none is found

    def is_a_button(self, role_id):
        """
        Checks if the role id passed has an active button within the view
        """
        
        for child in self.children:
            if child.role_id == role_id: return True

        return False

    def add_button(self, role:discord.Role, custom:str):
        logger.debug("adding button for role: %s (%d)", role.name, role.id)

        self.add_item(RoleButton(role, custom))

    def remove_button(self, role:discord.Role):
        logger.debug("removing button for role: %s (%d)", role.name, role.id)

        self.remove_item(dutils.get(self.children, role_id=role.id))

    async def interaction_check(self, interaction: Interaction):
        # TODO: check if the user can see the original message
        
        return True

class RoleSelectorView(discord.ui.View):
    """
    Represents the view that allows the user to select roles to add to a self
    assigner

    stores a max of 5 selects with 25 roles each for a total max of 125 roles.
    """

    def __init__(self, o_interaction):
        super().__init__(timeout=600)
        self.o_interaction = o_interaction

        self.selections = []

    def __slice_builder(self, items, length):
        """
        Returns an iterator that splits the contents of the list provided into
        smaller lists of the indicated length
        """

        for i in range(0, len(items), length):
            yield items[i:i + length]

    def build(self, roles: typing.List[discord.Role], /, callback, active_roles=[]):
        """
        Adds selections to the view to allow selecting the roles of the guild

        The roles should be positioned from top to bottom (accurate to the
        discord hierarchy) and can have no more than 4 due to the extra content
        field. This allows up to 100 roles to be supported through this method
        """
        
        for i, items in enumerate(list(self.__slice_builder(roles, 15))):
            if i == 5: break

            select = discord.ui.Select(
                placeholder="Roles selected will be added to the self assigner",
                min_values=0, 
                max_values=len(items),
            )

            for role in items:
                select.add_option(
                    label=role.name, 
                    value=role.id,
                    default=role in active_roles
                )

            select.callback = callback

            self.selections.append(select)
            self.add_item(select)

    async def interaction_check(self, interaction: Interaction):
        logger.debug("checking select interaction")
        
        return interaction.user.id == self.o_interaction.user.id

@app_commands.guild_only()
class Main(app_commands.Group):

    def __init__(self, bot):
        super().__init__(name="reacter")

        self.bot = bot
        logger.info("%s initialized" % __name__)

    @app_commands.command(name="create")
    async def _create(self, interaction: Interaction):
        """
        Creates a new role button interface in this channel
        """
        
        form = RoleButtonForm()
        await interaction.response.send_modal(form)

        result = await form.wait()
        if result: return

        # create message

        view = RoleButtonView(timeout=None)
        message = await interaction.channel.send(form.content, view=view)

        # Insert into postgres
        

    @app_commands.command(name="add")
    async def _add(self, interaction: Interaction, m_id: str, role: typing.Optional[discord.Role]):
        """
        Adds a single role to the self assignable roles
        """
        # First fetch the message with the buttons
        message = await interaction.channel.fetch_message(int(m_id))

        # search the database for the view defined
        # TODO: Change into postgres form
        # TODO: do not allow roles above the top_role of interaction.user
        with sqlite3.connect("test.sqlite") as conn:
            cursor = conn.execute("SELECT roles from role_buttons where message_id=?", (m_id,))
        
            active = [json.loads(i[0]) for i in cursor.fetchall()]
            # if there is no returned value then there is no database entry
            # this entry is invalid
            if active is None or len(active) == 0:
                await interaction.response.send_message(
                    "this is not a valid self assigner",
                    ephemeral=True
                )
                return

        """
        async with pool.acquire() as conn:
            result = await conn.fetch("select * from role_buttons where message_id=$1", m_id)
        
        """

        # Get all the guild roles, sort them and filter by active buttons and
        # roles that the bot can edit
        top_role = interaction.guild.me.top_role

        all_roles = await interaction.guild.fetch_roles()
        all_roles.sort(key=lambda x: x.position)
        
        editable_roles = list(filter(lambda x: x < top_role, all_roles))
        active_roles = list(filter(lambda x: x.id in active, all_roles))
        
        button_view = RoleButtonView()
        selector_view = RoleSelectorView(interaction)

        async def callback(s_interaction: Interaction):
            """
            Callback for the role selector. Is called once the selector is
            exited and the role buttons should be updated
            """
            
            logger.debug("selected changes")

            merged = []
            for selector in selector_view.selections:
                merged += selector.values

            roles = list([dutils.get(editable_roles, id=int(id)) for id in merged])
            roles.sort(key=lambda x: x.position)

            button_view.clear_items()
            for role in roles:
                button_view.add_button(role)

            await message.edit(view=button_view)
            await s_interaction.response.send_message("roles added", ephemeral=True)

            # TODO Update database with new roles

        selector_view.build(editable_roles, active_roles=active_roles, callback=callback)

        await interaction.response.send_message(
            "Selected roles will be self assignable to all who can see",
            view=selector_view,
            ephemeral=True
        )


    @app_commands.command(name="addtest")
    async def add(self, interaction: Interaction, m_id: str):
        """
        Sends a view to edit the role buttons
        """



    @app_commands.command(name="refresh")
    async def _refresh(self, interaction: Interaction, m_id: str):
        """
        Refreshes the current active roles (removes any deleted roles), reorders
        the buttons based on the role hierarchy
        """

        # takes the view
        # iterates over it to find any no longer valid roles (deleted)
        # updates the names and positioning of the buttons

    @app_commands.command(name="edit")
    async def _edit(self, interaction: Interaction, m_id: str):
        """
        Sends a modal to allow editing the text of the message and adding or
        removing multiple roles at a time
        """

        # takes the view and message
        # sends a create modal with the content filled from the message
        # the editor can edit the text inside the message and the roles that can
        # be toggled

async def setup(bot):
    bot.tree.add_command(Main(bot))