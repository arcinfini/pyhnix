
# TODO

1. schedule.py

# Workflow

The current workflow consists of separate branches based on the current version specification. The default branches are `main` and `dev`. The branch `main` is the branch where production code is released to. The server pulls from `main` on server startup. `dev` is used for development testing before being released to production. When working on separate versions, the naming scheme of `dev@X.X.X` is used. Most minor bug fixes and changes are updated on 0.0.X versions while new features are put on 0.X.0 versions.

# How to use

A makefile is included to deploy the bot to a production environment. The general dependencies to make this application are docker, make and python 3.8 or higher. `systemctl` is used to control the state of the docker compose.

For the build to work correctly, it must be stored in `/root/pyhnix`.

# How to develop

The makefile includes a venv option that easily creates a venv and installs pip requirements.

# Version release 1.0.0 

##### ext

- rolebuttons: allows the creation of views that give roles on an interaction with the button
- embedbuilder: allows creation and editing of embeds for display
- teams: enables the coordination of teams and allows those without the manage role permissions to add members to their team

##### dev

- evaluator: enables miniture environments for executing code with the default dependencies. These views are persistent
- terminal: certain dev commands for managing the bot

##### internal

- client: an extension of the default bot class to extend functionality
- tree: an extension of the default tree class to enable application command error handling and command logging
- a small number of util files and functions

# Version release 1.0.1

- teams front facing command documentation and ephemeral messages
- further error handling within the tree class
- implement a makefile to quickly install and build the application
- fixed rolebutton interface selection not appearing in positional order
- fixed embedbuilder edit field not correctly filling in the inline parameter
- fixed rolebutton reset error on no updated selection
