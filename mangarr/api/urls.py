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

    path("library/browse", views.library_explore_path, name="api_library_browse"),
    path("library/add", views.library_add, name="api_library_add"),
    path("library/edit/<uuid:id>", views.library_edit, name="api_library_edit"),
    path("library/delete/<uuid:id>", views.library_delete, name="api_library_delete"),

    path("connector/add", views.connector_add, name="api_connector_add"),
    path("connector/edit/<uuid:id>", views.connector_edit, name="api_connector_edit"),
    path("connector/delete/<uuid:id>", views.connector_delete, name="api_connector_delete"),

    path("manga/search/start", views.search_manga_start, name="api_search_manga_start"),
    path("manga/search/status/<uuid:task_id>", views.search_manga_status, name="api_search_manga_status"),
    path("manga/request", views.request_manga, name="api_request_manga"),
    path("manga/request/approve", views.approve_manga_request, name="approve_manga_request"),
    path("manga/request/deny", views.deny_manga_request, name="deny_manga_request"),
    path("manga/monitor", views.monitor_manga, name="api_monitor_manga"),
    path("manga/edit/<uuid:manga_id>", views.edit_manga, name="api_edit_manga"),
    path("manga/edit/<uuid:manga_id>/request", views.request_edit_manga, name="api_request_edit_manga"),
    path("manga/delete/<uuid:manga_id>", views.delete_manga, name="api_delete_manga"),
    path("manga/mass/<uuid:manga_id>", views.mass_edit_manga, name="api_mass_edit_manga"),

    path("volume/edit/<uuid:volume_id>", views.edit_volume, name="api_edit_volume"),
    path("volume/edit/<uuid:volume_id>/request", views.request_edit_volume, name="api_request_edit_volume"),
    path("chapter/edit/<uuid:chapter_id>", views.edit_chapter, name="api_edit_chapter"),
    path("chapter/edit/<uuid:chapter_id>/request", views.request_edit_chapter, name="api_request_edit_chapter"),
    path("chapter/redownload/<uuid:chapter_id>/request", views.request_redownload_chapter, name="api_request_redownload_chapter"),
    path("chapter/transfer/<uuid:chapter_id>/<uuid:manga_id>", views.transfer_chapter, name="api_transfer_chapter"),
]