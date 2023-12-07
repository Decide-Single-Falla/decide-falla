from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.StoreView.as_view(), name='store'),
    path('discord/<int:voting_id>/<int:voter_id>/<int:selectedOption>/', views.DiscordStoreView.as_view(), name='DiscordStore'),
]