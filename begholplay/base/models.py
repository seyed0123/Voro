from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    favorite_color = models.CharField(
        max_length=20,
        choices=[
            ('#DC143C', 'RED'),
            ('#Ffa500', 'ORANGE'),
            ('#4169E1', 'BLUE'),
            ('#228B22', 'GREEN'),
            ('#DAA520', 'GOLDEN-ROD'),
            ('#708090', 'GRAY'),
            ('#EE82EE', 'VIOLET'),
            ('#F4A460', 'BROWN'),
            ('#00FFFF', 'CYAN'),
        ],
        default='#4169E1',
    )


class Match(models.Model):
    lobby = models.ForeignKey(to='Lobby', on_delete=models.CASCADE, null=False)
    is_finished = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    current_turn = models.IntegerField()
    last_active_player = models.IntegerField()
    board = models.JSONField(null=False)


class Lobby(models.Model):
    name = models.CharField(max_length=100,unique=True, null=False)
    password = models.CharField(max_length=100, blank=True, null=True)
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='game_owner', null=False)
    players = models.ManyToManyField(to=Player, related_name='game_players')
    creation_date = models.DateTimeField(auto_now_add=True)
    is_match_started = models.BooleanField(default=False)


class Player_ranking(models.Model):
    game = models.ForeignKey(Lobby, on_delete=models.CASCADE, related_name='rankings')
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rankings')
    rank = models.IntegerField()
    score = models.IntegerField()

    def __str__(self):
        return f"{self.player.username} - Rank: {self.rank} in Game: {self.game.name}"
