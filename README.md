
# TODO

1. ~~send the .env file as the environment to the bot container and only load_dotenv when the bot is in test mode~~
2. ~~Figure out how to maintain volumes and enable this for logging~~
3. ~~create a new docker container to work with postgres~~
4. implement command tree error handling and more
5. have pgadmin save server registration
6. ~~create more logging within bot development (on awake, on command use, on interaction use)~~
7. ~~gracefully terminate python bot during `docker-compose down`~~ I think I did?
8. ~~see if there are any network configurations I should make and override default if needed~~
9. ~~see if profiles are useful. maybe they will allow test builds~~

10. finish teams implementation
11. bugtest rolebuttons and refactor + implement database calls
12. review embedbuilder
13. work on schedule.py
14. [postgres log listener ?](https://magicstack.github.io/asyncpg/current/api/index.html#asyncpg.connection.Connection.add_log_listener)
15. update to most recent d.py repo

# Docker Compose

I need to figure out how to use docker compose to enable easy access to a postgresql database. With this the database will be linked with the build and hopefully the data will be able to be transfered easily and with a modular access.

I could do this manually with a makerfile, but the standard process is with docker-compose.

Once this system is in place, beta versions will use sqlite to store persistent data while the production version will use postgresql. 

# Takeaways from 8-14-2022 (docker-compose)

Running postgres from the default image is a valid choice. As long as I understand where the content is stored so I can persist data, I can use it. The important info can be stored within the startup configs. 

Due to the volumes of docker and postgres, I can store mount the postgres data on the main drive and transfer it if need be. I have yet to test this ability however so I hope it works.

Currently though the network is automatically configured which includes the local ip address of the postgres server; I need to figure out how to change this configuration to be customized. It will also be important to learn how to use secret files within docker so sensetive information does not need to be stored in the dockerfile or docker-compose.yml

Another small note to take, pgadmin is its own container. This could be changed with a custom postgres container but there appears to be little reason to convert.

With some custom changes from the original docker-compose.yml found on the webpage [here](https://towardsdatascience.com/how-to-run-postgresql-and-pgadmin-using-docker-3a6a8ae918b5), the hostname is now consistent and the database is configured correctly. The .env file has secure content stored within and can be used by both the compose file and the bot's code.

~~A real quick assumption is that the bot's container will also need to be on the application's network for it to correctly communicate with the postgres server. I will however test this in the future~~ (I forgot this is done naturally through docker compose)

[docker-compose reference](https://docs.docker.com/compose/compose-file/) |
[Dockerfile reference](https://docs.docker.com/engine/reference/builder/)