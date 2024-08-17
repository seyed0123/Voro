import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from base.models import Lobby, Player


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

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the lobby group
        await self.channel_layer.group_discard(
            self.lobby_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle incoming WebSocket messages
        data = json.loads(text_data)
        user = self.scope['user']
        player = await database_sync_to_async(Player.objects.get)(user=user)

        # Broadcast the message to the group, including the username
        await self.channel_layer.group_send(
            self.lobby_group_name,
            {
                'type': 'game_message',
                'message': f'{user.username} pressed button {data["cell"]}',
                'cell': data["cell"],
                'color': player.match_color
            }
        )

    async def game_message(self, event):
        # Send message to WebSocket, including the cell ID and color
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'cell': event['cell'],
            'color': event['color'],
        }))
