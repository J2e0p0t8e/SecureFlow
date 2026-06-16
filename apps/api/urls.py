from django.urls import path
from . import views

urlpatterns = [
    path("analyze/", views.analyze, name="analyze"),
    path("pdf/<str:session_id>/", views.download_pdf, name="download_pdf"),
    path("room/<str:room_id>/messages/", views.room_messages, name="room_messages"),
]