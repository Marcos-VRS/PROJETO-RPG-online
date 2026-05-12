from django.urls import path

from .views import CsrfView, HealthView, MeView

urlpatterns = [
    path("health/", HealthView.as_view(), name="api-health"),
    path("csrf/", CsrfView.as_view(), name="api-csrf"),
    path("me/", MeView.as_view(), name="api-me"),
]
