import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from base.game_logic import *


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        from base.models import Lobby, Player
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

        if not hasattr(self.channel_layer, 'removed_list'):
            self.channel_layer.removed_list = set()
        await self.accept()

        await self.send_game_state(lobby)

    async def send_game_state(self, lobby):
        from base.models import Match
        match = await database_sync_to_async(Match.objects.get)(lobby=lobby)

        board = json.loads(match.board)

        if not hasattr(self.channel_layer, 'current_turn_ind'):
            self.channel_layer.current_turn_ind = 0
            await self.next_player()

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
            if len(self.channel_layer.group_channels) == 0:
                self.channel_layer.removed_list.clear()

    async def next_player(self):
        from base.models import Match
        players = list(self.channel_layer.group_channels.difference(self.channel_layer.removed_list))
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
        from base.models import Player
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
        asyncio.create_task(self._run_move_loop(game_class, data["cell"], user.id))

    async def _run_move_loop(self, game_class, start_cell, user_id):
        await game_class.initialize()
        saf = [(start_cell, True)]
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
            await asyncio.sleep(0)
            if res[0]['number'] == 4:
                await asyncio.sleep(0.1)
            if not item[1]:
                val = await game_class.validate_game(list(self.channel_layer.group_channels))
                for player in list(val['loss']):
                    self.channel_layer.group_channels.discard(int(player))
                    self.channel_layer.removed_list.add(int(player))
                if val['status'] == 'finish' or len(self.channel_layer.group_channels) == 1:
                    await self.channel_layer.group_send(
                        self.lobby_group_name,
                        {
                            'type': 'game_message',
                            'message': 'endgame',
                            'turn': val['ok_player']
                        }
                    )
                    await self.delete_match()
                    return

        if flag:
            game_class.board[str(user_id)]['boom'] = False
            game_class.match.board = json.dumps(game_class.board)
            await sync_to_async(game_class.match.save)()
            await self.next_player()
        else:
            await self.send(text_data=json.dumps({
                'message': 'error',
                'body': 'choose valid cell'
            }))

    async def delete_match(self):
        from base.models import Match, Lobby
        match = await sync_to_async(Match.objects.get)(lobby_id=self.lobby_id)
        await sync_to_async(match.delete)()
        lobby = await sync_to_async(Lobby.objects.get)(id=self.lobby_id)
        lobby.is_match_started = False
        await sync_to_async(lobby.save)()
        self.channel_layer.removed_list.clear()

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
