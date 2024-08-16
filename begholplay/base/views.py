from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.urls import reverse

from .forms import SignupForm, LoginForm, PlayerProfileForm, JoinLobbyForm, CreateLobbyForm
from .models import Player, Lobby


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
            return redirect('profile')  # Redirect to a profile page or another page after saving
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

                lobby.players.add(player)
                messages.success(request, 'Successfully joined the lobby.')
                return redirect('lobby_detail', pk=lobby.pk)
            else:
                messages.error(request, 'There was an error with your submission.')

        if 'create' in request.POST:
            form = CreateLobbyForm(request.POST)
            form.user = request.user
            if form.is_valid():
                lobby = form.save()
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

    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        players = list(lobby.players.all().values('user__username', 'profile_photo'))
        return JsonResponse({'players': list(players), 'base_url': request.build_absolute_uri('/') + 'media/',
                             'owner_username': owner_player.user.username})

    return render(request, 'lobby_detail.html',
                  {'lobby': lobby, 'owner_player': owner_player, 'players': players, 'is_owner': is_owner})


@login_required
def start_game(request, pk):
    lobby = get_object_or_404(Lobby, pk=pk)

    # Ensure that only the owner can start the game
    if request.user != lobby.owner:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    # Logic to start the game
    lobby.is_match_started = True
    lobby.save()

    # Redirect to the game page
    return JsonResponse({'redirect_url': reverse('game_detail', args=[lobby.pk])})
