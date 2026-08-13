# Event functions
Through the `@Server.event` decorator, you can register `async def` functions on the server that will be called in a specific event. Here is an example of registering an event function:

```py
# server.py
from onlineclicker.onlineclicker import *

server = Server()

@server.event
async def on_ws_server_ready():
    print("This will be printed when the WebSocket server is ready to operate.")

@server.event
async def on_player_connect(player: Player):
    print(player.username + " just connected to the server!")

server.initialize()
```

## ```Server.on_ws_server_ready()```
## ```Server.on_server_ready()```
Called when the WebSocket server is ready to operate.

## ```Server.on_api_server_ready()```
Called when the API server is ready to operate.

## ```Server.on_client_auth(websocket, json_obj)```
Called when a client is authorized.

Arguments:
- **websocket (websockets.ServerConnection):** Client websocket.
- **json_obj (dict):** Client JSON object that was provided to the server.

Returns:
> bool | str: *Optional.* Whether the player should connect to the server. String is reason for disconnecting the player. If this is provided, the player will be disconnected.

## ```Server.on_client_error(websocket, json_req, error, is_kicked)```
Called when a client connection error occurs.

Arguments:
- **websocket (websockets.ServerConnection):** Client websocket.
- **json_obj (dict):** Client JSON object that was provided to the server.
- **error (ClientErrorMessage):** Connection error.
- **is_kicked (bool):** Whether the client was kicked from the server.

## ```Server.on_process_player_connect(json_obj)```
Called before a player connects to the server.

Arguments:
- **json_obj (dict):** Player JSON object that was provided to the server.

Returns:
> bool | str: *Optional.* Whether the player should connect to the server. String is reason for disconnecting the player. If this is provided, the player will be disconnected.

## ```Server.on_player_connect(player)```
## ```Server.on_player_disconnect(player)```
Called when a player connects or disconnects from the server.

Arguments:
- **player (Player):** The connected/disconnected player.

## ```Server.on_player_reconnect(player, old_websocket)```
Called when a player reconnects to the server.

Arguments:
- **player (Player):** The reconnected player.
- **old_websocket (websockets.ServerConnection):** WebSocket object of the old player connection.

## ```Server.on_player_heartbeat_update(player, old_heartbeat, new_heartbeat)```
Called when a player updates their heartbeat.

Arguments:
- **player (Player):** The player who updated their heartbeat.
- **old_heartbeat (datetime.datetime):** Datetime object of the old heartbeat.
- **new_heartbeat (datetime.datetime):** Datetime object of the new heartbeat.

## ```Server.on_player_statistics_update(player, old_statistics, new_statistics)```
Called when a player updates their statistics.

Arguments:
- **player (Player):** The player who updated their statistics.
- **old_statistics (PlayerStatistics):** Object of old player statistics.
- **new_statistics (PlayerStatistics):** Object of new player statistics.

## ```Server.on_process_player_move(player, position)```
## ```Server.on_player_move(player, position)```
The first function is called before and the second one after processing a player movement.

Arguments:
- **player (Player):** The player who requested to move.
- **position (PlayerPosition):** Object of the requested position.

Returns (1. function):
> bool: *Optional.* Whether the player should move.

## ```Server.on_process_player_chat(player, message)```
## ```Server.on_player_chat(player, message, was_sent)```
The first function is called before and the second one after processing a player chat.

Arguments:
- **player (Player):** The player who requested to send a message.
- **message (Message):** Object of the requested message.
- **was_sent (bool):** Whether the player message appeared in chat.

Returns (1. function):
> bool: *Optional.* Whether the message should be sent.

## ```Server.on_process_player_status_update(player, old_status, new_status)```
## ```Server.on_player_status_update(player, old_status, new_status)```
The first function is called before and the second one after processing a player status change.

Arguments:
- **player (Player):** The player who requested to change their status.
- **old_status (PlayerStatus):** Object of old player status.
- **new_status (PlayerStatus):** Object of new player status.

Returns (1. function):
> bool: *Optional.* Whether the status should be changed.

## ```Server.on_player_kick(player, reason)```
Called when a player is kicked from the server.

Arguments:
- **player (Player):** The player who was kicked from the server.
- **reason (str):** Reason for kicking the player.

# API Documentation