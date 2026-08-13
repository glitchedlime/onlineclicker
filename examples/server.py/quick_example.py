from onlineclicker.onlineclicker import *

# Creates a server object
server = Server()
# Makes a chatbot (you need to specify chatbot name in config.ini!)
chatbot = server.create_chatbot(badges=[Badge.VERIFIED], nickname_color=NicknameColor.ORANGE)

# Makes a bot that sends "pong!" when someone sends "/ping".
@server.event
async def on_player_chat(player: Player, message: Message, was_sent: bool):
    if message.content == "/ping":
        await chatbot.send_message(player.node, "pong!")

# You can also program your Discord bot here by using the "bot" variable from "onlineclicker/bot.py"
# The Discord bot is made with Pycord (https://pycord.dev/)
@bot.listen()
async def on_ready():
    print("Discord bot is ready!")

# Starts the server and Discord bot
server.initialize(discord_bot=True)