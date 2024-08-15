from django.db import models
from django.contrib.auth.models import User

class Player(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    profile_photo = models.ImageField(upload_to='profile_photos/',null=True, blank=True)
    color = models.CharField(
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
        ]
    )


class Match(models.Model):
    lobby = models.ForeignKey(to='Lobby',  on_delete=models.CASCADE, null=True)
    players = models.ManyToManyField(to=Player, default=None)
    is_finished = models.BooleanField(default=False)
    creation_date = models.DateTimeField(auto_now_add=True)


class Lobby(models.Model):
    owner = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name='+', null=True)
    users = models.ManyToManyField(to=User, related_name='+')
    creation_date = models.DateTimeField(auto_now_add=True)
    is_match_started = models.BooleanField(default=False)
