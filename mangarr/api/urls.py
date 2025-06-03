from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name="index"),
    path('search', views.search, name='api_search'),



    path('manager/users/token/regenerate', views.regenerate_token_view, name='regenerate_token'),
    path('manager/users/<int:user_id>/staff/', views.toggle_staff_user, name='toggle_user_staff'),
    path('manager/users/<int:user_id>/permissions/', views.get_user_permissions, name='get_user_permissions'),
    path('manager/users/<int:user_id>/permissions/update/', views.update_user_permissions, name='update_user_permissions'),
    path('manager/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('manager/tokens/register/delete/<int:token_id>/', views.delete_token, name='delete_token'),
    path('manager/downloads/toggle/', views.toggle_pause_downloads, name='download_toggle'),


    path("manga/search/start", views.search_manga_start, name="api_search_manga_start"),
    path("manga/search/status/<uuid:task_id>", views.search_manga_status, name="api_search_manga_status"),
    path("manga/request", views.request_manga, name="api_request_manga"),
    path("manga/request/approve", views.approve_manga_request, name="approve_manga_request"),
    path("manga/request/deny", views.deny_manga_request, name="deny_manga_request"),
    path("manga/monitor", views.monitor_manga, name="api_monitor_manga"),
    path("manga/edit/<int:manga_id>", views.edit_manga, name="api_edit_manga"),
    path("manga/edit/<int:manga_id>/request", views.request_edit_manga, name="api_request_edit_manga"),
    path("manga/delete/<int:manga_id>", views.delete_manga, name="api_delete_manga"),

    path("volume/edit/<int:volume_id>", views.edit_volume, name="api_edit_volume"),
    path("volume/edit/<int:volume_id>/request", views.request_edit_volume, name="api_request_edit_volume"),
    path("chapter/edit/<int:chapter_id>", views.edit_chapter, name="api_edit_chapter"),
    path("chapter/edit/<int:chapter_id>/request", views.request_edit_chapter, name="api_request_edit_chapter"),
    path("chapter/redownload/<int:chapter_id>/request", views.request_redownload_chapter, name="api_request_redownload_chapter"),
]