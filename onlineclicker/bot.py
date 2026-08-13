import discord
#import aiomysql
import aiosqlite
#import sqlglot
import bcrypt
import datetime
import configparser
from random import randint
from dotenv import load_dotenv
#from os import getenv

# https://discord.gg/StJxMSc8kM

testing = False
players_column = "test_players" if testing else "players"
colors = (["Red", "🟥"], ["Orange", "🟧"], ["Yellow", "🟨"], ["Green", "🟩"], ["Blue", "🟦"], ["Purple", "🟪"], ["Brown", "🟫"])

load_dotenv("./config/.env")
config = configparser.ConfigParser(allow_no_value=True)
config.read("./config/config.ini")
bot = discord.Bot(intents=discord.Intents.all())
pool = None

def _get_ini_value(section, value, _type=None):
    try:
        value = config.get(section, value)
        if _type != None:
            value = _type(value)
        return value
    except:
        return None

# TAKE A LOOK AT .env FILE!!!
DB_TYPE = _get_ini_value("Global", "DB_TYPE") if _get_ini_value("Global", "DB_TYPE") != None else "SQLite3"
MODROLES = [int(role.strip()) for role in _get_ini_value("Discord", "MODROLES").split(",") if role != ""] if _get_ini_value("Discord", "MODROLES") != None else []
SERVER_ID = _get_ini_value("Discord", "DISCORD_SERVER_ID", int)
REGISTERED_ROLE_ID = _get_ini_value("Discord", "REGISTERED_ROLE_ID", int)
_CHATBOT_USERNAMES = [chatbot.strip() for chatbot in _get_ini_value("Global", "CHATBOT_USERNAMES").split(',')] if _get_ini_value("Global", "CHATBOT_USERNAMES") != None else []
_CHATBOT_LOWER_USERNAMES = [chatbot.lower() for chatbot in _CHATBOT_USERNAMES]

username_change_cooldowns = {}

# { "table_name": [ row1, row2, ... ], ... }
# db_cache = {}

async def execDB(query: str, vars: tuple = None) -> list:
    """Executes an SQL query on DB. This function is a coroutine.

    Parameters:
        query (str): SQLite query to execute.
        vars (tuple): *Optional.* Adds variables to SQL query to escape user input.

    Returns:
        list: A list of selected items. If there are none, it returns an empty list.
    """

    selected = []

    #if DB_TYPE == "MySQL":
        #async with pool.acquire() as con:
            #async with con.cursor() as cur:
                #if vars != "" and vars != None:
                    #await cur.execute(mysql, vars)
                #else:
                    #await cur.execute(mysql)

                #rows = await cur.fetchall()

                #for row in rows:
                    #selected.append(list(row))

    #elif DB_TYPE == "SQLite":
    async with aiosqlite.connect("sqlite3.db") as db:
        if vars != "" and vars != None:
            cur = await db.execute(query, vars)
        else:
            cur = await db.execute(query)
            
        rows = await cur.fetchall()

        for row in rows:
            selected.append(list(row))
        else:
            await db.commit()

    return selected

def isModerator(member: discord.Member):
    if member.guild_permissions.administrator:
        return True
    else:
        for role in member.roles:
            if role.id in MODROLES:
                return True
            
        return False

def errorEmbed(author: discord.User, description: str, title: str = "Error!"):
    return discord.Embed(
        author=discord.EmbedAuthor(name=author.name, icon_url=author.display_avatar.url),
        title=title + " :x:",
        description=description,
        color=discord.Color.red()
    )

def successEmbed(author: discord.User, description: str, title: str = "Success!"):
    return discord.Embed(
        author=discord.EmbedAuthor(name=author.name, icon_url=author.display_avatar.url),
        title=title + " :white_check_mark:",
        description=description,
        color=discord.Color.green()
    )

def generate_hash(_str: str):
    salt = bcrypt.gensalt()
    hashed_str = bcrypt.hashpw(_str.encode("utf-8"), salt)
    return hashed_str

async def add_user(user: discord.Member, username: str, password: str):
    pass_hash = generate_hash(password).decode("utf-8")
    await execDB(f"INSERT INTO {players_column}(discord_id, username, password, nickname_color, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)", (user.id, username, pass_hash, randint(0, len(colors)-1)))
    if REGISTERED_ROLE_ID:
        try:
            await user.add_roles(user.guild.get_role(REGISTERED_ROLE_ID))
        except:
            pass

async def delete_user(guild: discord.Guild, user: discord.Member | int):
    user_id = user if isinstance(user, int) else user.id
    user = guild.get_member(user) if isinstance(user, int) else user

    await execDB(f"DELETE FROM {players_column} WHERE discord_id=?", (user_id, ))
    if REGISTERED_ROLE_ID and isinstance(user, discord.Member):
        try:
            await user.remove_roles(guild.get_role(REGISTERED_ROLE_ID))
        except:
            pass

@bot.event
async def on_ready():
    #if DB_TYPE == "MySQL":
        #global pool
        #pool = await aiomysql.create_pool(
            #**{
                #"host": getenv("DB_HOST"),
                #"port": int(getenv("DB_PORT")),
                #"user": getenv("DB_USER"),
                #"password": getenv("DB_PASS"),
                #"db": getenv("DB_NAME")
            #},
            #autocommit=True,
            #connect_timeout=None
        #)

    guild = bot.get_guild(SERVER_ID)
    role = guild.get_role(REGISTERED_ROLE_ID)
    registered_users = await execDB(f"SELECT discord_id, username FROM {players_column}")
    
    for member in guild.members:
        for reg_user in registered_users:
            if member.id == reg_user[0]:
                # If member doesn't have the "registered" role
                if role not in member.roles:
                    await member.add_roles(role)

                # If the player username belongs to a chatbot
                if reg_user[1].lower() in _CHATBOT_LOWER_USERNAMES:
                    unnamed_players = await execDB(f"SELECT username FROM {players_column} WHERE username LIKE '%Unnamed'")
                    unnamed_username = "unnamed"
                    num = 0

                    while unnamed_username + str(num) in unnamed_players:
                        num += 1

                    await execDB(f"UPDATE {players_column} SET username=? WHERE discord_id=?", (unnamed_username + str(num), member.id))

    # DB caching but it's probably useless because the DB probably won't be big
    # If this changes, I'll implement caching
    """
    tables = await execDB("SHOW TABLES;", sqlite="SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")

    for table in tables:
        table = table[0]

        if table in ["chatlogs", "logs"]:
            continue

        columns = await execDB("SELECT column_name FROM information_schema.columns WHERE table_name=?", vars=(table, ), sqlite="SELECT name FROM pragma_table_info(?)")
        columns = [x[0] for x in columns]
        columns = ", ".join(columns)
        rows = await execDB(f"SELECT {columns} FROM {table};")
        db_cache[table] = []

        for row in rows:
            db_cache[table].append(row)
    """
    
    #if DB_TYPE == "MySQL":
        # Pinging connection between DB just in case
        #while True:
            #await execDB("DO 0;")
            #await sleep(10)

@bot.slash_command(description="Registers a new account.")
async def register(ctx: discord.ApplicationContext, username: discord.Option(str, "The username you want to use", min_length=1, max_length=50), password: discord.Option(str, "The password you want to use to access your account (min. 8 characters)", min_length=8, max_length=50)): # type: ignore
    await ctx.defer(ephemeral=True)

    registered_for_this_discord_account = await execDB(f"SELECT username FROM {players_column} WHERE discord_id=?", (ctx.user.id, ))
    is_already_registered = await execDB(f"SELECT username FROM {players_column} WHERE LOWER(username)=?", (username.lower(), ))
    banned = await execDB("SELECT reason FROM bans WHERE discord_id=?", (ctx.user.id, ))

    if len(banned) != 0:
        await ctx.respond(embed=errorEmbed(ctx.user, f"You can't create an account because you're banned from connecting to the server. Reason: `{banned[0][0]}`"), ephemeral=True)
    elif len(registered_for_this_discord_account) != 0:
        await ctx.respond(embed=errorEmbed(ctx.user, "You can have a maximum of one account. If you want to change something, use the command `/manage`."), ephemeral=True)
    elif len(is_already_registered) != 0:
        await ctx.respond(embed=errorEmbed(ctx.user, "An account with this username has already been registered. Please choose another one!"), ephemeral=True)
    elif not username.replace(".", "").replace("-", "").replace("_", "").isalnum():
        await ctx.respond(embed=errorEmbed(ctx.user, "Your username must be alphanumeric (must contain only letters and numbers). Dashes (-), dots (.) and underscores (_) **are allowed**!"), ephemeral=True)
    elif username.lower() in _CHATBOT_LOWER_USERNAMES:
        await ctx.respond(embed=errorEmbed(ctx.user, "This username is used by one of our chatbots. Please use a different one!"), ephemeral=True)
    else:
        await add_user(ctx.user, username, password)
        await ctx.respond(embed=successEmbed(ctx.user, "Your account was successfully created!"), ephemeral=True)

@bot.slash_command(description="Manages your account.")
async def manage(ctx: discord.ApplicationContext):
    registered_for_this_discord_account = await execDB(f"SELECT username FROM {players_column} WHERE discord_id=?", (ctx.user.id, ))

    if len(registered_for_this_discord_account) == 0:
        await ctx.respond(embed=errorEmbed(ctx.user, "You haven't registered an account. Use the command `/register` to make one!"), ephemeral=True)
    else:
        registered_username = registered_for_this_discord_account[0][0]

        class ManageView(discord.ui.View):
            @discord.ui.button(
                label="Change Username",
                style=discord.ButtonStyle.gray,
                emoji="📝"
            )

            async def change_username_button(self, button: discord.Button, interaction: discord.Interaction):
                if interaction.user.id != ctx.user.id:
                    await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                else:
                    class Modal(discord.ui.Modal):
                        def __init__(self, *args, **kwargs) -> None:
                            super().__init__(*args, **kwargs)

                            self.add_item(discord.ui.InputText(label="New username:", max_length=50, min_length=1))

                        async def callback(self, interaction: discord.Interaction):
                            if interaction.user.id in username_change_cooldowns and datetime.datetime.now() - username_change_cooldowns[interaction.user.id] < datetime.timedelta(days=1):
                                await interaction.response.send_message(embed=errorEmbed(ctx.user, "You can change your username again after 1 day. Please wait!"), ephemeral=True)
                                return

                            username = self.children[0].value
                            is_already_registered = await execDB(f"SELECT username FROM {players_column} WHERE LOWER(username)=?", (username.lower(), ))

                            if registered_username.lower() == username.lower():
                                await interaction.response.send_message(embed=errorEmbed(ctx.user, "You can't change your username to your current username. Note that case doesn't matter."), ephemeral=True)
                                return
                            if len(is_already_registered) != 0:
                                await interaction.response.send_message(embed=errorEmbed(ctx.user, "An account with this username has already been registered. Please choose another one!"), ephemeral=True)
                                return
                            elif not username.replace(".", "").replace("-", "").replace("_", "").isalnum():
                                await interaction.response.send_message(embed=errorEmbed(ctx.user, "Your username must be alphanumeric (must contain only letters and numbers). Dashes (-), dots (.) and underscores (_) **are allowed**!"), ephemeral=True)
                                return
                            elif username.lower() in _CHATBOT_LOWER_USERNAMES:
                                await interaction.response(embed=errorEmbed(ctx.user, "This username is used by one of our chatbots. Please use a different one!"), ephemeral=True)
                                return

                            old_username = await execDB(f"SELECT username FROM {players_column} WHERE discord_id=?", (interaction.user.id, ))

                            await execDB(f"UPDATE {players_column} SET username=? WHERE discord_id=?;", (self.children[0].value, interaction.user.id))
                            await execDB(f"INSERT INTO logs(executor, target, action, note, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);", (interaction.user.id, interaction.user.id, "username", f"{old_username[0][0]} -> {self.children[0].value}"))
                            username_change_cooldowns[interaction.user.id] = datetime.datetime.now()
                            await interaction.response.send_message(embed=successEmbed(interaction.user, f"Your account username has successfully been changed to `{self.children[0].value}`."), ephemeral=True)

                    await interaction.response.send_modal(Modal(title="Change Username"))

            @discord.ui.button(
                label="Change Password",
                style=discord.ButtonStyle.gray,
                emoji="📝"
            )

            async def change_password_button(self, button: discord.Button, interaction: discord.Interaction):
                if interaction.user.id != ctx.user.id:
                    await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                else:
                    class Modal(discord.ui.Modal):
                        def __init__(self, *args, **kwargs) -> None:
                            super().__init__(*args, **kwargs)

                            self.add_item(discord.ui.InputText(label="New password:", max_length=50, min_length=8))

                        async def callback(self, interaction: discord.Interaction):
                            pass_hash = generate_hash(self.children[0].value).decode("utf-8")
                            await execDB(f"UPDATE {players_column} SET password=? WHERE discord_id=?", (pass_hash, interaction.user.id))
                            await interaction.response.send_message(embed=successEmbed(interaction.user, f"Your account password has successfully been changed."), ephemeral=True)

                    await interaction.response.send_modal(Modal(title="Change Password"))

            @discord.ui.button(
                label="Change Nickname Color",
                style=discord.ButtonStyle.gray,
                emoji="🎨"
            )

            async def change_nickname_color_button(self, button: discord.Button, interaction: discord.Interaction):
                if interaction.user.id != ctx.user.id:
                    await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                else:
                    options = []

                    for i in range(len(colors)):
                        color = colors[i]
                        options.append(discord.SelectOption(label=color[0], emoji=color[1], value=str(i)))

                    class ChangeNickColor(discord.ui.View):
                        @discord.ui.select(
                            placeholder="Select a color...",
                            options=options
                        )

                        async def change_color(self, select: discord.SelectMenu, interaction: discord.Interaction):
                            if interaction.user.id != ctx.user.id: # just in case
                                await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                            else:
                                await execDB(f"UPDATE {players_column} SET nickname_color=? WHERE discord_id=?", (int(select.values[0]), interaction.user.id))
                                await interaction.response.send_message(embed=successEmbed(interaction.user, "Your chat color has successfully been changed."), ephemeral=True)

                    await interaction.response.send_message(embed=discord.Embed(
                        author=discord.EmbedAuthor(name=interaction.user.name, icon_url=interaction.user.display_avatar.url),
                        title="Choose a chat nickname color! :art:",
                        description="Now you can choose the color of the nickname you want in the chat by using the select menu!",
                        color=discord.Color.teal()
                    ), view=ChangeNickColor(), ephemeral=True)

            @discord.ui.button(
                label="Delete Account",
                style=discord.ButtonStyle.danger,
                emoji="🗑️"
            )

            async def delete_account_button(self, button: discord.Button, interaction: discord.Interaction):
                if interaction.user.id != ctx.user.id:
                    await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                else:
                    class Msg:
                        val = None

                    class Confirm(discord.ui.View):
                        @discord.ui.button(
                            label="Yes!",
                            style=discord.ButtonStyle.red
                        )

                        async def yes(self, button: discord.Button, interaction: discord.Interaction):
                            if interaction.user.id != ctx.user.id: # just in case
                                await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                            else:
                                await delete_user(interaction.guild, interaction.user)
                                await Msg.val.delete()
                                await interaction.response.send_message(embed=successEmbed(interaction.user, "Your account has successfully been deleted."), ephemeral=True)

                        @discord.ui.button(
                            label="No!",
                            style=discord.ButtonStyle.green
                        )

                        async def no(self, button: discord.Button, interaction: discord.Interaction):
                            if interaction.user.id != ctx.user.id: # just in case
                                await interaction.response.send_message(errorEmbed(interaction.user, "You can't interact with this."), ephemeral=True)

                            else:
                                await Msg.val.delete()

                    Msg.val = await interaction.response.send_message(embed=discord.Embed(title="Account Deletion :wastebasket:", description="Are you sure you want to delete your account?", color=discord.Color.red()), view=Confirm(), ephemeral=True)
                    Msg.val = await Msg.val.original_response()

        await ctx.respond(embed=discord.Embed(
            author=discord.EmbedAuthor(name=ctx.user.name, icon_url=ctx.user.display_avatar.url),
            title="Account Manager :gear:",
            description=f"Here you can manage your account by clicking one of the buttons below!\n\nYour username is: `{registered_username}`\nYour password is hidden for security reasons. If you forgot it, please change it.",
            color=discord.Color.teal()
        ), view=ManageView(), ephemeral=True)

@bot.slash_command(description="Gets Discord user from in-game username.")
async def get_discord_user_game_info(ctx: discord.ApplicationContext, username: str):
    if not isModerator(ctx.user):
        await ctx.respond(embed=errorEmbed(ctx.user, "You can't interact with this."), ephemeral=True)

    else:
        await ctx.defer(ephemeral=True)

        log_limit = 20
        user = await execDB(f"SELECT discord_id FROM {players_column} WHERE username=?", (username, ))
        logs = await execDB("SELECT executor, note FROM logs WHERE action=? AND note LIKE ? ORDER BY id DESC LIMIT ?;", ("username", f"%{username}%", log_limit))
        logs_str = ""

        if len(logs) != 0:
            for log in logs:
                logs_str += f"\n<@{log[0]}>: {log[1]}"

        else:
            logs_str = "\nNo logs found."

        await ctx.respond(embed=discord.Embed(
            title=f"Search results 🔍️ ({username})",
            description="**This username currently belongs to:** " + ((f"<@{user[0][0]}> ({user[0][0]})") if len(user) != 0 else "nobody")
                        + f"\n\n**Recent {log_limit} logs of changing this username:**{logs_str}",
            color=discord.Colour.teal() 
        ))

@bot.slash_command(description="Bans a user from connecting to the server.")
async def ban_service(ctx: discord.ApplicationContext, user: discord.Option(discord.User, "The user you want to ban"), reason: discord.Option(str, "The reason for banning the user", max_length=255)): # type: ignore
    user_id = user if isinstance(user, int) else user.id

    if not isModerator(ctx.user):
        await ctx.respond(embed=errorEmbed(ctx.user, "You can't interact with this."), ephemeral=True)

    else:
        is_banned = await execDB("SELECT reason FROM bans WHERE discord_id=?", (user_id, ))

        if len(is_banned) != 0:
            await ctx.respond(embed=errorEmbed(ctx.user, f"This user has already been banned.\nReason: `{is_banned[0][0]}`"), ephemeral=True)
        else:
            await execDB("INSERT INTO bans(discord_id, reason, created_at) VALUES (?, ?, CURRENT_TIMESTAMP);", (user_id, reason))
            await execDB("INSERT INTO logs(executor, target, action, note, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);", (ctx.user.id, user_id, "ban", reason))
            await delete_user(ctx.guild, user_id)
            await ctx.respond(embed=successEmbed(ctx.user, f"The user has successfully been banned from connecting to the server.\nReason: `{reason}`"))

@bot.slash_command(description="Unbans a user from connecting to the server.")
async def unban_service(ctx: discord.ApplicationContext, user: discord.Option(discord.User, "The user you want to unban"), reason: discord.Option(str, "The reason for unbanning the user", max_length=255)): # type: ignore
    user = user if isinstance(user, int) else user.id

    if not isModerator(ctx.user):
        await ctx.respond(embed=errorEmbed(ctx.user, "You can't interact with this."), ephemeral=True)

    else:
        is_banned = await execDB("SELECT reason FROM bans WHERE discord_id=?", (user, ))

        if len(is_banned) == 0:
            await ctx.respond(embed=errorEmbed(ctx.user, f"This user isn't banned."), ephemeral=True)
        else:
            await execDB("DELETE FROM bans WHERE discord_id=?;", (user, ))
            await execDB("INSERT INTO logs(executor, target, action, note, created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);", (ctx.user.id, user, "unban", reason))
            await ctx.respond(embed=successEmbed(ctx.user, f"The user has successfully been unbanned from connecting to the server.\nReason: `{reason}`"))
