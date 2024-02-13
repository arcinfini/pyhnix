
# TODO

- [ ] Have a development docker-compose file to run a postgres server with no data retention
- [X] Install pre-commit
- [ ] Build contribution guidelines
- [ ] Define tooling in readme and how to use them.
- [ ] [Refactor bot/ext/teams.py](#Teams Refactor)

# Issues

- [ ] GuildNotFound conversion error not displayed to user in sync command
- [ ] Command errors propogate to the user twice.

# Teams Refactor

Commands

info commands:
team info - returns info on a team
team list - returns a list of teams and their info
team members - returns a list of members on the team

team manage create - create a team with information
team manage edit - edit values of a team
team manage delete - deletes an entire team (should handle removing the role as well)

team members add - adds a single member to the team
team members remove - removes a single member from the team
team members edit - allows the removal or addition of multiple members
team members clean - removes all members from a team