# Configuring Discord bot
The Discord bot is needed to create accounts with which players will connect to your server. There is no other system for creating accounts (e.g. emails) yet, but maybe that will change in the future. :)

## Creating a bot
Creating your own Discord bot is simple. Follow these steps **(the steps might be slightly different for future versions of DDP!)**:
1. Go to [Discord Developer Portal](https://discord.com/developers/applications).
2. Click on "New Application".
3. Enter your bot's name and click "Create".
4. In the "Bot" section, check all intents (Presence Intent, Server Members Intent and so on).

## Inviting your bot
The Discord bot is created, now we need to get it into your Discord server. It's assumed that you already have a Discord server created.

Follow these steps:
1. In DDP, go to "Installation" and make sure "User Install" is turned **off** and "Guild Install" is turned **on**.
2. In "Default Install Settings", add "bot" to scopes in "Guild Install". A "Permissions" menu should appear.
3. You can add "Administrator" permission to the menu, just to make sure the bot will be accessible.
4. Now you can invite your bot by visiting the installation link, choosing your server and clicking "Authorize".

And one last thing:
1. In the "Installation" tab, set "Install Link" to none.
2. **In the "Bot" section, uncheck "Public Bot". Your bot should be private!**

And now you should have your bot in your server!

# Programming the server
**If you can't program in Python, you don't have to continue reading this documentation! Your server is ready!**

If you want to customize your server and Discord bot even more, you can write your own scripts. The script that starts the server is `server.py`. This server script was made to be edited by the server programmer. An example script can be found in the [Quick example](#quick-example) subsection.

## Server architecture
The server stores certain data in certain places. Here is the documented server architecture:
- `config/` - Here you can find all server configuration files.
- `custom/` - Here you can store all your custom scripts and files. This folder will never be edited by any update.
- `db_config/` - Here you can find scripts for creating a database. SQLite database is created automatically.
- `docs/` - Here you can find all documentation files.
- `examples/` - Here you can find examples for certain files.
- `logs/` - Here you can find server logs. There is usually information or errors here.
- `onlineclicker/` - Here you can find all OnlineClicker scripts required to run the server. Hovewer, the main script `server.py` is right in the root folder of your server.
- `.github` - GitHub settings. Not important for you.
- `CHANGELOG` - This file lists everything that your server version has brought.
- `LICENSE` - Project license.
- `README.md` - The README file you can see on GitHub.
- `requirements.txt` - This file lists all Python libraries the server needs to run.
- `server.example.py` - This is an example file of `server.py`. You must rename all files that has `.example` in their name!
- `start.bat` - This file runs the server on Windows.
- `start.sh` - This file runs the server on Linux.
- `start_docs.bat` - This file creates a documentation website on localhost on Windows.
- `start_docs.sh` - This file creates a documentation website on localhost on Linux.
- `update_server_git.bat` - This file updates your server with the latest version on Windows.
- `update_server_git.sh` - This file updates your server with the latest version on Linux.
- `.gitignore` - This file lists all the places in the project that shouldn't be uploaded on GitHub. This isn't important to you.

## Quick example
```py
# server.py
from onlineclicker.onlineclicker import *

# Creates a server object
server = Server()
# Makes a chatbot (you need to specify chatbot name in config.ini!)
chatbot = server.create_chatbot(badges=[Badge.VERIFIED], nickname_color=NicknameColor.ORANGE)

# Makes a bot that sends "pong!" when someone sends "/ping".
@server.event
async def on_player_chat(player: Player, message: Message):
    if message.content == "/ping":
        await chatbot.send_message(player.node, "pong!")

# You can also program your Discord bot here by using the "bot" variable from "onlineclicker/bot.py"
# The Discord bot is made with Pycord (https://pycord.dev/)
@bot.listen()
async def on_ready():
    print("Discord bot is ready!")

# Starts the server and Discord bot
server.initialize(discord_bot=True)
```

You can find more examples like this in the `examples/` folder!

