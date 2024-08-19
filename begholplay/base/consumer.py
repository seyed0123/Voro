import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from base.game_logic import *


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lobby_id = self.scope['url_route']['kwargs']['pk']
        self.lobby_group_name = f'lobby_{self.lobby_id}'

        # Check if user is authenticated
        if isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return

        # Fetch the lobby from the database
        try:
            lobby = await database_sync_to_async(Lobby.objects.get)(pk=self.lobby_id)
        except Lobby.DoesNotExist:
            await self.close()
            return

        try:
            player = await database_sync_to_async(Player.objects.get)(user=self.scope['user'])
        except Player.DoesNotExist:
            await self.close()
            return

        # Check if the user is a member of the lobby
        if not await database_sync_to_async(lobby.players.filter(id=player.id).exists)():
            await self.close()
            return

        # If the user is in the lobby, connect to the WebSocket
        await self.channel_layer.group_add(
            self.lobby_group_name,
            self.channel_name
        )

        if not hasattr(self.channel_layer, 'group_channels'):
            self.channel_layer.group_channels = set()
        self.channel_layer.group_channels.add(self.scope['user'].id)



        await self.accept()

        await self.send_game_state(lobby)

    async def send_game_state(self, lobby):

        match = await database_sync_to_async(Match.objects.get)(lobby=lobby)

        board = json.loads(match.board)

        if not hasattr(self.channel_layer, 'current_turn_ind'):
            self.channel_layer.current_turn_ind = match.current_turn

        for ind in range(Game.border_size ** 2):
            x, y = (ind // Game.border_size), (ind % Game.border_size) + 1
            data = {
                'cell': ind + 1,
                'number': board.get(f"{x},{y}", {}).get('number', 0),
                'color': board.get(f"{x},{y}", {}).get('color', 'None'),
            }

            await self.send(text_data=json.dumps({
                'message': 'change',
                **data
            }))

        await self.send(text_data=json.dumps({
            'message': 'current_turn',
            'turn': match.current_turn,
        }))

    async def disconnect(self, close_code):
        # Leave the lobby group
        await self.channel_layer.group_discard(
            self.lobby_group_name,
            self.channel_name
        )

        if hasattr(self.channel_layer, 'group_channels'):
            self.channel_layer.group_channels.discard(self.scope['user'].id)

    async def next_player(self):

        players = list(self.channel_layer.group_channels)
        players.sort()
        if self.channel_layer.current_turn_ind >= len(players) - 1:
            self.channel_layer.current_turn_ind = 0
        else:
            self.channel_layer.current_turn_ind += 1

        match = await sync_to_async(Match.objects.get)(lobby_id=self.lobby_id)
        match.current_turn = players[self.channel_layer.current_turn_ind]
        await sync_to_async(match.save)()

        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'game_message',
                'message': 'current_turn',
                'turn': players[self.channel_layer.current_turn_ind]
            }
        )

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        data = json.loads(text_data)
        user = self.scope['user']
        player = await database_sync_to_async(Player.objects.get)(user=user)
        players = list(self.channel_layer.group_channels)
        players.sort()

        if self.channel_layer.current_turn_ind >= len(players):
            await self.next_player()
            return

        if user.id != players[self.channel_layer.current_turn_ind]:
            await self.send(text_data=json.dumps({
                'message': 'error',
                'body': 'it\'s not your turn'
            }))

            return

        game_class = Game(player, self.lobby_id, self.channel_layer.group_channels)
        await game_class.initialize()
        saf = [(data["cell"], True)]
        flag = False
        while len(saf) > 0:
            item = saf.pop()
            res = await game_class.click(*item)
            if res is None:
                continue
            await self.channel_layer.group_send(
                self.lobby_group_name,
                {
                    'type': 'game_message',
                    'message': 'change',
                    **res[0]
                }
            )
            saf += res[1]
            flag = True

            # await asyncio.sleep(0.1)
            val = await game_class.validate_game()
            if val['status'] == 'finish':
                pass

        if flag:
            await self.next_player()
        else:
            await self.send(text_data=json.dumps({
                'message': 'error',
                'body': 'choose valid cell'
            }))

    async def game_message(self, event):
        # Send message to WebSocket, including the cell ID and color
        if 'turn' not in event:
            event['turn'] = 'null'
        if 'cell' not in event:
            event['cell'] = 'null'
        if 'number' not in event:
            event['number'] = 'null'
        if 'color' not in event:
            event['color'] = 'null'
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'cell': event['cell'],
            'color': event['color'],
            'number': event['number'],
            'turn': event['turn'],
        }))
