"""
A Python module that contains tools for running and managing a dedicated OnlineClicker server. It also contains scripts for running the Discord bot that is needed for account management.

OnlineClicker is an online multiplayer modification for Cookie Clicker, where you play as a cat and you can type in the chat. It's published on Steam Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3744919354

The library used for the Discord bot scripts is Pycord (MIT License). Official website: https://pycord.dev/

Copyright (C) 2026-present glitchedlime
License MIT, see LICENSE for more details.
"""

# WELCOME TO THE ONLINECLICKER SERVER BASE CODE
#
# Take a look, but try not to break anything.
# Want to suggest something? Contact me (glitchedlime) on our Discord (https://discord.gg/StJxMSc8kM)!

from __future__ import annotations
from typing import Any
from sys import modules

if "pdoc" not in modules:
    from .bot import bot

from abc import ABC
from jsonschema import validate
from colorama import Fore, Back
from dotenv import load_dotenv
from enum import Enum
import os
import ssl
import json
import asyncio
#import aiomysql
import aiosqlite
#import sqlglot
import websockets
import datetime
import no_profanity # this is actually my library; it works well but it's unfinished; I'll finish it someday for sure (adding more words and changing the detection system a lil bit) :)
import bcrypt
import logging
import configparser
import traceback
from pathlib import Path

__docformat__ = "google"
_docs_path = Path(__file__).parent.parent / "docs"

if _docs_path.exists():
    for file in sorted(_docs_path.iterdir()):
        if file.name.endswith((".py", ".md")):
            __doc__ += file.read_text(encoding="utf-8")

_testing = False # don't mind this :p
_chat_ratelimit: dict[websockets.ServerConnection, datetime.datetime] = {}
_missed_hearbeat: dict[websockets.ServerConnection, int] = {}

Path("./logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    filename="./logs/terminal_out.log",
    level=51,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.getLogger("websockets").setLevel(51)
_config = configparser.ConfigParser(allow_no_value=True)
_config.read("./config/config.ini")
load_dotenv("./config/.env")

def get_ini_value(section: str, variable: str, _type=None) -> Any | None:
    """Returns a value from variable in `config.ini`. If the value was not found, it returns None.
    
    Parameters:
        section (str): Section of the variable you want to get the value from.
        variable (str): Name of the varaible you want to get the value from.
        _type: *Optional.* Datatype in which the value should be returned. (example: int, str)

    Examples:
        >>> server_name = get_ini_value("Server", "SERVER_NAME")
        >>> max_in_lobby = get_ini_value("Server", "MAX_IN_LOBBY", int)
    """

    try:
        variable = _config.get(section, variable)
        if _type == bool:
            variable = eval(variable.capitalize())
        elif _type != None:
            variable = _type(variable)

        return variable
    except:
        return None

#_DB_TYPE = get_ini_value("Global", "DB_TYPE") if get_ini_value("Global", "DB_TYPE") != None else "SQLite3"
_PLAYERS_COLUMN = "test_players" if _testing else "players" # don't mind this - testing purposes
_CLIENT_VERSION = "1.6.1" # this is a mod client version
_SERVER_VERSION = "1.1"
_PORT = get_ini_value("Server", "PORT", int) if get_ini_value("Server", "PORT", int) != None else 24588
_SERVER_NAME = get_ini_value("Server", "SERVER_NAME") if get_ini_value("Server", "SERVER_NAME") != None else "OnlineClicker Server"
_OWNERS = [(int(owner.strip()) if owner.strip().isnumeric() else owner.strip()) for owner in get_ini_value("Server", "OWNERS").split(',')] if get_ini_value("Server", "OWNERS") != None else []
_MODERATORS = [(int(mod.strip()) if mod.strip().isnumeric() else mod.strip()) for mod in get_ini_value("Server", "MODERATORS").split(',')] if get_ini_value("Server", "MODERATORS") != None else []
_SUPPORTERS = [(int(supporter.strip()) if supporter.strip().isnumeric() else supporter.strip()) for supporter in get_ini_value("Server", "SUPPORTERS").split(',')] if get_ini_value("Server", "SUPPORTERS") != None else []
_VERIFIED = [(int(verified.strip()) if verified.strip().isnumeric() else verified.strip()) for verified in get_ini_value("Server", "VERIFIED").split(',')] if get_ini_value("Server", "VERIFIED") != None else []
_NODE_LIMIT = get_ini_value("Server", "MAX_IN_LOBBY", int)
_MAX_PLAYERS = get_ini_value("Server", "MAX_PLAYERS", int)
_LOG_MESSAGES = get_ini_value("Server", "LOG_MESSAGES", bool)
_CHATBOT_USERNAMES = [chatbot.strip() for chatbot in get_ini_value("Global", "CHATBOT_USERNAMES").split(',')] if get_ini_value("Global", "CHATBOT_USERNAMES") != None else []
_LOCALHOST = get_ini_value("Server", "LOCALHOST", bool) if get_ini_value("Server", "LOCALHOST", bool) != None else False

_profanity_filter = no_profanity.ProfanityFilter()
_pool = None

async def execDB(query: str, vars: tuple = None) -> list:
    """Executes an SQL query on DB. This function is a coroutine.

    Parameters:
        query (str): SQLite query to execute.
        vars (tuple): *Optional.* Adds variables to SQL query to escape user input.

    Returns:
        list: A list of selected items. If there are none, it returns an empty list.
    """

    selected = []

    #if _DB_TYPE == "MySQL":
        #async with _pool.acquire() as con:
            #async with con.cursor() as cur:
                #if vars != "" and vars != None:
                    #await cur.execute(mysql, vars)
                #else:
                    #await cur.execute(mysql)

                #rows = await cur.fetchall()

                #for row in rows:
                    #selected.append(list(row))

    #elif _DB_TYPE == "SQLite":
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

def compare_usernames(username1: str, username2: str) -> bool:
    """Compares two usernames using case-insensitive rules.
    
    Parameters:
        username1 (str): The first username to compare.
        username2 (str): The second username to compare.

    Returns:
        bool: Whether the usernames matches.
    """

    if username1 == None or username2 == None:
        return False
    else:
        return username1.lower() == username2.lower()
    
def is_player_in_list(player: Player, list: list[int | str]):
    """Checks if either player username or Discord user ID is in the specified list.
    
    Parameters:
        player (Player): The player to check.
        list (list[int | str]): The list of usernames and/or Discord user IDs.

    Returns:
        bool: Whether the player was found.
    """

    for value in list:
        if (isinstance(value, str) and compare_usernames(player.username, value)) or (isinstance(value, int) and player.discord_id == value):
            return True

    return False

# Check bcrypt hash
def _check_hash(check_str, _hash):
    return bcrypt.checkpw(check_str.encode("utf-8"), _hash)

# Calling registered functions
async def _call_registered_function(_list, function_name, *args):
    for func in _list:
        if func.__name__ == function_name:
            return await func(*args)

_valid_statistics_schema = {
    "type": "object",
    "properties": {
        "Cookies": {"type": "number"},
        "Cookies per second": {"type": "number"},
        "Sugar lumps": {"type": "integer"},
        "Upgrades": {"type": "integer"},
        "Achievements": {"type": "integer"},
        "Cursors": {"type": "integer"},
        "Grandmas": {"type": "integer"},
        "Farms": {"type": "integer"},
        "Mines": {"type": "integer"},
        "Factories": {"type": "integer"},
        "Banks": {"type": "integer"},
        "Temples": {"type": "integer"},
        "Wizard towers": {"type": "integer"},
        "Shipments": {"type": "integer"},
        "Alchemy labs": {"type": "integer"},
        "Portals": {"type": "integer"},
        "Time machines": {"type": "integer"},
        "Antimatter condensers": {"type": "integer"},
        "Prisms": {"type": "integer"},
        "Chancemakers": {"type": "integer"},
        "Fractal engines": {"type": "integer"},
        "Javascript consoles": {"type": "integer"},
        "Idleverses": {"type": "integer"},
        "Cortex bakers": {"type": "integer"},
        "You": {"type": "integer"}
    },
    "additionalProperties": False
}

_valid_statistics_schema["required"] = list(_valid_statistics_schema["properties"].keys())

class Base(ABC):
    """An abstract class with basic functions for certain classes."""

    def __repr__(self):
        """Generates a string that will be printed when a derived class is printed. This will print all properties (@property) of the class."""
        attrs = ""
        seen = set()

        for cls in type(self).mro():
            for k, v in cls.__dict__.items():
                if isinstance(v, property) and k not in seen:
                    attrs += f" {k}={("'" + getattr(self, k) + "'") if isinstance(getattr(self, k), str) else getattr(self, k)}"

        return f"<{type(self).__name__}{attrs}>"

class PlayerPosition:
    """A class that holds information about a player position. The player position is expressed in percentages."""

    def __init__(self, x: int | float, y: int | float):
        """
        Parameters:
            x (int | float): X coordinate of player position.
            y (int | float): Y coordinate of player position.
        """

        if not (isinstance(x, (int, float)) and isinstance(y, (int, float)) and x >= 0 and x <= 100 and y >= 0 and y <= 100):
            raise ValueError("Invalid position values. Make sure X and Y are integers and their values are in range from 0 to 100.")

        self._x: int | float = x
        self._y: int | float = y

    def __repr__(self):
        return f"<{type(self).__name__} x={self.x} y={self.y}>"

    @property
    def x(self) -> int | float:
        """X coordinate of player position."""
        return self._x
    @property
    def y(self) -> int | float:
        """Y coordinate of player position."""
        return self._y
    @property
    def string_value(self) -> str:
        """The string version of the PlayerPosition object."""
        return f"{self.x} {self.y}"
    
    @classmethod
    def str_to_object(cls, string: str) -> PlayerPosition:
        """Converts string to PlayerPosition. This method is a classmethod."""
        nums = string.split(" ")
        return cls(float(nums[0]), float(nums[1]))

class PlayerStatus(Enum):
    """A class that holds information about player status. This class is an enumeration."""

    ONLINE: str = "online"
    """The "online" status."""
    IDLE: str = "idle"
    """The "idle" status."""

class Badge(Enum):
    """A class representing a chat badge. This class is an enumeration."""

    OWNER: int = 0
    """This attribute has a value of 0. It represents a red wrench badge."""
    MODERATOR: int = 1
    """This attribute has a value of 1. It represents a green shield badge."""
    VERIFIED: int = 2
    """This attribute has a value of 2. It represents a badge with a purple checkmark."""
    SUPPORTER: int = 3
    """This attribute has a value of 3. It represents a purple heart badge."""

class NicknameColor(Enum):
    """A class representing a nickname color. This class is an enumeration."""

    RED: int = 0
    """This attribute has a value of 0. It represents a red nickname color."""
    ORANGE: int = 1
    """This attribute has a value of 1. It represents an orange nickname color."""
    YELLOW: int = 2
    """This attribute has a value of 2. It represents a yellow nickname color."""
    GREEN: int = 3
    """This attribute has a value of 3. It represents a green nickname color."""
    BLUE: int = 4
    """This attribute has a value of 4. It represents a blue nickname color."""
    PURPLE: int = 5
    """This attribute has a value of 5. It represents a purple nickname color."""
    BROWN: int = 6
    """This attribute has a value of 6. It represents a brown nickname color."""

class ClientErrorMessage(str, Enum):
    """A class representing an error message intended to be sent to client. This class is an enumeration. All exceptions are in HTML format."""

    FULL_SERVER: str = "This server is currently full. Please try again later!"
    """Represents a "full server" exception."""
    MISSING_REQ_VALUE: str = "Missing the \"request\" value."
    """Represents a "missing 'request' JSON value" exception."""
    WRONG_USERNAME_OR_PASSWORD: str = "Wrong username or password. If you forgot to log in, please enter your account details in the \"Account\" section."
    """Represents a "wrong username or password" exception."""
    OUTDATED_CLIENT: str = f"Your version of OnlineClicker is outdated. To join the server, update to the newest version (<b><strong>v{_CLIENT_VERSION}</strong></b>)!"
    """Represents an "outdated client" exception."""
    ALREADY_LOGGED_IN: str = "You're already logged in to the server."
    """Represents an "already logged in" exception."""

class PlayerStatistics:
    """A class representing player statistics."""

    def __init__(self, *args):
        """
        Parameters:
            cookies (float): Number of cookies.
            cookies_per_second (float): Number of cookies per second.
            sugar_lumps (int): Number of sugar lumps.
            upgrades (int): Number of upgrades.
            achievements (int): Number of achievements.
            cursors (int): Number of "Cursor" buildings.
            grandmas (int): Number of "Grandma" buildings.
            farms (int): Number of "Farm" buildings.
            mines (int): Number of "Mine" buildings.
            factories (int): Number of "Factory" buildings.
            banks (int): Number of "Bank" buildings.
            temples (int): Number of "Temple" buildings.
            wizard_towers (int): Number of "Wizard Tower" buildings.
            shipments (int): Number of "Shipment" buildings.
            alchemy_labs (int): Number of "Alchemy Lab" buildings.
            portals (int): Number of "Portal" buildings.
            time_machines (int): Number of "Time Machine" buildings.
            antimatter_condensers (int): Number of "Antimatter Condenser" buildings.
            prisms (int): Number of "Prism" buildings.
            chancemakers (int): Number of "Chancemaker" buildings.
            fractal_engines (int): Number of "Fractal Engine" buildings.
            javascript_consoles (int): Number of "Javascript Console" buildings.
            idleverses (int): Number of "Idleverse" buildings.
            cortex_bakers (int): Number of "Cortex Baker" buildings.
            you (int): Number of "You" buildings.
        """
        data = args if args else [0] * 25

        self._cookies: float = data[0]
        self._cookies_per_second: float = data[1]
        self._sugar_lumps: int = data[2]
        self._upgrades: int = data[3]
        self._achievements: int = data[4]
        self._cursors: int = data[5]
        self._grandmas: int = data[6]
        self._farms: int = data[7]
        self._mines: int = data[8]
        self._factories: int = data[9]
        self._banks: int = data[10]
        self._temples: int = data[11]
        self._wizard_towers: int = data[12]
        self._shipments: int = data[13]
        self._alchemy_labs: int = data[14]
        self._portals: int = data[15]
        self._time_machines: int = data[16]
        self._antimatter_condensers: int = data[17]
        self._prisms: int = data[18]
        self._chancemakers: int = data[19]
        self._fractal_engines: int = data[20]
        self._javascript_consoles: int = data[21]
        self._idleverses: int = data[22]
        self._cortex_bakers: int = data[23]
        self._you: int = data[24]

    @property
    def cookies(self) -> float:
        """Number of cookies."""
        return self._cookies
    @property
    def cookies_per_second(self) -> float:
        """Number of cookies per second."""
        return self._cookies_per_second
    @property
    def sugar_lumps(self) -> int:
        """Number of sugar lumps."""
        return self._sugar_lumps
    @property
    def upgrades(self) -> int:
        """Number of upgrades."""
        return self._upgrades
    @property
    def achievements(self) -> int:
        """Number of achievements."""
        return self._achievements
    @property
    def cursors(self) -> int:
        """Number of "Cursor" buildings."""
        return self._cursors
    @property
    def grandmas(self) -> int:
        """Number of "Grandma" buildings."""
        return self._grandmas
    @property
    def farms(self) -> int:
        """Number of "Farm" buildings."""
        return self._farms
    @property
    def mines(self) -> int:
        """Number of "Mine" buildings."""
        return self._mines
    @property
    def factories(self) -> int:
        """Number of "Factory" buildings."""
        return self._factories
    @property
    def banks(self) -> int:
        """Number of "Bank" buildings."""
        return self._banks
    @property
    def temples(self) -> int:
        """Number of "Temple" buildings."""
        return self._temples
    @property
    def wizard_towers(self) -> int:
        """Number of "Wizard Tower" buildings."""
        return self._wizard_towers
    @property
    def shipments(self) -> int:
        """Number of "Shipment" buildings."""
        return self._shipments
    @property
    def alchemy_labs(self) -> int:
        """Number of "Alchemy Lab" buildings."""
        return self._alchemy_labs
    @property
    def portals(self) -> int:
        """Number of "Portal" buildings."""
        return self._portals
    @property
    def time_machines(self) -> int:
        """Number of "Time Machine" buildings."""
        return self._time_machines
    @property
    def antimatter_condensers(self) -> int:
        """Number of "Antimatter Condenser" buildings."""
        return self._antimatter_condensers
    @property
    def prisms(self) -> int:
        """Number of "Prism" buildings."""
        return self._prisms
    @property
    def chancemakers(self) -> int:
        """Number of "Chancemaker" buildings."""
        return self._chancemakers
    @property
    def fractal_engines(self) -> int:
        """Number of "Fractal Engine" buildings."""
        return self._fractal_engines
    @property
    def javascript_consoles(self) -> int:
        """Number of "Javascript Console" buildings."""
        return self._javascript_consoles
    @property
    def idleverses(self) -> int:
        """Number of "Idleverse" buildings."""
        return self._idleverses
    @property
    def cortex_bakers(self) -> int:
        """Number of "Cortex Baker" buildings."""
        return self._cortex_bakers
    @property
    def you(self) -> int:
        """Number of "You" buildings."""
        return self._you

    def to_json(self) -> dict:
        """Converts PlayerStatistics object to JSON."""
        _dict = {}

        for k, v in self.__dict__.copy().items():
            k = k[1:]
            _dict[k.capitalize().replace("_", " ")] = v

        return _dict
    
class Message:
    """A class representing a chat message."""

    def __init__(self, username: str, content: str, badges: list[Badge] = [], nickname_color: NicknameColor = NicknameColor.RED):
        """
        Parameters:
            username (str): Sender username.
            content (str): Content of the message. Players can only type max. 100 characters.
            badges (list[Badge]): List of sender badges.
            nickname_color (NicknameColor): Sender nickname color.
        """
        self._username: str = username
        self._content: str = content
        self._badges: list[Badge] = badges
        self._nickname_color: NicknameColor = nickname_color

    def __repr__(self):
        return self.username + ": " + self.content

    @property
    def username(self) -> str:
        """Sender username."""
        return self._username
    @property
    def content(self) -> str:
        """Content of the message. Players can only type max. 100 characters."""
        return self._content
    @property
    def censored_content(self) -> str:
        """Censored version of the message content."""
        return _profanity_filter.censor_text(self.content)
    @property
    def badges(self) -> list[Badge]:
        """List of sender badges."""
        return self._badges
    @property
    def badges_values(self) -> list[int]:
        """Returns list of values of badge attributes."""
        return [badge.value for badge in self.badges]
    @property
    def nickname_color(self) -> NicknameColor:
        """Sender nickname color."""
        return self._nickname_color

class SafePlayer(Base):
    """Safe version of Player (without last_heartbeat, websocket, password). This class is NOT intended to be created by the server programmer."""

    def __init__(self,
                 server: Server,
                 discord_id: int,
                 node: str,
                 username: str,
                 position: PlayerPosition,
                 flip: bool,
                 status: PlayerStatus,
                 nickname_color: NicknameColor,
                 statistics: PlayerStatistics):

        self._server: Server = server
        self._discord_id: int = discord_id
        self._node: str = node
        self._username: str = username
        self._position: PlayerPosition = position
        self._flip: bool = flip
        self._status: PlayerStatus = status
        self._nickname_color: NicknameColor = nickname_color
        self._statistics: PlayerStatistics = statistics

    @property
    def discord_id(self) -> int:
        """Player Discord user ID."""
        return self._discord_id
    @property
    def node(self) -> str:
        """Node to which the player is assigned."""
        return self._node
    @property
    def username(self) -> str:
        """Player username in the right case. However, usernames in general are case-**in**sensitive."""
        return self._username
    @property
    def position(self) -> PlayerPosition:
        """Player position object."""
        return self._position
    @property
    def flip(self) -> bool:
        """Whether the player sprite is flipped (facing right)."""
        return self._flip
    @property
    def status(self) -> PlayerStatus:
        """Player status object."""
        return self._status
    @property
    def nickname_color(self) -> NicknameColor:
        """Player nickname color object."""
        return self._nickname_color
    @property
    def statistics(self) -> PlayerStatistics:
        """Player statistics object."""
        return self._statistics
    
    def to_json(self) -> dict:
        """Converts the player object to JSON."""

        _dict = {}
        _ignored_attributes = ["_server"]

        for k, v in self.__dict__.copy().items():
            if k in _ignored_attributes:
                continue

            k = k[1:]

            if k == "position":
                v = v.string_value

            elif k == "status":
                v = v.value

            elif k == "nickname_color":
                v = v.value

            elif k == "statistics":
                v = v.to_json()

            _dict[k] = v
        
        return _dict

class Player(SafePlayer):
    """A class representing a player connected to the server. Derived from SafePlayer. This class is NOT intended to be created by the server programmer."""

    def __init__(self,
                 server: Server,
                 websocket: websockets.ServerConnection,
                 discord_id: int,
                 node: str,
                 username: str,
                 password: str,
                 last_heartbeat: datetime.datetime,
                 position: PlayerPosition,
                 flip: bool,
                 status: PlayerStatus,
                 nickname_color: NicknameColor,
                 statistics: PlayerStatistics):

        super().__init__(server,
                 discord_id,
                 node,
                 username,
                 position,
                 flip,
                 status,
                 nickname_color,
                 statistics)

        self._websocket: websockets.ServerConnection = websocket
        self._password: str = password
        self._last_heartbeat: datetime.datetime = last_heartbeat

    @property
    def websocket(self) -> websockets.ServerConnection:
        """Connection object of the player."""
        return self._websocket
    @property
    def password(self) -> str:
        """Player hashed password."""
        return self._password
    @property
    def last_heartbeat(self) -> datetime.datetime:
        """Last time the player sent a heartbeat message."""
        return self._last_heartbeat

    def safe(self) -> SafePlayer:
        """Converts the player object to its safe version."""

        return self.__class__.__base__(
                 self._server,
                 self.discord_id,
                 self.node,
                 self.username,
                 self.position,
                 self.flip,
                 self.status,
                 self.nickname_color,
                 self.statistics)

    async def move(self, position: PlayerPosition, flip: bool = None) -> None:
        """Moves the player to a specific position. This method is a coroutine.
        
        Parameters:
            position (PlayerPosition): Position to move the player to.
            flip (bool): Whether the player sprite should be flipped (facing right).
        """

        self._position = position
        self._flip=(self.position.x < position.x) if flip == None else flip
        await self._server.broadcast_to_node(self.node, {"request": "move", "position": self.position.string_value, "flip": self.flip}, sender_websocket=self.websocket)

    async def change_status(self, status: PlayerStatus) -> None:
        """Changes the player status. This method is a coroutine.

        Parameters:
            status (PlayerStatus): Updated player status.
        """

        self._status = status
        await self._server.broadcast_to_node(self.node, {"request": "status", "value": self.status.value}, sender_websocket=self.websocket)

class ChatBot(Base):
    """A class representing a chatbot in the server chat. This class is NOT intended to be created by the server programmer."""

    def __init__(self,
                server: Server,
                username_index: int = 0,
                badges: list[Badge] = [],
                nickname_color: NicknameColor = NicknameColor.RED
                ):

        self._server: Server = server
        self._username: int = self._server.chatbot_usernames[username_index]
        self._badges: list[Badge] = badges
        self._nickname_color: NicknameColor = nickname_color

    @property
    def username(self) -> int:
        """Chatbot username."""
        return self._username
    @property
    def badges(self) -> list[Badge]:
        """List of chatbot badges."""
        return self._badges
    @property
    def nickname_color(self) -> NicknameColor:
        """Chatbot nickname color."""
        return self._nickname_color
        
    async def send_message(self, node: str, content: str, log_message: bool = False):
        """Sends a message as the chatbot. This method is a coroutine.

        Parameters:
            node (str): Node to broadcast the message to.
            content (str): Content of the message.
            log_message (bool): *Optional.* Whether the message should be logged to DB. If the message has more than 100 characters, it won't be logged.
        """
        await self._server.send_message(node, Message(self.username, content, self.badges, self.nickname_color), log_message)

class Server(Base):
    """A class representing the OnlineClicker server. Configuration attributes are defaulted to its values in the `config.ini` file."""

    def __init__(self,
                 name: str = _SERVER_NAME,
                 port: int = _PORT,
                 node_limit: int = _NODE_LIMIT,
                 max_players: int = _MAX_PLAYERS,
                 log_messages: bool = _LOG_MESSAGES,
                 owners: list[int | str] = _OWNERS,
                 moderators: list[int | str] = _MODERATORS,
                 supporters: list[int | str] = _SUPPORTERS,
                 verified: list[int | str] = _VERIFIED,
                 localhost: bool = _LOCALHOST
                 ):
        """
        Parameters:
            name (str): Server name.
            port (int): The port on which the server is running.
            node_limit (int): The maximum number of players who can play on one node.
            max_players (int): The maximum number of players that can be connected to the server.
            log_messages (bool): Whether player messages should be logged to DB.
            owners (list[int | str]): List of server owners' identificators (Discord user ID or in-game username).
            moderators (list[int | str]): List of server moderators' identificators (Discord user ID or in-game username).
            supporters (list[int | str]): List of server supporters' identificators (Discord user ID or in-game username).
            verified (list[int | str]): List of server verified players' identificators (Discord user ID or in-game username).
            localhost (bool): Whether the server should run on localhost.
        """
        
        self._name: str = name
        self._port: int = port
        self._node_limit: int = node_limit
        self._max_players: int = max_players
        self._log_messages: bool = log_messages
        self._owners: list[int | str] = owners
        self._moderators: list[int | str] = moderators
        self._supporters: list[int | str] = supporters
        self._verified: list[int | str] = verified
        self._localhost: bool = localhost

        self._all_players: dict[websockets.ServerConnection, Player] = {}
        self._nodes: dict[str, list[str]] = {}
        self._chatbot_usernames: list[str] = _CHATBOT_USERNAMES

        # Registered event functions (@self.event)
        self.__registered_events = []

    @property
    def name(self) -> str:
        """Server name."""
        return self._name
    @property
    def port(self) -> int:
        """The port on which the server is running."""
        return self._port
    @property
    def node_limit(self) -> int:
        """The maximum number of players who can play on one node."""
        return self._node_limit
    @property
    def max_players(self) -> int:
        """The maximum number of players that can be connected to the server."""
        return self._max_players
    @property
    def log_messages(self) -> bool:
        """Whether player messages should be logged to DB."""
        return self._log_messages
    @property
    def owners(self) -> list[int | str]:
        """List of server owners' identificators (Discord user ID or in-game username)."""
        return self._owners
    @property
    def moderators(self) -> list[int | str]:
        """List of server moderators' identificators (Discord user ID or in-game username)."""
        return self._moderators
    @property
    def supporters(self) -> list[int | str]:
        """List of server supporters' identificators (Discord user ID or in-game username)."""
        return self._supporters
    @property
    def verified(self) -> list[int | str]:
        """List of server verified players' identificators (Discord user ID or in-game username)."""
        return self._verified
    @property
    def all_players(self) -> dict[websockets.ServerConnection, Player]:
        """Dictionary of all connected players."""
        return self._all_players
    @property
    def nodes(self) -> dict[str, list[str]]:
        """Dictionary of every node and usernames of players connected to them."""
        return self._nodes
    @property
    def chatbot_usernames(self) -> bool:
        """List of server chatbot usernames."""
        return self._chatbot_usernames
    @property
    def localhost(self) -> bool:
        """Whether the server should run on localhost."""
        return self._localhost

    def initialize(self, discord_bot: bool = False, ssl_chain: list[str] = None) -> None:
        """Runs the server. Initializes OnlineClicker server and/or Discord bot at the same time. This method is blocking and should be at the last line of your custom server script.

        Parameters:
            discord_bot (bool): *Optional.* Whether the Discord bot should be launched.
            ssl_chain (list[str]): *Optional.* SSL certification chain. This is a list that contains a path to your certificate (index 0) and a path to your private key (index 1).
        """

        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

        print(Fore.CYAN + self.name + " (v" + _SERVER_VERSION + ") (client: v" + _CLIENT_VERSION + ")" + Fore.BLACK + Back.WHITE + "\nServer logs can be found in the \"logs/terminal_out.log\" file!" + Back.BLUE + "\nIf you have any questions, join our Discord: https://discord.gg/StJxMSc8kM" + Fore.RESET + Back.RESET)
        asyncio.run(self.__main(discord_bot, ssl_chain))

    def create_chatbot(self, username_index: str = 0, badges: list[Badge] = [], nickname_color: NicknameColor = NicknameColor.RED) -> ChatBot:
        """Creates a chatbot for the server.
        
        Parameters:
            username_index (int): Username index in the `Server.chatbot_usernames` list.
            badges (list[Badge]): List of chatbot badges.
            nickname_color (NicknameColor): Chatbot nickname color.

        Returns:
            ChatBot: Initialized chatbot.

        Raises:
            ValueError: Username index is out of range. Check if there are enough usernames in Server.chatbot_usernames (or check CHATBOT_USERNAMES in config.ini).
        """

        if username_index > len(self.chatbot_usernames)-1:
            raise ValueError("Username index is out of range. Check if there are enough usernames in Server.chatbot_usernames (or check CHATBOT_USERNAMES in config.ini).")

        return ChatBot(self, username_index, badges, nickname_color)

    async def send_kick_notification(self, websocket: websockets.ServerConnection, reason: str = None) -> None:
        """Sends a kick notification to a player. This method is a coroutine.

        Parameters:
            websocket (websockets.ServerConnection): Websocket object of the player to kick.
            reason (str): *Optional.* Reason for kicking the player. This will make a kick notification with this reason stated.
        """

        await websocket.send(json.dumps({"request": "kick", "reason": reason if reason else "(not set)"}))

    async def send_ban_notification(self, websocket: websockets.ServerConnection, reason: str = None) -> None:
        """Sends a ban notification to a player. This method is a coroutine.

        Parameters:
            websocket (websockets.ServerConnection): Websocket object of the player to ban.
            reason (str): *Optional.* Reason for banning the player. This will make a ban notification with this reason stated.
        """

        await websocket.send(json.dumps({"request": "ban", "reason": reason if reason else "(not set)"}))

    async def kick_player_by_websocket(self, websocket: websockets.ServerConnection, reason: str = None) -> bool:
        """Kicks a player by their websocket object. Also sends a kick notification, if a reason is given. This method is a coroutine.

        Parameters:
            websocket (websockets.ServerConnection): Websocket object of the player to kick.
            reason (str): *Optional.* Reason for kicking the player. This will make a kick notification with this reason stated.

        Returns:
            bool: Whether the player was kicked.
        """

        for _websocket, player in self.all_players.copy().items():
            if websocket == _websocket:
                await _call_registered_function(self.__registered_events, "on_player_kick", player, reason)
                if reason:
                    await self.send_kick_notification(websocket, reason[:255])
                await websocket.close(1000)
                return True
        
        return False
    
    async def kick_player_by_username(self, username: str, reason: str = None) -> bool:
        """Kicks a player by their username. Also sends a kick notification, if a reason is given. This method is a coroutine.

        Parameters:
            username (str): Username of the player to kick.
            reason (str): *Optional.* Reason for kicking the player. This will make a kick notification with this reason stated.

        Returns:
            bool: Whether the player was kicked.
        """

        for websocket, player in self.all_players.copy().items():
            if compare_usernames(username, player.username):
                await _call_registered_function(self.__registered_events, "on_player_kick", player, reason)
                if reason:
                    await self.send_kick_notification(websocket, reason[:255])
                await websocket.close(1000)
                return True
        
        return False

    def get_players_in_node(self, node: str, remove_sensitive: bool = True) -> list[Player]:
        """Returns a list of players in a node.
        
        Parameters:
            node (str): Node to get players from.
            remove_sensitive (bool): *Optional.* Whether the list should contain safe versions of player JSON objects.

        Returns:
            list[Player]: (stated upper)
        """

        players = []

        for player in self.all_players.copy().values():
            if player.node == node:
                if remove_sensitive:
                    players.append(player.safe())
                else:
                    players.append(player)
        
        return players
    
    def get_players_in_node_json(self, node: str, remove_sensitive: bool = True) -> list[dict]:
        """Returns a list of JSON objects of players in a node.
        
        Parameters:
            node (str): Node to get players from.
            remove_sensitive (bool): *Optional.* Whether the list should contain safe versions of player JSON objects.

        Returns:
            list[dict]: (stated upper)
        """

        players = []

        for player in self.all_players.copy().values():
            if player.node == node:
                if remove_sensitive:
                    players.append(player.safe().to_json())
                else:
                    players.append(player.to_json())
        
        return players

    def get_player_by_username(self, username: str, remove_sensitive: bool = True) -> Player:
        """Finds and returns a player object by username.

        Parameters:
            username (str): Player username.
            remove_sensitive (bool): *Optional.* Whether to return a safe version of the player object.

        Returns:
            Player: Found player (or False if not found).
        """

        for player in self.all_players.copy().values():
            if compare_usernames(username, player.username):
                if remove_sensitive:
                    return player.safe()
                else:
                    return player
            
        return False

    async def send_message(self, node: str, message: Message, log_message: bool = False) -> None:
        """Sends a message to chat. This method is a coroutine.

        Parameters:
            node (str): Node to broadcast the message to.
            message (Message): Message to send.
            log_message (bool): *Optional.* Whether the message should be logged to DB. If the message has more than 100 characters, it won't be logged.
        """

        escaped = message.content.replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        escaped_censored = message.censored_content.replace("<", "&lt;").replace(">", "&gt;")

        await self.broadcast_to_node(node, {"request": "chat", "message": escaped, "censored_message": escaped_censored, "badges": message.badges_values, "nickname_color": message.nickname_color.value}, username=message.username)
        
        if self.log_messages and log_message and len(message.content) <= 100:
            await execDB("INSERT INTO chatlogs(username, message, node, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)", (message.username, message.content, node))

    async def broadcast_to_node(self, node: str, message: dict, sender_websocket: websockets.ServerConnection = None, username: str = None, send_to_sender: bool = True) -> None:
        """Broadcasts a WebSocket message to a node as player. This method is a coroutine.

        **IMPORTANT:** `sender_websocket` and `username` are optional, but at least one of them **must** be given!

        Parameters:
            node (str): Node to broadcast the message to.
            message (dict): Message to broadcast.
            sender_websocket (websockets.ServerConnection): *Optional.* Sender websocket. If set, the player's username will be included in the JSON message.
            username (str): *Optional.* Username of the player that broadcasted the message. If set, the value will be included in the JSON message.
            send_to_sender (bool): *Optional.* Whether to send the message back to sender.

        Raises:
            ValueError: At least one of these parameters must be given: sender_websocket, username!
        """

        if sender_websocket == None and username == None:
            raise ValueError("At least one of these parameters must be given: sender_websocket, username!")

        if sender_websocket:
            username = self.all_players[sender_websocket].username if username == None else username
            
        message["username"] = username

        for websocket, player in self.all_players.items():
            if player.node == node and (sender_websocket == None or ((not send_to_sender and (websocket != sender_websocket and not compare_usernames(username, player.username))) or send_to_sender)):
                try:
                    await websocket.send(json.dumps(message))
                except:
                    pass

    async def broadcast(self, message: dict) -> None:
        """Broadcasts a WebSocket message to every node. This method is a coroutine.

        Parameters:
            message (dict): Message to broadcast.
        """

        try:
            for websocket in self.all_players.keys():
                try:
                    await websocket.send(json.dumps(message))
                except:
                    pass
        except:
            pass

    # Check heartbeats, logins and do other stuff
    async def __validate_players(self):
        while True:
            accounts = await execDB(f"SELECT username, password FROM {_PLAYERS_COLUMN}")

            if len(accounts) != 0:
                accounts = {row[0]: row[1] for row in accounts}

            accounts_keys = accounts.keys()
            now = datetime.datetime.now()

            for websocket, player in self.all_players.copy().items():
                try:
                    if not (player.username in accounts_keys and player.password == accounts[player.username]):
                        await self.kick_player_by_websocket(websocket, "Your account has been changed. Please log in again.")

                    else:
                        if now - player.last_heartbeat > datetime.timedelta(seconds=12):
                            if websocket in _missed_hearbeat:
                                _missed_hearbeat[websocket] += 1

                                if _missed_hearbeat[websocket] >= 4:
                                    await websocket.close(1001)

                            else:
                                _missed_hearbeat[websocket] = 1

                        else:
                            if websocket in _missed_hearbeat:
                                _missed_hearbeat.remove(websocket)

                            await self.broadcast_to_node(player.node, {"request": "update_statistics", "value": player.statistics.to_json()}, sender_websocket=websocket)

                except:
                    await self.kick_player_by_websocket(websocket, "Internal server error.")
            
            #__print_statistics()
            await asyncio.sleep(10)

    # Main function
    async def __main(self, discord_bot, ssl_chain):
        #if _DB_TYPE == "MySQL":
            #global _pool
            #_pool = await aiomysql.create_pool(
                #**{
                    #"host": os.getenv("DB_HOST"),
                    #"port": int(os.getenv("DB_PORT")),
                    #"user": os.getenv("DB_USER"),
                    #"password": os.getenv("DB_PASS"),
                    #"db": os.getenv("DB_NAME")
                #},
                #autocommit=True
            #)

        #elif _DB_TYPE == "SQLite":
        with open("db_config/sqlite3.sql", "r", encoding="utf-8") as file:
            sql_script = file.read()

        async with aiosqlite.connect("sqlite3.db") as db:
            await db.executescript(sql_script)
            await db.commit()

        asyncio.create_task(self.__validate_players())

        if ssl_chain != None:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(
                certfile=ssl_chain[0],
                keyfile=ssl_chain[1]
            )

        async with websockets.serve(self.__handle_client, "localhost" if _testing or self.localhost else "0.0.0.0", self.port, ssl=ssl_context if ssl_chain != None else None):
            await _call_registered_function(self.__registered_events, "on_server_ready")
            if discord_bot:
                await bot.start(os.getenv("DISCORD_BOT_TOKEN"))
            else:
                await asyncio.Future()

    async def __handle_client(self, websocket):
        try:
            async for req in websocket:
                json_req = json.loads(req)

                #if _testing:
                    #print(json_req)

                if "request" not in json_req:
                    await websocket.send(json.dumps({"status_code": 400, "message": ClientErrorMessage.MISSING_REQ_VALUE}))
                    await _call_registered_function(self.__registered_events, "on_client_error", websocket, ClientErrorMessage.MISSING_REQ_VALUE, False)

                elif websocket not in self.all_players:
                    # Join to a free node after logging in

                    if self.max_players != None and len(self.all_players) >= self.max_players:
                        await websocket.send(json.dumps({"status_code": 400, "message": ClientErrorMessage.FULL_SERVER}))
                        await _call_registered_function(self.__registered_events, "on_client_error", websocket, ClientErrorMessage.FULL_SERVER, True)
                        return
                    
                    if not json_req["request"] == "login":
                        await websocket.send(json.dumps({"reply": "login", "status_code": 400, "message": ClientErrorMessage.WRONG_USERNAME_OR_PASSWORD}))
                        await _call_registered_function(self.__registered_events, "on_client_error", websocket, ClientErrorMessage.WRONG_USERNAME_OR_PASSWORD, True)
                        return
                    
                    else:
                        values = await execDB(f"SELECT password, discord_id, username FROM {_PLAYERS_COLUMN} WHERE LOWER(username)=?", (json_req["username"].lower(), ))

                        if not (len(values) != 0 and _check_hash(json_req["password"], values[0][0].encode("utf-8"))):
                            await websocket.send(json.dumps({"reply": "login", "status_code": 400, "message": ClientErrorMessage.WRONG_USERNAME_OR_PASSWORD}))
                            await _call_registered_function(self.__registered_events, "on_client_error", websocket, ClientErrorMessage.WRONG_USERNAME_OR_PASSWORD, True)
                            return
                        
                        elif json_req["version"] != _CLIENT_VERSION:
                            await websocket.send(json.dumps({"reply": "login", "status_code": 400, "message": ClientErrorMessage.OUTDATED_CLIENT}))
                            await _call_registered_function(self.__registered_events, "on_client_error", websocket, ClientErrorMessage.OUTDATED_CLIENT, True)
                            return
                        
                        else:
                            validate(json_req["statistics"], _valid_statistics_schema)

                            json_req["username"] = values[0][2]
                            json_req["password"] = values[0][0]
                            
                            last_connection = self.get_player_by_username(json_req["username"], False)

                            if last_connection:
                                old_websocket = last_connection.websocket
                                last_connection._last_heartbeat = datetime.datetime.now()
                                last_connection._websocket = websocket
                                
                                self.all_players[websocket] = last_connection
                                del self.all_players[old_websocket]

                                players = self.get_players_in_node_json(last_connection.node)
                                try:
                                    await old_websocket.close(1000)
                                except:
                                    pass
                                await websocket.send(json.dumps({"reply": "login", "status_code": 200, "message": f"Successfully relogged in.", "heartbeat_ms": 8000, "players": players, "node": last_connection.node}))
                                await _call_registered_function(self.__registered_events, "on_player_reconnect", last_connection, old_websocket)

                            else:
                                nickname_color = await execDB(f"SELECT nickname_color FROM {_PLAYERS_COLUMN} WHERE LOWER(username)=?", (json_req["username"].lower(), ))
                                json_req["nickname_color"] = nickname_color[0][0]
                                allowed_to_connect = await _call_registered_function(self.__registered_events, "on_process_player_connect", json_req)

                                if allowed_to_connect == None or allowed_to_connect == True:
                                    node = self.__assign_to_node(websocket, json_req, values[0][1])
                                    players = self.get_players_in_node_json(node)

                                    await self.broadcast_to_node(node, {"request": "connect", "status": json_req["status"], "statistics": json_req["statistics"]}, sender_websocket=websocket, send_to_sender=False)
                                    await websocket.send(json.dumps({"reply": "login", "status_code": 200, "message": f"Successfully logged in.", "heartbeat_ms": 8000, "players": players, "node": node}))
                                    await _call_registered_function(self.__registered_events, "on_player_connect", self.all_players[websocket])

                                else:
                                    await self.send_kick_notification(websocket, allowed_to_connect if isinstance(allowed_to_connect, str) else None)
                                    return

                elif json_req["request"] == "login":
                    await websocket.send(json.dumps({"reply": "login", "status_code": 400, "message": ClientErrorMessage.ALREADY_LOGGED_IN}))
                    await _call_registered_function(self.__registered_events, "on_client_error", websocket, ClientErrorMessage.ALREADY_LOGGED_IN, True)
                
                elif json_req["request"] == "heartbeat":
                    player = self.all_players[websocket]
                    old_heatbeat = player.last_heartbeat
                    new_heartbeat = datetime.datetime.now()

                    player._last_heartbeat = new_heartbeat
                    await _call_registered_function(self.__registered_events, "on_player_heartbeat_update", player, old_heatbeat, new_heartbeat)

                elif json_req["request"] == "update_statistics":
                    try:
                        player = self.all_players[websocket]
                        old_stats = player.statistics
                        new_stats = PlayerStatistics(*json_req["value"].values())

                        validate(json_req["value"], _valid_statistics_schema)
                        player._statistics = new_stats
                        await _call_registered_function(self.__registered_events, "on_player_statistics_update", player, old_stats, new_stats)
                    
                    except:
                        pass

                elif json_req["request"] == "move":
                    try:
                        player = self.all_players[websocket]
                        position = PlayerPosition.str_to_object(json_req["position"])
                        allowed_to_move = await _call_registered_function(self.__registered_events, "on_process_player_move", player, position)
                        
                        if allowed_to_move == None or allowed_to_move:
                            await player.move(position, float(json_req["current_position"].split(" ")[0]) < position.x)
                            await _call_registered_function(self.__registered_events, "on_player_move", player, position)

                    except:
                        pass

                elif json_req["request"] == "chat":
                    if not (websocket in _chat_ratelimit and datetime.datetime.now() - _chat_ratelimit[websocket] < datetime.timedelta(seconds=2)):
                        player = self.all_players[websocket]
                        badges = []

                        if is_player_in_list(player, self.owners) or player.discord_id in self.owners:
                            badges.append(Badge.OWNER) # owner badge
                        if is_player_in_list(player, self.moderators) or player.discord_id in self.moderators:
                            badges.append(Badge.MODERATOR) # moderator badge
                        if is_player_in_list(player, self.verified) or player.discord_id in self.verified:
                            badges.append(Badge.VERIFIED) # verified badge
                        if is_player_in_list(player, self.supporters) or player.discord_id in self.supporters:
                            badges.append(Badge.SUPPORTER) # supporter badge

                        message = Message(
                                player.username,
                                json_req["message"].strip()[:100],
                                badges,
                                player.nickname_color
                            )
                        
                        allowed_to_send = await _call_registered_function(self.__registered_events, "on_process_player_chat", player, message)

                        if allowed_to_send == None or allowed_to_send:
                            await self.send_message(player.node, message, log_message=True)
                            await _call_registered_function(self.__registered_events, "on_player_chat", player, message)
                        
                        _chat_ratelimit[websocket] = datetime.datetime.now()

                elif json_req["request"] == "status":
                    value = json_req["value"]

                    if value == "online" or value == "idle":
                        player = self.all_players[websocket]
                        old_status = player.status
                        new_status = PlayerStatus(value)

                        allowed_to_change_status = await _call_registered_function(self.__registered_events, "on_process_player_status_update", player, old_status, new_status)
                        
                        if allowed_to_change_status == None or allowed_to_change_status:
                            await player.change_status(new_status)
                            await _call_registered_function(self.__registered_events, "on_player_status_update", player, old_status, new_status)
        
        except websockets.exceptions.InvalidMessage:
            pass

        except websockets.exceptions.ConnectionClosedError:
            pass

        except Exception:
            logging.log(51, traceback.format_exc())

        finally:
            try:
                username = self.all_players[websocket].username
                node = self.all_players[websocket].node

                if websocket.close_code != 1000:
                    await asyncio.sleep(20)

                player = self.get_player_by_username(username, False)

                if player and player.websocket == websocket:
                    await self.broadcast_to_node(node, {"request": "disconnect"}, sender_websocket=websocket, send_to_sender=False)
                    await _call_registered_function(self.__registered_events, "on_player_disconnect", player)

                    logging.log(51, username + " has been detached from " + player.node)
                    self.nodes[player.node].remove(username)
                    self.all_players.pop(websocket)
                    _chat_ratelimit.pop(websocket, None)

                    if websocket in _missed_hearbeat:
                        del _missed_hearbeat[websocket]

            except:
                pass

    def __assign_to_node(self, websocket: websockets.ServerConnection, json_obj: dict, discord_id: int):
        found_node = False
        assigned_to = None

        for node in self.nodes.copy().keys():
            ply_count = len(self.nodes[node])

            if self.node_limit == None or ply_count < self.node_limit:
                found_node = True
                assigned_to = node
                
        # If not found, deploy new node
        if not found_node:
            assigned_to = f"node{len(self.nodes)}"
            self.nodes[assigned_to] = []

        player_obj = Player(self,
                            websocket,
                            discord_id,
                            assigned_to,
                            json_obj["username"],
                            json_obj["password"],
                            datetime.datetime.now(),
                            PlayerPosition(0, 0),
                            False,
                            PlayerStatus(json_obj["status"]),
                            NicknameColor(json_obj["nickname_color"]),
                            PlayerStatistics(
                                *json_obj["statistics"].values()
                            ))
        self.nodes[assigned_to].append(player_obj.username)
        self.all_players[websocket] = player_obj

        logging.log(51, player_obj.username + " has been assigned to " + assigned_to)
        return assigned_to

    # Decorator
    def event(self, func):
        """Registeres custom server event function. This method is a decorator."""
        self.__registered_events.append(func)

        return func
