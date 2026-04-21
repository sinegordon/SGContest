from django.urls import path

from client.views import index_view


urlpatterns = [
    path("", index_view, name="index"),
]
