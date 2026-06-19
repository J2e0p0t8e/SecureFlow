"""Configuration URL principale SecureFlow AI."""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.api.urls")),
    path("app/", TemplateView.as_view(template_name="index.html"), name="app"),
    path("", TemplateView.as_view(template_name="landing.html"), name="home"),
]