from django.urls import path
from gurps import views
from django.conf import settings
from django.conf.urls.static import static

app_name = "gurps"

urlpatterns = [
    # Login/Logout
    path("login/", views.login_view.login, name="login"),
    path("logout/", views.login_view.logout, name="logout"),
    # Index
    path("", views.menu_view.index, name="index"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
