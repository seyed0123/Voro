from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.urls import reverse
from .forms import SignupForm, LoginForm, PlayerProfileForm, JoinLobbyForm, CreateLobbyForm
from base.game_logic import create_game
from .models import Player, Lobby
import random


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            next_url = request.GET.get('next', 'index')
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def index(request):
    return render(request, 'index.html')


@login_required
def profile(request):
    player = Player.objects.get(user=request.user)

    if request.method == 'POST':
        form = PlayerProfileForm(request.POST, request.FILES, instance=player)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = PlayerProfileForm(instance=player)

    return render(request, 'profile.html', {'form': form, 'player': player})


@login_required
def play(request):
    if request.method == 'POST':
        if 'join' in request.POST:
            form = JoinLobbyForm(request.POST)
            if form.is_valid():
                lobby = form.cleaned_data['lobby']
                player = Player.objects.get(user=request.user)
                if player in lobby.players.all():
                    messages.info(request, 'You are already in this lobby.')
                    return redirect('lobby_detail', pk=lobby.pk)

                if player.in_lobby:
                    messages.warning(request, 'You are already in another lobby')
                    return redirect('play')

                taken_colors = lobby.players.values_list('match_color', flat=True)
                if player.favorite_color not in taken_colors:
                    player.match_color = player.favorite_color
                else:
                    available_colors = Player.color_choices.copy()
                    random.shuffle(available_colors)
                    for color in available_colors:
                        color_code = color[0]
                        if color_code not in taken_colors:
                            player.match_color = color_code
                            break
                player.in_lobby = True
                player.save()

                lobby.players.add(player)
                lobby.save()
                messages.success(request, 'Successfully joined the lobby.')
                return redirect('lobby_detail', pk=lobby.pk)
            else:
                messages.error(request, 'There was an error with your submission.')

        if 'create' in request.POST:
            form = CreateLobbyForm(request.POST)
            form.user = request.user
            if form.is_valid():
                lobby = form.save()
                player = Player.objects.get(user=request.user)
                if player.in_lobby:
                    messages.warning(request, 'You are already in another lobby')
                    return redirect('play')

                player.match_color = player.favorite_color
                player.in_lobby = True
                player.save()
                return redirect('lobby_detail', pk=lobby.pk)
            else:
                if form.errors['name']:
                    for error in form.errors['name']:
                        messages.error(request, error)

    create_form = JoinLobbyForm()
    join_form = CreateLobbyForm()
    return render(request, 'home_play.html', {'create_form': create_form, 'join_form': join_form})


@login_required
def lobby_detail(request, pk):
    lobby = get_object_or_404(Lobby, pk=pk)
    players = list(lobby.players.all())
    owner_player = Player.objects.get(user=lobby.owner)
    is_owner = request.user == lobby.owner

    if not Player.objects.get(user=request.user) in players:
        raise Http404("This page does not exist.")

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.POST['type'] == 'update':
            players = list(lobby.players.all().values('user__username', 'profile_photo','match_color'))
            return JsonResponse({'players': list(players), 'base_url': request.build_absolute_uri('/') + 'media/',
                                 'owner_username': owner_player.user.username, 'match_status': lobby.is_match_started,
                                 'match_url': reverse('game', args=[lobby.pk])})

        elif request.POST['type'] == 'leave':
            player = Player.objects.get(user=request.user)
            if is_owner:
                lobby.delete()
                for player in players:
                    player.in_lobby = False
                    player.save()
                messages.error(request, 'Lobby deleted by owner')
                return JsonResponse({'redirect_url': reverse('index')})
            if player in players:
                player.in_lobby = False
                lobby.players.remove(player)
                lobby.save()
                player.save()
                messages.warning(request, 'Leaved the lobby')
                return JsonResponse({'redirect_url': reverse('index')})

    return render(request, 'lobby_detail.html',
                  {'lobby': lobby, 'owner_player': owner_player, 'players': players, 'is_owner': is_owner})


@login_required
def start_game(request, pk):
    lobby = get_object_or_404(Lobby, pk=pk)

    if request.user != lobby.owner:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    lobby.is_match_started = True
    lobby.save()
    create_game(lobby, request.user)

    return JsonResponse({'redirect_url': reverse('game', args=[lobby.pk])})


@login_required
def game(request, pk):
    lobby = get_object_or_404(Lobby, pk=pk)
    player = Player.objects.get(user=request.user)
    own_color = Player.objects.get(user_id=lobby.owner_id).match_color
    players = list(lobby.players.all())
    if player not in players:
        raise Http404("This page does not exist.")

    return render(request, 'game.html', {'lobby': lobby, 'players': players, 'own_color': own_color, 'base_url': request.build_absolute_uri('/') + 'media/' , 'lobby_url':reverse('lobby_detail', args=[lobby.pk]) , 'user_id':request.user.id})
