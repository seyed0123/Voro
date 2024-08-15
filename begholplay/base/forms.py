from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from base.models import Player


class SignupForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=commit)

        Player.objects.create(user=user, color='#4169E1')
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class PlayerProfileForm(forms.ModelForm):

    class Meta:
        model = Player
        fields = ['profile_photo', 'color']

    widgets = {
        'color': forms.Select(attrs={'class': 'form-select'}),
        'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
    }
