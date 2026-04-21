from django.urls import path

from rag import views

app_name = "rag"

urlpatterns = [
    path("", views.query_page, name="query_page"),
    path("api/query", views.query_api, name="query_api"),
]
