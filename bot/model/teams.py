class Team:
    """"""

    def __init__(self):
        pass

    @property
    def name(self) -> None:
        pass

    @property
    def member_role(self) -> TeamRole:
        pass

    def describe(self) -> str:
        pass

    async def fetch_members(self) -> List[TeamMember]:
        pass

    async def add_member(self, member: discord.Member) -> None:
        pass


class TeamMember:
    def __init__(self, team: Team):
        pass

    async def resolve(self) -> discord.User | discord.Member:
        pass


class TeamRole:
    def __init__(self, team: Team):
        pass

    async def resolve(self) -> discord.Role:
        pass


async def fetch_teams(guild: discord.Guild) -> List[Team]:
    """Fetch all teams of a guild."""


async def fetch_team() -> Team:
    """Fetch a team."""


async def edit_team(team: Team) -> Team:
    """Edit a team."""
