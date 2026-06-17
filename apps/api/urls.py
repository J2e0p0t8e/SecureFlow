"""Routes API — Personne 2 Backend."""

from django.urls import path

from apps.api import views

urlpatterns = [
    # Endpoint principal
    path("analyze/", views.analyze, name="analyze"),
    
    # Détails d'une session
    path("session/<int:session_id>/", views.session_detail, name="session_detail"),
    
    # Messages Band Room (pour affichage live)
    path("room/<str:room_id>/messages/", views.room_messages, name="room_messages"),
    
    # Health check
    path("health/", views.health_check, name="health_check"),
]
