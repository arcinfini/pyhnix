
# TODO

1. schedule.py

# Workflow

The current workflow consists of separate branches based on the current version specification. The default branches are `main` and `dev`. The branch `main` is the branch where production code is released to. The server pulls from `main` on server startup. `dev` is used for development testing before being released to production. When working on separate versions, the naming scheme of `dev@X.X.X` is used. Most minor bug fixes and changes are updated on 0.0.X versions while new features are put on 0.X.0 versions.

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