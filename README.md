
# TODO

- [ ] Have a development docker-compose file to run a postgres server with no data retention
- [X] Install pre-commit
- [ ] Build contribution guidelines
- [ ] Define tooling in readme and how to use them.
- [ ] Add approve and deny buttons back to requester. these buttons alert the requester when the decision is made. The embed will have a different color on each status state

# Issues

- [ ] GuildNotFound conversion error not displayed to user in sync command
- [ ] Command errors propogate to the user twice.

#  Current state
database for local testing is functional. you just need to clear the volume when testing sql scripts as i dont have a method for upgrading an existing database. 

taems.py is also incomplete

once these two things are done and tested, i can work on documentation and other bug fixes