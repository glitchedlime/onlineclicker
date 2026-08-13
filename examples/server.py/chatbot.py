# This example file shows how to use ChatBot class.
# Everything important is in the documentation! :)

# To make your own chatbot, do these steps:
# 1. Open config.ini and search up for CHATBOT_USERNAMES. This variable is a list, which means that you can have multiple chatbots!
# 2. If you want to have only one chatbot, edit it like this: CHATBOT_USERNAMES=<bot username>
#    If you want more chatbots, edit it like this: CHATBOT_USERNAMES=<bot username>, <bot_username>, ...
# 3. Use Server.create_chatbot() (see below)
# Just to reassure you: the ChatBot class is NOT intended to be created by you!

# Import the OnlineClicker server library
from onlineclicker.onlineclicker import *

# Create a server
server = Server()

# Make chatbots.
# (let's say our CHATBOT_USERNAMES variable looks like this: CHATBOT_USERNAMES=GrandmaBot, CookieBot)
grandmabot = server.create_chatbot(badges=[Badge.VERIFIED], nickname_color=NicknameColor.BLUE) # GrandmaBot
cookiebot = server.create_chatbot(username_index=1) # CookieBot

# When a player sends a message, the server checks whether it has "/ping" in it.
# If yes, it sends "Pong!" as a chatbot.

# Or if the message has "/cookies" in it, it sends their amount of cookies as CookieBot.

# Or if the message has "/online" or "/idle" in it, it will change player status!
@server.event
async def on_player_chat(player: Player, message: Message, was_sent: bool):
    if message.content == "/ping":
        await grandmabot.send_message(player.node, "Pong!")

    elif message.content == "/cookies":
        await cookiebot.send_message(player.node, "You have " + player.statistics.cookies + " cookies!")

    elif message.content in ["/online", "/idle"]:
        if message.content == "/online":
            await player.change_status(PlayerStatus.ONLINE)
            await grandmabot.send_message(player.node, "Successfully set your status to ONLINE!")
            return
        
        await player.change_status(PlayerStatus.IDLE)
        await grandmabot.send_message(player.node, "Successfully set your status to IDLE!")

server.initialize()