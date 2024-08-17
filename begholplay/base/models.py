from django.db import models
from django.contrib.auth.models import User


class Player(models.Model):
    color_choices = [
        ('#B22222', 'FIREBRICK'),
        ('#DC143C', 'RED'),
        ('#FF6347', 'TOMATO'),
        ('#FF4500', 'ORANGE RED'),
        ('#Ffa500', 'ORANGE'),
        ('#DAA520', 'GOLDEN-ROD'),
        ('#FFD700', 'GOLD'),
        ('#FFFF00', 'YELLOW'),
        ('#ADFF2F', 'GREEN YELLOW'),
        ('#228B22', 'GREEN'),
        ('#32CD32', 'LIME GREEN'),
        ('#2E8B57', 'SEA GREEN'),
        ('#00FA9A', 'MEDIUM SPRING GREEN'),
        ('#20B2AA', 'LIGHT SEA GREEN'),
        ('#008080', 'TEAL'),
        ('#48D1CC', 'MEDIUM TURQUOISE'),
        ('#00FFFF', 'CYAN'),
        ('#00CED1', 'DARK TURQUOISE'),
        ('#5F9EA0', 'CADET BLUE'),
        ('#87CEFA', 'LIGHT SKY BLUE'),
        ('#6495ED', 'CORNFLOWER BLUE'),
        ('#4169E1', 'BLUE'),
        ('#191970', 'MIDNIGHT BLUE'),
        ('#6A5ACD', 'SLATE BLUE'),
        ('#8A2BE2', 'BLUE VIOLET'),
        ('#4B0082', 'INDIGO'),
        ('#9400D3', 'DARK VIOLET'),
        ('#9932CC', 'DARK ORCHID'),
        ('#EE82EE', 'VIOLET'),
        ('#DDA0DD', 'PLUM'),
        ('#C71585', 'MEDIUM VIOLET RED'),
        ('#FF69B4', 'HOT PINK'),
        ('#FF1493', 'DEEP PINK'),
        ('#FFB6C1', 'LIGHT PINK'),
        ('#F4A460', 'BROWN'),
        ('#D2691E', 'CHOCOLATE'),
        ('#8B4513', 'SADDLE BROWN'),
        ('#2F4F4F', 'DARK SLATE GRAY'),
        ('#708090', 'GRAY'),
    ]

    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True, default='profile_photos/default.jpg')
    favorite_color = models.CharField(
        max_length=20,
        choices=color_choices,
        default='#4169E1',
    )
    match_color = models.CharField(max_length=20, default='#4169E1')
    in_lobby = models.BooleanField(default=False)


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
    game = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='rankings')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='rankings')
    rank = models.IntegerField()
    score = models.IntegerField()

    def __str__(self):
        return f"{self.player.user.username} - Rank: {self.rank} in Game: {self.game.lobby.name}"
