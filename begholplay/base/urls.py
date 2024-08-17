from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.index, name='index'),
    path('profile/', views.profile, name='profile'),
    path('play/', views.play, name='play'),
    path('lobby/<int:pk>/', views.lobby_detail, name='lobby_detail'),
    path('lobby/<int:pk>/start-game/', views.start_game, name='start_game'),
    path('game/<int:pk>/', views.game, name='game')
]
