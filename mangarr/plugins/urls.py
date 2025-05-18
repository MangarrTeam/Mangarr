from django.urls import path
from . import views

urlpatterns = [
    path("manager/", views.plugin_manager, name="plugin_manager"),
    path("download/<str:domain>/", views.download_plugin_view, name="plugin_download"),
    path("delete/<str:domain>/", views.delete_plugin_view, name="plugin_delete"),
]
