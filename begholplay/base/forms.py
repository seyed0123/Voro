import os
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User

from base.models import Player, Lobby


class SignupForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)

        Player.objects.create(user=user)
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class PlayerProfileForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['profile_photo', 'favorite_color']
        widgets = {
            'favorite_color': forms.Select(attrs={'class': 'form-select'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super(PlayerProfileForm, self).save(commit=False)

        if 'profile_photo' in self.changed_data:

            profile_photo = self.cleaned_data.get('profile_photo')
            if profile_photo:
                ext = os.path.splitext(profile_photo.name)[1]
                new_filename = f'{instance.id}{ext}'
                instance.profile_photo.save(new_filename, profile_photo, save=False)

        if commit:
            instance.save()

        return instance


class CreateLobbyForm(forms.ModelForm):
    user = None

    class Meta:
        model = Lobby
        fields = ['name', 'password']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        lobby = super(CreateLobbyForm, self).save(commit=False)
        lobby.owner = self.user
        lobby.password = make_password(lobby.password)
        if commit:
            lobby.save()
        player = Player.objects.get(user=self.user)
        lobby.players.add(player)
        if commit:
            lobby.save()
        return lobby


class JoinLobbyForm(forms.Form):
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(max_length=100, required=False,
                               widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_password(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        password = cleaned_data.get("password")
        try:
            lobby = Lobby.objects.get(name=name)
        except Lobby.DoesNotExist:
            raise forms.ValidationError("Lobby does not exist.")

        if not check_password(password, lobby.password):
            raise forms.ValidationError("Invalid password.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        password = cleaned_data.get('password')

        try:
            lobby = Lobby.objects.get(name=name)
        except Lobby.DoesNotExist:
            raise forms.ValidationError("Lobby does not exist.")

        if not check_password(password, lobby.password):
            raise forms.ValidationError("Incorrect password.")

        self.cleaned_data['lobby'] = lobby
        return cleaned_data
