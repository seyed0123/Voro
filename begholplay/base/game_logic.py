from asgiref.sync import sync_to_async

import json


def xy2ind(x, y):
    return x * Game.border_size + y


def create_game(lobby, user):
    from base.models import Match
    board = {}
    for ind in range(Game.border_size ** 2):
        x, y = (ind // Game.border_size), (ind % Game.border_size) + 1
        board[f"{x},{y}"] = {
            'number': 0,
            'color': 'None',
            'Player': 'None'
        }
    for player in list(lobby.players.all()):
        board[player.user.id] = {'status': "not_start", 'number': 0, 'boom': False}
    Match.objects.create(lobby=lobby, board=json.dumps(board), current_turn=user.id, last_active_player=0)


class Game:
    border_size = 8

    def __init__(self, player, lobby_id, user_ids):

        self.player = player
        self.lobby_id = lobby_id
        self.user_ids = user_ids
        self.match = None
        self.players = []
        self.board = {}
        self.user_id = 0

    async def initialize(self):
        from base.models import Match, Lobby
        # Fetch the match and players asynchronously
        self.match = await sync_to_async(Match.objects.get)(lobby_id=self.lobby_id)

        lobby = await sync_to_async(Lobby.objects.get)(id=self.lobby_id)

        self.players = await sync_to_async(list)(lobby.players.all())
        self.user_id = await sync_to_async(lambda: self.player.user.id)()
        self.user_id = str(self.user_id)
        await self.init_board()

    async def init_board(self):
        self.board = json.loads(self.match.board)

    async def click(self, ind, first: bool):
        ind -= 1
        x, y = (ind // Game.border_size), (ind % Game.border_size) + 1
        ind += 1
        # Ensure board is up-to-date
        board_value = self.board.get(f"{x},{y}")
        fake = False
        # Start state handling
        if self.board[self.user_id]['status'] == 'not_start' and board_value['Player'] == 'None':
            self.board[self.user_id]['number'] += 1
            board_value['number'] += 1
            board_value['color'] = await sync_to_async(lambda: self.player.match_color)()
            board_value['Player'] = self.user_id
            self.board[self.user_id]['status'] = 'start'
            self.match.board = json.dumps(self.board)
            await sync_to_async(self.match.save)()
            return {
                       'cell': ind,
                       'number': board_value['number'],
                       'color': await sync_to_async(lambda: self.player.match_color)()
                   }, []

        # Check if this is the first click
        if first:
            if board_value['Player'] == 'None' or board_value['Player'] != self.user_id:
                return None

        # Handle updating the board
        if board_value['number'] <= 3:
            if board_value['Player'] == 'None':
                self.board[self.user_id]['number'] += 1
            elif board_value['Player'] != self.user_id:
                self.board[board_value['Player']]['number'] -= 1
                self.board[self.user_id]['number'] += 1
            ret = []
            if board_value['number'] == 3:
                ret.append((ind, False))
            board_value['number'] += 1
            board_value['color'] = await sync_to_async(lambda: self.player.match_color)()
            board_value['Player'] = self.user_id
            self.match.board = json.dumps(self.board)
            await sync_to_async(self.match.save)()
            return {
                       'cell': ind,
                       'number': board_value['number'],
                       'color': await sync_to_async(lambda: self.player.match_color)()
                   }, ret

        # Handle board state reset
        elif board_value['number'] <= 4:
            self.board[board_value['Player']]['number'] -= 1
            self.board[self.user_id]['boom'] = True

            board_value['number'] = 0
            board_value['color'] = 'None'
            board_value['Player'] = 'None'

            self.match.board = json.dumps(self.board)
            await sync_to_async(self.match.save)()
            ret_list = []

            if x >= 1:
                ret_list.append((ind - 8, False))
            if x < self.border_size - 1:
                ret_list.append((ind + 8, False))
            if y >= 2:
                ret_list.append((ind - 1, False))
            if y < self.border_size:
                ret_list.append((ind + 1, False))

            return {
                       'cell': ind,
                       'number': board_value['number'],
                       'color': 'None'
                   }, ret_list

    async def validate_game(self, players):
        # Initialize player status
        players_status = {'None': {'number': 0}, 'loss': set()}
        player_ids = {}
        # Prepare the players' IDs in an async-safe manner
        for player in players:
            player_id = player
            player_ids[player] = player_id
            players_status[str(player_id)] = {
                'number': self.board[str(player_id)]['number'],
            }

        # Iterate over the board and count pieces for each player
        # for ind in range(Game.border_size ** 2):
        #     x, y = (ind // Game.border_size), (ind % Game.border_size) + 1
        #     player_at_position = self.board[f"{x},{y}"]['Player']
        #     if player_at_position in players_status:
        #         players_status[player_at_position]['number'] += 1

        # Determine the status of each player
        num_loss = 0
        ok_player = None
        for player in players:
            player_id = str(player_ids[player])
            if players_status[player_id]['number'] == 0 and self.board[player_id]['status'] == 'start' and \
                    self.board[player_id]['boom'] == False:
                # players_status[player_id]['status'] = 'loss'
                players_status['loss'].add(player_id)
                num_loss += 1
            else:
                ok_player = player_id
                # players_status[player_id]['status'] = 'ok'

        # Determine overall game status
        if num_loss == len(self.players) - 1:
            players_status['status'] = 'finish'
        else:
            players_status['status'] = 'continue'

        players_status['ok_player'] = ok_player
        return players_status
