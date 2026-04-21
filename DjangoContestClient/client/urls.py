from django.urls import path

from client.views import index_view, ops_results_view, ops_view


urlpatterns = [
    path("", index_view, name="index"),
    path("ops/", ops_view, name="ops"),
    path("ops/results/", ops_results_view, name="ops_results"),
]
