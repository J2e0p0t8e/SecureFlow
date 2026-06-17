"""Routes API SecureFlow AI."""

from django.urls import path

from apps.api import views

urlpatterns = [
    path("analyze/", views.analyze, name="analyze"),
    path("session/<int:session_id>/", views.session_detail, name="session_detail"),
    path("pdf/<str:room_id>/", views.download_pdf, name="download_pdf"),
    path("room/<str:room_id>/messages/", views.room_messages, name="room_messages"),
    path("health/", views.health_check, name="health_check"),
]
