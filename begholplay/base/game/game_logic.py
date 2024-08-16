from ..models import *

def create_new_game(name):
    game = Lobby.objects.create(name="New Checkers Game",players="")