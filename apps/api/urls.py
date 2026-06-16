from django.urls import path
from . import views

urlpatterns = [
    path("analyze/", views.analyze, name="analyze"),
    path("pdf/<str:session_id>/", views.download_pdf, name="download_pdf"),
]